"""Build a RAG-friendly PDF book from the Food + AI web archive.

Usage (from the archive root):
    source ~/lib/python/uv-osm/bin/activate && python src/build_book.py [OUTPUT_DIR]

Reads the archive read-only and writes to OUTPUT_DIR (default: pdf/ in the
archive): the full book food-ai-sourcebook.pdf, plus a split edition with
food-ai-intro.pdf and one food-ai-<source>.pdf per source.
Requires PyMuPDF (fitz), Pillow, ffmpeg and a headless Chromium.
"""

import base64
import html
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz
from PIL import Image

SRC = Path(__file__).resolve().parent.parent
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else SRC / "pdf"
PDF_OUT = OUT / "food-ai-sourcebook.pdf"
TITLE = "Food and AI: A Sourcebook on AI-Generated Menu Imagery"
KEYWORDS = "AI food images, menus, uncanny valley, disgust, restaurants, generative AI, Sweden, SVT"

FRAME_TIMES = [1, 7, 13, 20, 27, 34, 41, 46]


def esc(s):
    return html.escape(s, quote=False)


def read(rel):
    return (SRC / rel).read_text(encoding="utf-8")


def meta(name):
    return json.loads(read(f"{name}/metadata.json"))


def img_data_uri(img, max_side=1400, quality=82):
    if not isinstance(img, Image.Image):
        img = Image.open(img)
    img = img.convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def paragraphs(text):
    """Convert plain extracted article text into HTML paragraphs/headings."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("# "):
            out.append(f"<h3>{esc(block[2:])}</h3>")
        elif block.startswith("## "):
            out.append(f"<h3>{esc(block[3:])}</h3>")
        else:
            out.append(f"<p>{esc(block).replace(chr(10), '<br>')}</p>")
    return "\n".join(out)


def source_card(label, m, extra=None):
    rows = [("Source", label), ("Title", m.get("title", "")), ("URL", m.get("url", "")),
            ("Kind", m.get("kind", "")), ("Archive status", m.get("download_status", ""))]
    if m.get("description"):
        rows.append(("Publisher description", m["description"]))
    rows += extra or []
    body = "".join(f"<tr><th>{esc(k)}</th><td>{esc(str(v))}</td></tr>" for k, v in rows if v)
    return f'<table class="card">{body}</table>'


def figure(fig_id, src, source_label, caption, description, file_rel, max_side=1400, cls=""):
    return f"""
<figure class="{cls}" id="{fig_id}">
  <img src="{img_data_uri(src, max_side)}" alt="{html.escape(caption)}">
  <figcaption>
    <p class="figlabel">{fig_id.replace('-', ' ').title()} · {esc(source_label)} · archive file <code>{esc(file_rel)}</code></p>
    <p><b>Original caption/alt text:</b> {esc(caption)}</p>
    <p><b>Visual description (written for this book):</b> {description}</p>
  </figcaption>
</figure>"""


# ---------------------------------------------------------------- image notes

IMAGE_NOTES = {
    "guardian/images/image-01.jpg": (
        "A printed poster taped inside a window of Bella Cafe, San Francisco, headed by a handwritten "
        "strip reading “BREAKFAST 8AM–11AM”. It shows twelve tiles in a Wild West / “spaghetti western” "
        "style, each with a Bella Cafe logo, a generated food photo and a movie-title dish name: "
        "Unforgiven, Tombstone, A Fistful of Dollars, The Magnificent Seven, Rio Bravo, and The Good, the "
        "Bad and the Ugly in the top row; French Toast, a waffle dish, Bella Lox Deluxe Bagel, Prosciutto "
        "Avocado Toast, Veggie Frittata and Prosciutto Frittata in the bottom row. The dishes (eggs, "
        "bacon, pancakes, waffles, frittatas) share a uniform glossy, warm-toned, over-saturated look "
        "typical of generated imagery. The owner told the Guardian the signs were designed with ChatGPT."),
    "guardian/images/image-02.jpg": (
        "Close-up of a menu board from a Jamaican barbecue pop-up in Denver, with large text “COMBO … ANY "
        "PROTEIN WITH … SIDES OF YOUR CHOICE” and a “PROTEINS” header below. A takeaway tray holds dark, "
        "glossy strips of meat whose surface is covered by a regular stitched, quilted or cross-hatched "
        "pattern with small black dots, so the meat resembles leather belts or reptile skin with tiny "
        "beetles on it. Beside it are unnaturally uniform yellow macaroni pieces and rice with dark beans. "
        "This is the image nurse Jill Sennett shared on X."),
    "guardian/images/image-03.jpg": (
        "Screenshot from the DoorDash app showing a menu item “Chicken Katsu” (96% approval, 26 ratings; "
        "“Deep fried breaded chicken breast”) with an “AI-enhanced” label on the photo. The image shows "
        "sliced breaded chicken, a triangular mound of rice, a cup of dark sauce and shredded cabbage "
        "salad on a dark plate. Below is an optional “Roll Addition” (California Roll, +$6.75). Unlike the "
        "other examples, the image looks largely plausible, illustrating how hard it is to tell AI "
        "enhancement from ordinary over-editing."),
    "cnn/images/image-01.jpg": (
        "Photo of an illuminated “HOT ENTREES” board in a New York deli/bodega above a shelf of snacks "
        "(Goldfish crackers, Chips Deluxe cookies). Five numbered dishes are shown with generated images: "
        "1 Chicken Marsala, 2 Chicken Francaise, 3 Chicken Cutlet Parmigiana, 4 Pepper Steak, 5 Shrimp "
        "Scampi. The shrimp scampi image is the notorious one: the shrimp are rendered as identical "
        "doughnut-like rings with segmented, striped bodies lying on noodles, looking like small "
        "creatures rather than food. On the right edge, partially visible, are hero sandwiches and a "
        "“3 FT” party sub offer (“Includes 1 lb. Coleslaw, Potato Salad”) and the word “FRESH”. "
        "Photo credited to Intercept reporter Sam Biddle."),
    "cnn/images/image-02.jpg": (
        "Small thumbnail of a related CNN story, not about food: four painted-style AI-generated portraits "
        "of US founding fathers (Francis Lewis, Carter Braxton, Edward Rutledge, Abraham Clark) from the "
        "Freedom 250 website, labelled “AI-GENERATED IMAGE”. All four men look strikingly alike, "
        "in the same pose with hand to chin."),
    "cnn/images/image-03.jpg": (
        "The article’s lead (Open Graph) image: advertising for “Freesh Juice Bar” showing three branded "
        "plastic cups of smoothie (orange/peach, green-to-red layered, purple berry) topped with fruit and "
        "mint, surrounded by cut mango, peaches, passion fruit, berries, lime and ice on a dark wet "
        "background. The look is hyper-glossy and over-saturated, with fruit cut surfaces and splashes "
        "that are slightly too perfect, a typical AI-advertising aesthetic."),
    "reddit/images/image-01.jpg": (
        "Phone photo of a digital menu screen above a food counter, titled “STORMARKNADEN (Äta här "
        "priser)” with a “Street Food ♡” sign and a “Maxi Stormarknaden” logo containing a Poké Ball. "
        "Commenters identify the location as ICA Maxi Stormarknad, Solbacken, Skellefteå, Sweden. The "
        "background is a busy fantasy landscape (waterfalls, lanterns, rocks, autumn colours) with "
        "AI-generated Pokémon-like characters: a yellow Pikachu/Pichu hybrid, a fiery monkey resembling "
        "Infernape/Chimchar, and a blue penguin resembling Piplup. Six menu tiles each show a hot dog "
        "meal with a drink: MENY 1 15 kr (boiled sausage with bread and a drink), MENY 2 25 kr (grilled "
        "sausage with bread and a drink), MENY 3 35 kr (grilled sausage in baguette and a drink), MENY 4 "
        "39 kr (any sausage in a “chicagobörd” [sic, for chicagobröd] with shrimp/cucumber salad + "
        "drink), MENY 5 40 kr (any sausage with mashed potatoes, shrimp/cucumber salad + drink), MENY 6 "
        "50 kr (two sausages with mash, shrimp/cucumber salad + drink). A sign reads “Vänligen säg till "
        "ifall ni vill äta här eller ta med” (Please tell us if you want to eat here or take away). "
        "The poster says the screen was actually an animated video."),
    "instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.jpg": (
        "Video thumbnail (vertical 1080×1920): Jenny Frennberg, a young woman with long blonde hair, black "
        "leather jacket and brown buttoned top with a clip-on microphone, speaks to camera on a sunny "
        "Stockholm street lined with restaurants, outdoor seating, parked cars and bicycles."),
}


# ---------------------------------------------------------------- sections


SPLIT_FILES = [
    ("food-ai-intro.pdf", "Introduction, overview, source catalogue and glossary"),
    ("food-ai-guardian.pdf", "The Guardian article (book chapter 2)"),
    ("food-ai-cnn.pdf", "CNN article (book chapter 3)"),
    ("food-ai-instagram.pdf", "Instagram reel by Jenny Frennberg (book chapter 4)"),
    ("food-ai-reddit.pdf", "Reddit r/sweden discussion (book chapter 5)"),
    ("food-ai-nytimes.pdf", "The New York Times interactive, retrieval note (book chapter 6.1)"),
    ("food-ai-tiktok.pdf", "TikTok discovery page, retrieval note (book chapter 6.2)"),
]


def split_file_list():
    items = "".join(f"<li><code>{f}</code>: {esc(d)}</li>" for f, d in SPLIT_FILES)
    return f"""<p>This content is also available as separate files, one per source.
Chapter numbers mentioned in the text refer to the full book, <code>{PDF_OUT.name}</code>:</p>
<ul class="toc">{items}</ul>"""


def split_header(source_title, chapter):
    """Short header that opens each per-source file of the split edition."""
    return f"""
<section class="split-head">
  <p class="kicker">{esc(TITLE)} · split edition · {esc(chapter)}</p>
  <h1 class="split-title">{esc(source_title)}</h1>
  <p class="small">This file covers a single source in the Food + AI web archive, which collects
  material for an SVT Nyheter Helsingborg interview about AI-generated food images on restaurant
  menus. Text marked “written for this book” (visual descriptions, translations, summaries) was
  added during compilation and is not part of the original source.</p>
  {split_file_list()}
</section>"""


def front_matter(split=False):
    contents = split_file_list() if split else """<ol class="toc">
  <li><a href="#ch1">Overview: the question, the sources, and the main explanations</a></li>
  <li><a href="#ch2">The Guardian: “Uncanny and unappetizing”</a></li>
  <li><a href="#ch3">CNN: “Why restaurants are facing backlash for fake food pictures”</a></li>
  <li><a href="#ch4">Instagram: Jenny Frennberg’s reel “AI-bilder på menyn? NEJ TACK!”</a></li>
  <li><a href="#ch5">Reddit r/sweden: “Vad tycker ni om att allt fler restauranger har AI-genererade menyer?”</a></li>
  <li><a href="#ch6">Sources that could not be retrieved: The New York Times and TikTok</a></li>
  <li><a href="#appA">Appendix A: Catalogue of sources and files</a></li>
  <li><a href="#appB">Appendix B: Glossary of key concepts, people and organisations</a></li>
</ol>"""
    return f"""
<section class="title-page">
  <p class="kicker">Research sourcebook · SVT Nyheter Helsingborg interview preparation · October 2026</p>
  <h1 class="book-title">{esc(TITLE)}</h1>
  <p class="subtitle">Complete text, transcripts, and described images from six linked sources:
  The Guardian, CNN, Instagram (Jenny Frennberg), Reddit r/sweden, The New York Times, and TikTok.</p>
  <p class="small">Compiled from the Food / AI Sourcebook web archive (<code>web/food-ai</code>).
  Built 2026-10-26.</p>
</section>

<section class="about">
<h2 id="about">About this book</h2>
<p>This book gathers every piece of content in the Food + AI web archive into one document that can be
searched and used for retrieval-augmented (RAG) question answering. The archive was built from the six
topical links in <i>svt.pdf</i>, a three-page Swedish email thread setting up an SVT Nyheter
Helsingborg interview about AI-generated food images in restaurant menus and advertising.</p>
<p><b>Conventions for retrieval.</b> Each chapter covers one source and opens with a source card
giving its title, URL, kind and archive status. Article text is reproduced in full, as extracted.
Social media text is reproduced verbatim in its original language (mostly Swedish) and labelled
by author and timestamp. Images and video frames are embedded, and each comes with a written
<i>visual description</i> so that its content can be searched as text. Text marked
“written for this book” (visual descriptions, translations, summaries) is editorial
material added during compilation and is not part of the original sources.</p>
<p><b>Gaps.</b> The New York Times interactive and the TikTok discovery feed could not be retrieved.
Chapter 6 records these gaps; nothing has been invented to fill them.</p>

<h2 id="contents">Contents</h2>
{contents}
</section>
"""


def ch_overview():
    return """
<section>
<h2 id="ch1">Chapter 1. Overview: the question, the sources, and the main explanations</h2>

<h3>1.1 The interview request (svt.pdf)</h3>
<p>The source PDF is a three-page Swedish email thread preparing an SVT Nyheter Helsingborg interview
about AI-generated food images in restaurant menus and advertising. It describes generative imagery
moving off the internet and into everyday physical communication: menus, food trucks, signs and
restaurant advertising. It raises five questions:</p>
<ul>
<li>Why are businesses adopting AI-generated food imagery?</li>
<li>Why are reactions unusually strong when the subject is food?</li>
<li>Why do the images have a recognisable visual character?</li>
<li>Is the “uncanny valley” a useful explanation?</li>
<li>Will audiences get used to it as synthetic imagery becomes more common?</li>
</ul>

<h3>1.2 The six linked sources</h3>
<table class="grid">
<colgroup><col style="width:22%"><col style="width:14%"><col><col style="width:16%"></colgroup>
<tr><th>Source</th><th>Type</th><th>What it contributes</th><th>Status</th></tr>
<tr><td>The Guardian (6 Sep 2026)</td><td>News article</td><td>US reporting on restaurants adopting AI menu images to cut costs; diner backlash (Denver, San Francisco); DoorDash “AI-enhanced” tool; Charles Spence’s research.</td><td>Complete, chapter 2</td></tr>
<tr><td>CNN (2 Sep 2026)</td><td>News article</td><td>Global examples (Los Angeles, New York, Tokyo, Kuala Lumpur, Berlin); uncanny valley; Alexander Diel’s psychology research on disgust and food neophobia; restaurant economics (National Restaurant Association figures); advice from the International Association of Culinary Professionals.</td><td>Complete, chapter 3</td></tr>
<tr><td>Instagram reel by Jenny Frennberg</td><td>Social video (48 s)</td><td>A Stockholm food creator’s appeal to Swedish restaurateurs to skip AI menu images.</td><td>Complete, chapter 4</td></tr>
<tr><td>Reddit r/sweden thread (Oct 2026)</td><td>Social discussion</td><td>Swedish audience reactions (original post and 198 comments) to an AI-generated, Pokémon-themed hot-dog menu at ICA Maxi in Skellefteå.</td><td>Complete, chapter 5</td></tr>
<tr><td>The New York Times (6 Oct 2026)</td><td>News interactive</td><td>“Why A.I. Food Slop Looks So Gross”</td><td>Blocked, chapter 6</td></tr>
<tr><td>TikTok discovery page</td><td>Social discovery feed</td><td>Search phrase “ai food looks disgusting”</td><td>Feed not available, chapter 6</td></tr>
</table>

<h3>1.3 Recurring explanations across the sources (synthesis)</h3>
<p>The retrievable sources point to five overlapping explanations:</p>
<ol>
<li><b>Economics.</b> Generated images are cheap and quick to make. Restaurant margins are thin:
42% of US operators did not turn a profit in 2025, and 26% use AI, mostly for marketing (National
Restaurant Association). Owners quoted in the sources used ChatGPT instead of paying a designer or
photographer.</li>
<li><b>Visual defects.</b> Texture, lighting and structure come out wrong: leathery or rubbery
meat, bread that looks like reptile skin or a loofah, pasta like yarn or Play-Doh, ring-shaped
“shrimp”, repeated forms, excess gloss and saturation, and layouts that are too geometric.</li>
<li><b>Uncanny valley.</b> Masahiro Mori’s 1970 concept describes the eerie feeling caused by
near-human figures with slight flaws. Diel’s research found that slightly imperfect AI food images
are rated more uncanny and less pleasant than either clearly unrealistic or highly realistic ones.</li>
<li><b>Food-specific disgust.</b> Food can make us ill, so people are sensitive to anything that
looks “slightly off”. Two candidate mechanisms are evolved disgust, which guards against
contamination, and food neophobia, a wariness of unfamiliar food. Viewers want to eat AI food less
even when they judge it equally healthy.</li>
<li><b>Trust and truth in advertising.</b> A photograph can be styled, but it still implies that the
dish existed. A generated image may show food that never did. Diners call this false advertising,
read it as a sign of cut corners (“if they skimp on the signage they skimp on the food”), worry
about hallucinated allergen labels, and in Sweden point to Japan’s strict rules on food imagery as
a model. Charles Spence found that people preferred AI food images until they were told the images
were AI-made.</li>
</ol>
<p>“Uncanny valley” works as shorthand for imagery that is almost real but perceptually wrong.
Food-specific disgust and expectations about truthful advertising add mechanisms that go beyond the
term’s original context of humans and robots. On habituation, the evidence is mixed. In 2023 more
than 60% of people in a Slerp survey could not tell AI food images from photos, but the 2025–2026
reporting describes growing sensitivity and backlash. Restaurants have also begun advertising
“no AI” as a selling point (Chugwater Soda Fountain, Wyoming).</p>
</section>
"""


def ch_guardian():
    m = meta("guardian")
    figs = "".join(
        figure(f"figure-2-{i+1}", SRC / "guardian" / im["file"], "The Guardian", im["caption_or_alt"],
               IMAGE_NOTES[f"guardian/{im['file']}"], f"guardian/{im['file']}")
        for i, im in enumerate(m["images"]))
    text = read("guardian/content.txt")
    text = text.replace("D uring", "During")
    return f"""
<section>
<h2 id="ch2">Chapter 2. The Guardian: “Uncanny and unappetizing: appetites spoil as AI images take over food menus”</h2>
{source_card("The Guardian (technology section), 6 September 2026", m)}
<h3>2.1 Full article text</h3>
<div class="article" data-source="The Guardian">
{paragraphs(text)}
</div>
<h3>2.2 Article images</h3>
{figs}
</section>
"""


def ch_cnn():
    m = meta("cnn")
    figs = "".join(
        figure(f"figure-3-{i+1}", SRC / "cnn" / im["file"], "CNN", im["caption_or_alt"],
               IMAGE_NOTES[f"cnn/{im['file']}"], f"cnn/{im['file']}",
               cls="tall" if i == 0 else ("thumb" if i == 1 else ""))
        for i, im in enumerate(m["images"]))
    return f"""
<section>
<h2 id="ch3">Chapter 3. CNN: “Why restaurants are facing backlash for fake food pictures”</h2>
{source_card("CNN, 2 September 2026", m)}
<h3>3.1 Full article text</h3>
<div class="article" data-source="CNN">
{paragraphs(read("cnn/content.txt"))}
</div>
<h3>3.2 Article images</h3>
{figs}
</section>
"""


def parse_vtt(path):
    cues = []
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        if "-->" in lines[i]:
            start, end = [t.strip()[3:11] for t in lines[i].split("-->")]
            i += 1
            txt = []
            while i < len(lines) and lines[i].strip():
                txt.append(lines[i].strip())
                i += 1
            cues.append((start, end, " ".join(txt)))
        i += 1
    return cues


def ch_instagram(frames_uri):
    m = meta("instagram")
    from datetime import datetime, timezone
    posted = datetime.fromtimestamp(m["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    en = parse_vtt(SRC / "instagram/subtitles-en.vtt")
    de = parse_vtt(SRC / "instagram/subtitles-de.vtt")
    rows = "".join(
        f"<tr><td class='tc'>{a}–{b}</td><td>{esc(e)}</td><td>{esc(d[2]) if d else ''}</td></tr>"
        for (a, b, e), d in zip(en, de + [None] * (len(en) - len(de))))
    thumb = "instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.jpg"
    return f"""
<section>
<h2 id="ch4">Chapter 4. Instagram: Jenny Frennberg’s reel “AI-bilder på menyn? NEJ TACK!”</h2>
{source_card("Instagram reel", m, [("Uploader", m["uploader"]), ("Posted", posted),
    ("Duration", "48.15 seconds (1080×1920 vertical video with audio)"),
    ("Language", "Swedish speech, with Swedish burned-in captions")])}

<h3>4.1 Reel caption (original Swedish)</h3>
<blockquote lang="sv">{esc(m["description"]).replace(chr(10), "<br>")}</blockquote>
<h3>4.2 Reel caption: English translation (written for this book)</h3>
<blockquote>AI images on the menu? NO THANKS!!! 🤖<br><br>
A bit of a different video from me, but I still think it’s important to raise this issue! I think
it’s a shame that more and more restaurants are choosing to use AI to generate the images that are
supposed to represent the dishes on the menu. It looks bad and it just makes me sad.<br><br>
‼️ This is not an attack on individual restaurants or a call to boycott this place or that, I don’t
believe in that. You know I stand for the joy of food and inspiration. So this is more my opinion and
some encouragement to dare to keep things genuine and authentic! Skip the AI and it’ll be better 🥰
What do you think?<br><br>PÖSS! (“kisses”) ❤️</blockquote>

<h3>4.3 Spoken transcript, English (from the archive)</h3>
<div class="transcript">{paragraphs(read("instagram/transcript-en.txt"))}</div>
<h3>4.4 Spoken transcript, German (from the archive)</h3>
<div class="transcript" lang="de">{paragraphs(read("instagram/transcript-de.txt"))}</div>

<h3>4.5 Timed subtitles (English and German)</h3>
<table class="grid subs"><tr><th>Time</th><th>English</th><th>German</th></tr>{rows}</table>

<h3>4.6 What the video shows (visual description written for this book)</h3>
<p>Jenny Frennberg (“Stockholm Food Gems”) walks and talks on a sunny Stockholm street lined with
restaurants, outdoor seating, bicycles and parked vans. She wears a black leather jacket over a
brown buttoned top and a clip-on microphone. The video carries a title overlay, <i>“AI-bilder måste
upphöra!!!”</i> (“AI images must stop!!!”), and burned-in Swedish captions. Around 0:05–0:09 it cuts
to a close-up example: a restaurant poster headed <b>“MALATANG – Nu på buffén!”</b> (“Malatang – now
at the buffet!”) with a generated image of a bowl of red spicy broth containing meat, noodles,
potato and greens. Its text reads “Välj dina råvaror · Vi tillagar dem i kryddig buljong · Serveras
varmt &amp; starkt” (“Choose your ingredients · We cook them in spicy broth · Served hot &amp;
spicy”) and is signed “Mandarin …”.</p>
<p>Swedish on-screen captions seen in sampled frames (with English):</p>
<table class="grid">
<tr><th>Approx. time</th><th>Swedish on-screen text</th><th>English</th></tr>
<tr><td>0:01</td><td lang="sv">AI-bilder måste upphöra!!! / Okej vi måste snacka</td><td>AI images must stop!!! / Okay, we need to talk</td></tr>
<tr><td>0:07</td><td lang="sv">Och på dessa menyer så finns det inte längre äkta bilder på mat utan allt …</td><td>And on these menus there are no longer real pictures of food, instead everything …</td></tr>
<tr><td>0:13</td><td lang="sv">Det här måste upphöra</td><td>This has to stop</td></tr>
<tr><td>0:20</td><td lang="sv">Men problemet är alltså det ser inte bra ut</td><td>But the problem is, it doesn’t look good</td></tr>
<tr><td>0:27</td><td lang="sv">Så jag säger bara det här till hela Sverige till alla fina krögare där ute</td><td>So I’m just saying this to all of Sweden, to all the wonderful restaurateurs out there</td></tr>
<tr><td>0:34</td><td lang="sv">Skippa det bara i så fall för att det blir så mycket bättre och äkta och …</td><td>Just skip it, because it becomes so much better and genuine and …</td></tr>
<tr><td>0:41</td><td lang="sv">Har ni märkt fler AI-genererade bilder?</td><td>Have you noticed more AI-generated images?</td></tr>
<tr><td>0:46</td><td lang="sv">För att det här måste få ett slut</td><td>Because this has to come to an end</td></tr>
</table>
<figure class="frames" id="figure-4-1">
  <img src="{frames_uri}" alt="Eight frames sampled from the Instagram reel">
  <figcaption><p class="figlabel">Figure 4 1 · Instagram · frames sampled at 1, 7, 13, 20, 27, 34, 41 and 46 seconds from
  <code>instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4</code></p>
  <p><b>Visual description (written for this book):</b> Seven frames show the creator speaking on
  the street with the Swedish captions listed above. The second frame shows the AI-generated
  “MALATANG – Nu på buffén!” poster used as an example.</p></figcaption>
</figure>
{figure("figure-4-2", SRC / thumb, "Instagram", "Thumbnail for Jenny Frennberg’s reel about AI-generated menu images.",
        IMAGE_NOTES[thumb], thumb, max_side=700, cls="thumbsmall")}
</section>
"""


def parse_reddit():
    text = read("reddit/content.txt")
    entries = []
    for block in re.split(r"(?m)^## ", text)[1:]:
        lines = block.split("\n")
        head = lines[0].strip()
        author = updated = ""
        body = []
        for ln in lines[1:]:
            if ln.startswith("Author:"):
                author = ln[7:].strip()
            elif ln.startswith("Updated:"):
                updated = ln[8:].strip()
            else:
                body.append(ln)
        entries.append((head, author, updated, "\n".join(body).strip()))
    return entries


def ch_reddit():
    m = meta("reddit")
    entries = parse_reddit()
    post = entries[0]
    comments = entries[1:]
    post_body = post[3].replace("submitted by /u/Sensitive_Cream3920 [link] [comments]", "").strip()
    ctxt = []
    for n, (_, author, updated, body) in enumerate(comments, 1):
        ts = updated.replace("T", " ").replace("+00:00", " UTC")
        ctxt.append(
            f'<div class="comment"><p class="chead">r/sweden comment {n} of {len(comments)} · '
            f'{esc(author)} · {esc(ts)}</p><p lang="sv">{esc(body).replace(chr(10), "<br>")}</p></div>')
    img = "reddit/images/image-01.jpg"
    return f"""
<section>
<h2 id="ch5">Chapter 5. Reddit r/sweden: “Vad tycker ni om att allt fler restauranger har AI-genererade menyer?”</h2>
{source_card("Reddit, r/sweden discussion thread", m, [("Entries archived", f"{len(entries)} (1 original post + {len(comments)} comments)"),
    ("Language", "Swedish (one comment in English)"),
    ("Note", "Retrieved via the thread’s Atom feed; the feed does not preserve reply nesting, so comments appear in feed order.")])}

<h3>5.1 Original post</h3>
<p class="chead">Original post by {esc(post[1])} · {esc(post[2].replace("T", " ").replace("+00:00", " UTC"))}</p>
<blockquote lang="sv"><b>Vad tycker ni om att allt fler restauranger har AI-genererade menyer?</b><br>{esc(post_body)}</blockquote>
<p><b>English translation (written for this book):</b> <i>What do you think about more and more
restaurants having AI-generated menus?</i> “Can’t people choose food without Pikachu looking
on encouragingly? I understand if it’s for kids, but at restaurants with a mainly adult clientele
surely you can sit down and make a menu yourself.”</p>
{figure("figure-5-1", SRC / img, "Reddit r/sweden", m["images"][0]["caption_or_alt"], IMAGE_NOTES[img], img, cls="tall")}

<h3>5.2 Summary of the discussion (written for this book)</h3>
<p>The thread centres on an AI-generated animated menu screen at the street-food counter of ICA
Maxi Stormarknad (Solbacken, Skellefteå), shown in figure 5-1. Most of the 198 comments are
negative. The main themes are:</p>
<ul>
<li><b>Clutter and readability.</b> Many say the menu is messy, overstimulating and hard to read. It
is compared to an online casino, a slot machine, a bowling-alley strike animation and a casino game.
One autistic commenter says they would simply turn around and leave. Several argue a menu only
needs to list dishes and prices; one jokes they prefer the menu “in JSON format”.</li>
<li><b>Language errors.</b> Commenters mock the split compound “Äta här priser” and the typo
“chicagobörd” (meant to be “chicagobröd”).</li>
<li><b>Copyright and Pokémon.</b> A long sub-thread argues over whether the character is Pikachu,
Pichu or a hybrid, and identifies Infernape/Chimchar and Piplup. Many doubt that ICA licensed
Nintendo/Pokémon characters. Some suggest reporting it to Nintendo, noting that Nintendo sued a
Costa Rican shop over the name “Super Mario” in 2024. Commenters say the screen was not the
children’s menu.</li>
<li><b>False advertising and regulation.</b> Commenters say generated images never match the food
and call for a law, like Japan’s, requiring food to look like its picture. Japanese rules are
described as very strict, down to the scale of snack packaging and whether juice cartons may show
cut fruit. Others reply that menu photos and stock images were never truthful either, and that food
styling uses glue, toothpicks and oil-based paint.</li>
<li><b>Trust and quality signals.</b> “If they skimp on the signage they probably skimp on the food.”
AI menus are read as unprofessional and as a sign of hidden shortcuts. One English-language comment
and one Swedish comment warn of AI-made menus marking dishes gluten-free, nut-free or vegan when
they are not. One commenter tells of poor food (underseasoned fries, five small pieces of gyros) at
a place with an AI menu.</li>
<li><b>Cultural norms.</b> Some say restaurants proud of their food show no pictures at all, in Sweden
as in Greece, and that real, unglamorous photos at small (e.g. Asian) restaurants are more honest
than big chains’ imagery. Sun-bleached laminated photos at old takeaway places come up with affection.</li>
<li><b>Company size matters.</b> Several excuse a struggling kiosk or a small pizzeria with tight
margins, but not a large ICA Maxi store that could afford a designer. Similar generic AI menu
designs were also seen across restaurants in Tallinn and in cafés in Stockholm’s Gamla stan.</li>
<li><b>Disgust and avoidance.</b> Commenters write things like “I want to throw up”, say the food
triggers trypophobia, that they lose their appetite, would turn around in the door, or boycott.</li>
<li><b>Dissenting views.</b> A minority do not care (“good prices anyway”: two sausages with mash,
shrimp salad and a drink for 50 kr), think a menu is one of the best uses of AI, accept AI if the
design is clean, or think people spend too much energy hating AI compared with issues like
propaganda.</li>
</ul>

<h3>5.3 All comments (verbatim, feed order)</h3>
<div class="comments">
{''.join(ctxt)}
</div>
</section>
"""


def ch_unavailable():
    return f"""
<section>
<h2 id="ch6">Chapter 6. Sources that could not be retrieved: The New York Times and TikTok</h2>
<h3>6.1 The New York Times: “Why A.I. Food Slop Looks So Gross”</h3>
{nytimes_body()}
<h3>6.2 TikTok discovery page: “ai food looks disgusting”</h3>
{tiktok_body()}
</section>
"""


def ch_nytimes():
    return f"""
<section>
<h2 id="ch6">The New York Times: “Why A.I. Food Slop Looks So Gross” (not retrievable)</h2>
{nytimes_body()}
</section>
"""


def ch_tiktok():
    return f"""
<section>
<h2 id="ch6">TikTok discovery page: “ai food looks disgusting” (feed not retrievable)</h2>
{tiktok_body()}
</section>
"""


def nytimes_body():
    ny = meta("nytimes")
    return f"""
{source_card("The New York Times (interactive), 6 October 2026", ny, [("Note", ny.get("note", ""))])}
<p>The archive kept only the publisher’s robot-block response. Both the direct page and a public
gift link were blocked. The title survives from the link, but this book has no article body or
images from this source, and none of its content should be inferred from the title.</p>
"""


def tiktok_body():
    tt = meta("tiktok")
    return f"""
{source_card("TikTok discovery page", tt, [("Note", tt.get("note", ""))])}
<p>The linked page is TikTok’s search/discovery page for the phrase “ai food looks disgusting”,
which shows that this complaint is common on the platform. The archived HTML contains only TikTok’s
application shell and localisation data. The result videos load in the browser and were not
present in the server response, so no TikTok videos are included here. CNN (chapter 3) reports that
TikTok users coined the term “AI slop menus”, and that Adaeze Onejeme posted TikTok videos of an
“AI flyer epidemic” at a Hollywood night market.</p>
"""


def appendices():
    rows = []
    for d in ["guardian", "cnn", "instagram", "reddit", "nytimes", "tiktok"]:
        files = sorted(p.relative_to(SRC).as_posix() for p in (SRC / d).rglob("*") if p.is_file())
        rows.append(f"<tr><td>{d}</td><td>{esc(meta(d)['url'])}</td><td>{'<br>'.join(esc(f) for f in files)}</td></tr>")
    return f"""
<section>
<h2 id="appA">Appendix A: Catalogue of sources and files</h2>
<table class="grid small">
<tr><th>Directory</th><th>Original URL</th><th>Archived files</th></tr>
{''.join(rows)}
</table>
<p class="small">Each directory holds <code>metadata.json</code> and <code>content.txt</code>.
<code>source.html</code> is the unmodified direct response. <code>MANIFEST.sha256</code> in the
archive root records checksums.</p>

<h3>A.1 Image catalogue</h3>
<table class="grid small">
<tr><th>Figure</th><th>File</th><th>Shows</th></tr>
<tr><td>2-1</td><td>guardian/images/image-01.jpg</td><td>Bella Cafe (San Francisco) western-themed breakfast menu poster, made with ChatGPT</td></tr>
<tr><td>2-2</td><td>guardian/images/image-02.jpg</td><td>Jamaican BBQ pop-up (Denver) combo menu, meat looking like leather belts with beetles</td></tr>
<tr><td>2-3</td><td>guardian/images/image-03.jpg</td><td>DoorDash “AI-enhanced” Chicken Katsu listing</td></tr>
<tr><td>3-1</td><td>cnn/images/image-01.jpg</td><td>New York deli hot-entrees board with ring-shaped “shrimp scampi” (photo: Sam Biddle)</td></tr>
<tr><td>3-2</td><td>cnn/images/image-02.jpg</td><td>Freedom 250 AI portraits of founding fathers (related CNN story, not food)</td></tr>
<tr><td>3-3</td><td>cnn/images/image-03.jpg</td><td>Freesh Juice Bar AI-style smoothie advertisement (CNN lead image)</td></tr>
<tr><td>4-1</td><td>instagram/…mp4 (frames)</td><td>Eight frames from Jenny Frennberg’s reel, including the “MALATANG – Nu på buffén!” poster</td></tr>
<tr><td>4-2</td><td>instagram/…jpg</td><td>Reel thumbnail: Jenny Frennberg on a Stockholm street</td></tr>
<tr><td>5-1</td><td>reddit/images/image-01.jpg</td><td>ICA Maxi Stormarknad (Skellefteå) AI-generated Pokémon-themed hot-dog menu screen</td></tr>
</table>
</section>

<section>
<h2 id="appB">Appendix B: Glossary of key concepts, people and organisations</h2>
<dl>
<dt>AI slop / AI slop menus</dt><dd>Pejorative term for low-effort generative AI content. TikTok users apply it to restaurant menus with AI images (CNN).</dd>
<dt>Uncanny valley</dt><dd>Concept introduced by Japanese roboticist Masahiro Mori in 1970: eerie or repellent feelings caused by near-human figures with slight imperfections. Applied to near-realistic AI food images (CNN, Guardian).</dd>
<dt>Food neophobia</dt><dd>Fear of or reluctance to try unfamiliar foods; one hypothesis for aversion to AI food images (Diel, CNN).</dd>
<dt>Disgust (evolutionary)</dt><dd>An emotion that protects against harmful or contaminated food. Slightly-off food images may trigger it (Diel, CNN).</dd>
<dt>Alexander Diel</dt><dd>Psychologist at the University of Duisburg-Essen, Germany, who studies responses to AI food images. A 2025 peer-reviewed study found slightly imperfect AI food rated more uncanny and less pleasant; a 2026 study found lower desire to eat AI food despite equal health and calorie judgements.</dd>
<dt>Charles Spence</dt><dd>Oxford professor of experimental psychology. His 2024 study found that consumers preferred AI food images until told they were AI-made. AI tends to add fat (e.g. butter) when asked to make food look appealing, which might nudge people toward bigger, fattier portions (Guardian).</dd>
<dt>National Restaurant Association (NRA)</dt><dd>Its 2026 report says 26% of US restaurant operators use AI, mostly for marketing, and that 42% did not turn a profit in 2025.</dd>
<dt>Slerp</dt><dd>British restaurant ordering platform. Its 2023 survey of 100 people found more than 60% could not tell AI food images from photos (founder JP Then).</dd>
<dt>Nancy Hopkins</dt><dd>President of the International Association of Culinary Professionals. She advises using AI for scheduling and payroll, not food pictures, and using smartphone photos or illustrations instead: “Real people, real stories will always be better.”</dd>
<dt>Hunter Lewis</dt><dd>Editor in chief of Food &amp; Wine. He says AI use should be invisible to diners: “The American dining public is smart.”</dd>
<dt>Kat Kinsman</dt><dd>Food &amp; Wine features editor who wrote about the “uncanny valley of a dish I know cannot be real”.</dd>
<dt>Jamie Soja</dt><dd>Bay Area food photographer. AI gets texture, colour, arrangement and lighting wrong (Guardian).</dd>
<dt>Jill Sennett</dt><dd>Denver nurse who posted the Jamaican BBQ pop-up menu on X.</dd>
<dt>Grind &amp; Unwind</dt><dd>San Francisco café whose AI signage drew graffiti (“seriously”); owner Lyndsey Lozano spent about $700 removing it.</dd>
<dt>Bella Cafe</dt><dd>San Francisco café using ChatGPT-made menu signs; owner Nila Norero Salvatore likes them. Brandon Hill posted about it on X.</dd>
<dt>Chugwater Soda Fountain</dt><dd>Wyoming restaurant whose hand-written “no AI” pledge got more than 200,000 Instagram likes.</dd>
<dt>DoorDash “AI-enhanced”</dt><dd>Label applied automatically when restaurants use DoorDash’s AI photo tool to adjust lighting, colour or background. Misleading images are prohibited by policy.</dd>
<dt>Adaeze Onejeme, Julia Damphouse, Sam Biddle</dt><dd>People in the CNN article who documented AI menus in Los Angeles (“AI flyer epidemic”), Berlin, and a New York deli (“shrimp scampi”) respectively.</dd>
<dt>Jenny Frennberg</dt><dd>Stockholm food creator (“Stockholm Food Gems”) whose reel urges Swedish restaurateurs to skip AI menu images.</dd>
<dt>ICA Maxi Stormarknad, Skellefteå</dt><dd>Swedish supermarket whose AI-generated, Pokémon-themed street-food menu set off the r/sweden thread.</dd>
</dl>
</section>
"""


CSS = """
@page { size: A4; margin: 20mm 18mm 20mm 18mm;
  @bottom-center { content: counter(page); font: 9pt 'DejaVu Sans', sans-serif; color: #666; }
  @top-right { content: "Food and AI: A Sourcebook"; font: 8pt 'DejaVu Sans', sans-serif; color: #999; } }
@page :first { @bottom-center { content: none; } @top-right { content: none; } }
body { font-family: 'DejaVu Serif', 'Noto Color Emoji', serif; font-size: 10.5pt; line-height: 1.45; color: #111; }
h1, h2, h3, .chead, .figlabel, th, .kicker, .toc { font-family: 'DejaVu Sans', 'Noto Color Emoji', sans-serif; }
h2 { font-size: 17pt; break-before: page; border-bottom: 2px solid #333; padding-bottom: 4pt; margin-top: 0; }
.about h2#about { break-before: page; }
.about h2#contents { break-before: auto; margin-top: 24pt; }
h3 { font-size: 12.5pt; margin-top: 16pt; break-after: avoid; }
.title-page { height: 240mm; display: flex; flex-direction: column; justify-content: center; }
.book-title { font-size: 30pt; line-height: 1.15; margin: 8pt 0 16pt; }
.subtitle { font-size: 13pt; color: #333; }
.kicker { text-transform: uppercase; letter-spacing: .06em; font-size: 9pt; color: #666; }
.small { font-size: 8.5pt; color: #444; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.5pt; overflow-wrap: anywhere; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 12pt; font-size: 9pt; }
th, td { border: 1px solid #bbb; padding: 4pt 6pt; vertical-align: top; text-align: left; overflow-wrap: anywhere; }
th { background: #eee; }
table.card th { width: 28%; }
table.subs td.tc { white-space: nowrap; font-family: 'DejaVu Sans Mono', monospace; font-size: 8pt; }
tr { break-inside: avoid; }
blockquote { margin: 8pt 0; padding: 6pt 12pt; border-left: 3px solid #999; background: #f6f6f6; }
figure { margin: 12pt 0; break-inside: avoid; }
figure img { display: block; max-width: 100%; max-height: 150mm; margin: 0 auto; border: 1px solid #ccc; }
figure.tall img { max-height: 175mm; }
figure.thumb img { max-height: 40mm; }
figure.thumbsmall img { max-height: 90mm; }
figure.frames img { max-height: 125mm; }
figcaption { font-size: 9pt; margin-top: 5pt; }
figcaption p { margin: 2pt 0; }
.figlabel { color: #555; font-size: 8.5pt; }
.comment { border-top: 1px solid #ddd; padding: 3pt 0; break-inside: avoid; }
.comment p { margin: 1pt 0; }
.chead { font-size: 8pt; color: #555; }
.toc a { color: #111; text-decoration: none; }
dt { font-weight: bold; font-family: 'DejaVu Sans', sans-serif; margin-top: 6pt; }
dd { margin-left: 14pt; }
.split-title { font-size: 20pt; line-height: 1.2; margin: 6pt 0 10pt; }
.split-head { border-bottom: 1px solid #ccc; margin-bottom: 14pt; }
.split-head + section h2 { break-before: auto; }
"""


def build_frames():
    mp4 = SRC / "instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4"
    frames = []
    for t in FRAME_TIMES:
        png = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(mp4), "-frames:v", "1",
             "-vf", "scale=360:-1", "-f", "image2pipe", "-vcodec", "png", "-"],
            check=True, capture_output=True).stdout
        frames.append(Image.open(io.BytesIO(png)).convert("RGB"))
    w, h = frames[0].size
    sheet = Image.new("RGB", (w * 4, h * 2), "white")
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % 4) * w, (i // 4) * h))
    return img_data_uri(sheet, max_side=1440)


def render(body, pdf_out, title, subject, skip_pages=0):
    """Render an HTML body to pdf_out with metadata and a chapter bookmark outline.

    skip_pages: leading pages to ignore when locating chapter headings (e.g. a
    contents page that repeats every chapter title).
    """
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>
<meta name="author" content="Food + AI web archive"><style>{CSS}</style></head><body>
{body}
</body></html>"""
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "book.html"
        tmp_pdf = Path(tmp) / "book.pdf"
        html_path.write_text(doc, encoding="utf-8")
        subprocess.run(
            ["chromium", "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={tmp_pdf}", html_path.as_uri()],
            check=True, capture_output=True)

        pdf = fitz.open(tmp_pdf)
        toc = []
        headings = [re.sub(r"<[^>]+>", "", h) for h in re.findall(r"<h2 id=\"[^\"]+\">(.*?)</h2>", doc)]
        start = skip_pages
        for hd in headings:
            key = html.unescape(hd)[:40]
            first = 1 if hd in ("About this book", "Contents") else start
            for pno in range(first, pdf.page_count):
                if pdf[pno].search_for(key):
                    toc.append([1, html.unescape(hd), pno + 1])
                    start = max(start, pno)
                    break
        pdf.set_toc(toc)
        pdf.set_metadata({"title": title, "author": "Compiled from the Food + AI web archive",
                          "subject": subject, "keywords": KEYWORDS})
        pdf.save(pdf_out, garbage=3, deflate=True)
        pages = pdf.page_count
        pdf.close()
    print(f"wrote {pdf_out.name}: {pages} pages, {pdf_out.stat().st_size / 1e6:.1f} MB, "
          f"{len(toc)} bookmarks")


def main():
    frames = build_frames()
    guardian, cnn, instagram, reddit = ch_guardian(), ch_cnn(), ch_instagram(frames), ch_reddit()

    # Full book, as a single file.
    render(front_matter() + ch_overview() + guardian + cnn + instagram + reddit
           + ch_unavailable() + appendices(),
           PDF_OUT, TITLE, "AI-generated food images on restaurant menus: news, research, social reactions",
           skip_pages=2)

    # Split edition: intro plus one file per source.
    render(front_matter(split=True) + ch_overview() + appendices(),
           OUT / "food-ai-intro.pdf", f"{TITLE}: Introduction",
           "Introduction, overview of sources and explanations, source catalogue, glossary",
           skip_pages=2)
    sources = [
        ("food-ai-guardian.pdf", "The Guardian: “Uncanny and unappetizing”", "Book chapter 2", guardian),
        ("food-ai-cnn.pdf", "CNN: “Why restaurants are facing backlash for fake food pictures”", "Book chapter 3", cnn),
        ("food-ai-instagram.pdf", "Instagram: Jenny Frennberg’s reel “AI-bilder på menyn? NEJ TACK!”", "Book chapter 4", instagram),
        ("food-ai-reddit.pdf", "Reddit r/sweden: AI-generated restaurant menus", "Book chapter 5", reddit),
        ("food-ai-nytimes.pdf", "The New York Times: “Why A.I. Food Slop Looks So Gross”", "Book chapter 6.1", ch_nytimes()),
        ("food-ai-tiktok.pdf", "TikTok: “ai food looks disgusting” discovery page", "Book chapter 6.2", ch_tiktok()),
    ]
    for fname, src_title, chapter, body in sources:
        render(split_header(src_title, chapter) + body, OUT / fname, f"{TITLE}: {src_title}",
               f"{src_title}. Source material on AI-generated food images on restaurant menus.")


if __name__ == "__main__":
    sys.exit(main())
