#!/usr/bin/env python3
"""Generate a self-contained HTML guide to the food + AI source archive."""

from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path


from media import HF_DATASET, MEDIA, ROOT, is_media, local

PAGES = ROOT / "pages"
ASSETS = ROOT / "web-assets"

# Binary media are served from the Hugging Face dataset repo, whose paths mirror
# this archive (see src/media.py and src/publish_assets.sh). FOOD_AI_LOCAL_ASSETS=1
# builds relative links instead, for an offline preview served with
# rangeserver.py --overlay web/food-ai=/data/media/food-ai (media come from the mirror).
ASSET_BASE = f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main/"
LOCAL_ASSETS = os.environ.get("FOOD_AI_LOCAL_ASSETS") == "1"

SUMMARIES = {
    "guardian": (
        "Reporting on restaurants adopting AI imagery to cut marketing costs—and the diners who read its "
        "rubbery textures, impossible details, and synthetic sheen as unappetizing or misleading."
    ),
    "cnn": (
        "A science-led account of why near-real food can feel wrong: uncanny-valley effects, contamination "
        "signals, food neophobia, and the trust gap between a generated picture and the dish served."
    ),
    "instagram": (
        "Swedish food creator Jenny Frennberg argues for authentic menu photography over generated stand-ins, "
        "framing the reel as encouragement rather than a call to boycott individual restaurants."
    ),
    "reddit": (
        "A Swedish discussion with 199 feed entries. Commenters debate visual clutter, authenticity, real food "
        "photography, misleading representation, and what menu imagery says about a restaurant."
    ),
    "tiktok": (
        "The linked discovery query documents the phrase “AI food looks disgusting.” Its page shell is archived, "
        "but TikTok did not expose the result videos without client-side/API loading."
    ),
    "nytimes": (
        "The linked interactive is titled “Why A.I. Food Slop Looks So Gross.” The publisher blocked automated "
        "retrieval, so the archive preserves the response and records the gap without fabricating a summary."
    ),
}

SOURCE_LABELS = {
    "guardian": "The Guardian",
    "cnn": "CNN",
    "instagram": "Instagram",
    "reddit": "Reddit / r/sweden",
    "tiktok": "TikTok",
    "nytimes": "The New York Times",
}

SOURCE_ORDER = ["guardian", "cnn", "instagram", "reddit", "tiktok", "nytimes"]

# The two SVT pieces (26 October 2026) the archive was compiled for; files in svt/ (see svt/metadata.json).
SVT_DIR = ROOT / "svt"
SVT_LANGS = [("en", "English"), ("sv", "Svenska"), ("de", "Deutsch")]
SVT_CLIPS = [
    {
        "id": "nyheter-helsingborg",
        "title": "Forskaren: Därför väcker AI-bilder på mat ilska",
        "programme": "SVT Nyheter Helsingborg",
        "length": "1 min 14 s",
        "portrait": True,
        "summary": (
            "A short vertical piece for svt.se: why we are evolutionarily alert to food that looks slightly wrong, "
            "why food images affect us physiologically, and how technology acceptance may soften reactions over time."
        ),
    },
    {
        "id": "sverige-live",
        "title": "Sverige Live: live from Lund",
        "programme": "Sverige Live, SVT1",
        "length": "6 min 30 s",
        "portrait": False,
        "summary": (
            "A live segment from Lund with Joel Sund: why restaurants try generated images now, why food is a special "
            "genre, the evolutionary account of disgust, the uncanny valley, and whether we will get used to it."
        ),
    },
]

# AI-generated summaries (Gemini Notebook): an infographic and an audio overview; files in notebook/.
NOTEBOOK_DIR = ROOT / "notebook"
NOTEBOOK_INFOGRAPHIC = "notebook/ai-menu-imagery-infographic"   # .png full size, .jpg 1600 px preview
NOTEBOOK_AUDIO = "notebook/why-ai-food-menus-disgust-us"         # .m4a, .en.vtt, .en.txt

PDF_DIR = MEDIA / "pdf"
REF_DIR = ROOT / "references"
BIB_FILE = REF_DIR / "food-ai.bib"

# BibTeX keys of the six archived sources, mapped to their source pages.
BIB_SOURCE_PAGES = {
    "bonos2026uncanny": "guardian",
    "mack2026restaurants": "cnn",
    "frennberg2026ai": "instagram",
    "sensitivecream2026vad": "reddit",
    "tiktok2026ai": "tiktok",
    "nytimes2026ai": "nytimes",
}

BIB_GROUPS = [
    ("research", "Research literature", "Peer-reviewed studies and the original uncanny-valley essay cited by the reporting."),
    ("primary", "Archived sources", "The six topical links from svt.pdf, each preserved in this archive."),
    ("grey", "Reporting and industry sources", "News coverage, industry reports, and commentary linked from the Guardian and CNN articles."),
]

BIB_KIND_LABELS = {"article": "Journal article", "techreport": "Report", "misc": "Web source"}

PDF_EDITIONS = [
    ("food-ai-sourcebook.pdf", "Complete book", "Full sourcebook",
     "Every source in one document: overview, full article texts, transcripts, all Reddit comments, "
     "described images, source catalogue, and glossary."),
    ("food-ai-intro.pdf", "Section", "Introduction",
     "The interview questions, the six sources at a glance, recurring explanations, file catalogue, and glossary."),
    ("food-ai-guardian.pdf", "Section", "The Guardian",
     "The full extracted article with its three menu images and written visual descriptions."),
    ("food-ai-cnn.pdf", "Section", "CNN",
     "The full extracted article with its images and written visual descriptions."),
    ("food-ai-instagram.pdf", "Section", "Instagram",
     "Reel caption and translation, English and German transcripts, timed subtitles, and sampled video frames."),
    ("food-ai-reddit.pdf", "Section", "Reddit / r/sweden",
     "The original post and menu image, a thematic summary, and all 198 comments verbatim."),
    ("food-ai-tiktok.pdf", "Section", "TikTok",
     "Retrieval note for the discovery page whose result videos could not be archived."),
    ("food-ai-nytimes.pdf", "Section", "The New York Times",
     "Retrieval note for the interactive blocked by the publisher."),
]


def asset(path: str, prefix: str = "../", *, download: bool = False) -> str:
    """URL for an archive file: the HF dataset copy for binary media, else a relative link."""
    if LOCAL_ASSETS or not is_media(path):
        return prefix + path
    return ASSET_BASE + path + ("?download=true" if download else "")


def load_meta(source: str) -> dict:
    return json.loads((ROOT / source / "metadata.json").read_text(encoding="utf-8"))


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def shell(title: str, content: str, *, prefix: str = "../", body_class: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A sourcebook about AI-generated food imagery in menus and advertising.">
  <title>{html.escape(title)} · Food / AI Sourcebook</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='32' fill='%23dc4f32'/%3E%3Ctext x='32' y='39' text-anchor='middle' font-family='Arial' font-size='19' font-weight='700' fill='white'%3EF/A%3C/text%3E%3C/svg%3E">
  <link rel="stylesheet" href="{prefix}web-assets/site.css">
  <script defer src="{prefix}web-assets/site.js"></script>
</head>
<body class="{html.escape(body_class)}">
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="topbar">
    <a class="brand" href="{prefix}index.html" aria-label="Food and AI Sourcebook home">
      <span class="brand-mark" aria-hidden="true">F/A</span>
      <span>Food / AI <em>Sourcebook</em></span>
    </a>
    <nav aria-label="Primary navigation">
      <a href="{prefix}pages/svt.html">Interviews</a>
      <a href="{prefix}pages/images.html">Images</a>
      <a href="{prefix}pages/videos.html">Video</a>
      <a href="{prefix}pages/texts.html">Texts</a>
      <a href="{prefix}pages/references.html">References</a>
    </nav>
  </header>
  <main id="main">{content}</main>
  <footer class="site-footer">
    <p>Local research archive generated from the six topical links embedded in <code>svt.pdf</code>.</p>
    <p><a href="{prefix}README.md">Archive notes</a> · <a href="{prefix}MANIFEST.sha256">Checksums</a></p>
  </footer>
</body>
</html>"""


def status_class(meta: dict) -> str:
    status = meta.get("download_status", "")
    return "complete" if status.startswith("complete") else "partial"


def source_card(source: str) -> str:
    meta = load_meta(source)
    category = "article" if source in {"guardian", "cnn", "nytimes"} else "social"
    state = status_class(meta)
    return f"""
<article class="source-card" data-source-card data-category="{category}" data-state="{state}">
  <div class="card-topline">
    <span class="eyebrow">{html.escape(meta.get('kind', 'source'))}</span>
    <span class="status {state}">{'Archived' if state == 'complete' else 'Limited'}</span>
  </div>
  <h3>{html.escape(SOURCE_LABELS[source])}</h3>
  <p>{html.escape(SUMMARIES[source])}</p>
  <a class="text-link" href="pages/{source}.html">Explore source <span aria-hidden="true">→</span></a>
</article>"""


def pdf_card(filename: str, kind: str, title: str, summary: str) -> str:
    size = (PDF_DIR / filename).stat().st_size / 1e6
    return f"""
<article class="source-card">
  <div class="card-topline">
    <span class="eyebrow">{html.escape(kind)}</span>
    <span class="status complete">PDF · {size:.1f} MB</span>
  </div>
  <h3>{html.escape(title)}</h3>
  <p>{html.escape(summary)}</p>
  <a class="text-link" href="{asset(f'pdf/{filename}', '')}" target="_blank" rel="noopener">Open PDF <span aria-hidden="true">↗</span></a>
</article>"""


def build_index() -> None:
    cards = "\n".join(source_card(source) for source in SOURCE_ORDER)
    pdf_cards = "\n".join(pdf_card(*edition) for edition in PDF_EDITIONS if (PDF_DIR / edition[0]).exists())
    svt_stills = "".join(
        f"""<a class="still{' portrait' if clip['portrait'] else ''}" href="pages/svt.html#{clip['id']}"><img src="{asset(f"svt/{clip['id']}.jpg", '')}" alt="Still from {html.escape(clip['title'])}"><span>{html.escape(clip['programme'])} · {clip['length']}</span></a>"""
        for clip in SVT_CLIPS
    )
    if BIB_FILE.exists():
        pdf_cards += f"""
<article class="source-card">
  <div class="card-topline">
    <span class="eyebrow">References</span>
    <span class="status complete">BibTeX · {len(parse_bib(BIB_FILE))} entries</span>
  </div>
  <h3>Bibliography</h3>
  <p>Research literature, archived sources, and the reporting they cite, with DOIs and open-access full text where available.</p>
  <a class="text-link" href="pages/references.html">Browse references <span aria-hidden="true">→</span></a>
</article>"""
    content = f"""
<section class="hero">
  <div class="hero-copy">
    <p class="kicker">SVT interview research · October 2026</p>
    <h1>When food looks <span>almost</span> edible</h1>
    <p class="dek">A compact sourcebook on AI-generated menu imagery, the economics behind it, and the disgust, distrust, and uncanny recognition it can provoke.</p>
    <div class="hero-actions">
      <a class="button primary" href="pages/images.html">Enter the visual archive</a>
      <a class="button secondary" href="#sources">Browse six sources</a>
      <a class="button secondary" href="{asset('pdf/food-ai-sourcebook.pdf', '')}" target="_blank" rel="noopener">Read the PDF book ↗</a>
      <a class="button secondary" href="pages/notebook.html">Infographic + audio overview</a>
    </div>
  </div>
  <div class="hero-collage" aria-label="Examples from the source archive">
    <figure class="tile tile-large"><img src="{asset('guardian/images/image-01.jpg', '')}" alt="Restaurant breakfast menu with generated food images"><figcaption>Menu board · Guardian source</figcaption></figure>
    <figure class="tile tile-small"><img src="{asset('cnn/images/image-01.jpg', '')}" alt="Uncanny generated shrimp food image"><figcaption>Shrimp scampi · CNN source</figcaption></figure>
    <figure class="tile tile-tall"><img src="{asset('reddit/images/image-01.jpg', '')}" alt="AI-generated restaurant menu shared on Reddit"><figcaption>Swedish discussion · Reddit</figcaption></figure>
  </div>
</section>

<section class="interview-hero" aria-labelledby="interview-title">
  <div class="interview-copy">
    <p class="kicker">On air · SVT Helsingborg · 26 October 2026</p>
    <h2 id="interview-title">The interviews <span>with Joel Sund</span></h2>
    <p class="dek">The sourcebook was compiled to prepare two SVT pieces. Reporter Joel Sund asks Nils Holmberg, researcher in communication at Lund University, why AI-generated food images make so many people angry: in a short clip for SVT Nyheter Helsingborg and in a live segment on Sverige Live.</p>
    <div class="hero-actions">
      <a class="button primary" href="pages/svt.html">Watch both interviews</a>
      <a class="button secondary" href="pages/svt.html#sverige-live">Sverige Live segment · 6½ min</a>
    </div>
    <p class="interview-langs">Subtitles in English, Svenska and Deutsch · searchable transcripts</p>
  </div>
  <div class="interview-stills">{svt_stills}</div>
</section>

<section class="stats" aria-label="Archive at a glance">
  <div><strong>6</strong><span>linked sources</span></div>
  <div><strong>199</strong><span>Reddit feed entries</span></div>
  <div><strong>48s</strong><span>playable social video</span></div>
  <div><strong>7</strong><span>relevant visual assets</span></div>
</section>

<section class="section modes" aria-labelledby="modes-title">
  <div class="section-heading">
    <p class="kicker">Choose a lens</p>
    <h2 id="modes-title">Explore by medium</h2>
  </div>
  <div class="mode-grid">
    <a class="mode-card images-mode" href="pages/images.html"><span>01</span><h3>Images</h3><p>Menu boards, restaurant examples, thumbnails, and the Swedish post that prompted discussion.</p></a>
    <a class="mode-card video-mode" href="pages/videos.html"><span>02</span><h3>Video</h3><p>Watch the archived Instagram reel locally with its full Swedish caption and source metadata.</p></a>
    <a class="mode-card text-mode" href="pages/texts.html"><span>03</span><h3>Texts</h3><p>Read reporting, source summaries, and the complete accessible Reddit discussion.</p></a>
  </div>
</section>

<section class="section thesis" aria-labelledby="thesis-title">
  <div class="section-heading"><p class="kicker">What the material suggests</p><h2 id="thesis-title">More than an aesthetic complaint</h2></div>
  <div class="thesis-grid">
    <p class="lead-quote">“Uncanny” explains the near-real mismatch. Food adds something sharper: a learned need to spot contamination, decay, and false promises before taking a bite.</p>
    <div class="thesis-notes">
      <p><b>Why businesses use it</b><br>Speed and lower production costs make generated advertising tempting, especially under thin restaurant margins.</p>
      <p><b>Why audiences recoil</b><br>Wrong textures, repeated forms, and impossible anatomy collide with expectations of what food should safely look like.</p>
      <p><b>Why trust matters</b><br>A photograph can be styled, but it still implies a dish existed. A generated image may advertise food that never did.</p>
    </div>
  </div>
</section>

<section class="section" id="sources" aria-labelledby="sources-title">
  <div class="section-heading split-heading">
    <div><p class="kicker">Source shelf</p><h2 id="sources-title">Six perspectives</h2></div>
    <div class="filters" role="group" aria-label="Filter sources">
      <button class="active" type="button" data-filter="all">All</button>
      <button type="button" data-filter="article">Reporting</button>
      <button type="button" data-filter="social">Social</button>
      <button type="button" data-filter="partial">Limited</button>
    </div>
  </div>
  <div class="source-grid">{cards}</div>
</section>

<section class="section" id="pdf" aria-labelledby="pdf-title">
  <div class="section-heading">
    <p class="kicker">Read offline · search · RAG</p>
    <h2 id="pdf-title">PDF editions</h2>
  </div>
  <div class="source-grid">{pdf_cards}</div>
</section>
"""
    write(ROOT / "index.html", shell("Home", content, prefix="", body_class="home"))


def prose_to_html(text: str, *, skip_first_heading: bool = True) -> str:
    blocks = re.split(r"\n\s*\n", text.strip())
    rendered: list[str] = []
    heading_seen = False
    for block in blocks:
        block = re.sub(r"\s+", " ", block).strip()
        if block.startswith("# "):
            if skip_first_heading and not heading_seen:
                heading_seen = True
                continue
            heading_seen = True
            rendered.append(f"<h2>{html.escape(block[2:])}</h2>")
        elif block.startswith("## "):
            rendered.append(f"<h2>{html.escape(block[3:])}</h2>")
        else:
            rendered.append(f"<p>{html.escape(block)}</p>")
    return "\n".join(rendered)


def source_header(source: str) -> str:
    meta = load_meta(source)
    state = status_class(meta)
    return f"""
<section class="source-hero">
  <a class="back-link" href="../index.html#sources">← All sources</a>
  <div class="card-topline"><span class="eyebrow">{html.escape(meta.get('kind', 'source'))}</span><span class="status {state}">{html.escape(meta.get('download_status', ''))}</span></div>
  <h1>{html.escape(meta.get('title') or SOURCE_LABELS[source])}</h1>
  <p class="dek">{html.escape(SUMMARIES[source])}</p>
  <div class="source-actions">
    <a class="button primary" href="{html.escape(meta['url'])}" target="_blank" rel="noreferrer">Open original ↗</a>
    <a class="button secondary" href="../{source}/metadata.json">Metadata</a>
    <a class="button secondary" href="../{source}/source.html">Raw response</a>
  </div>
</section>"""


def gallery(source: str, *, exclude: set[str] | None = None) -> str:
    exclude = exclude or set()
    meta = load_meta(source)
    figures = []
    for image in meta.get("images", []):
        if image["file"] in exclude:
            continue
        figures.append(
            f"""<figure class="gallery-item"><a href="{asset(f'{source}/{image['file']}')}" target="_blank" rel="noopener"><img loading="lazy" src="{asset(f'{source}/{image['file']}')}" alt="{html.escape(image.get('caption_or_alt', ''))}"></a><figcaption>{html.escape(image.get('caption_or_alt', 'Source image'))}</figcaption></figure>"""
        )
    if not figures:
        return ""
    return f"<section class=\"source-section\"><div class=\"section-heading\"><p class=\"kicker\">Visual evidence</p><h2>Images from this source</h2></div><div class=\"gallery\">{''.join(figures)}</div></section>"


def build_news_page(source: str) -> None:
    text = (ROOT / source / "content.txt").read_text(encoding="utf-8")
    excluded = {"images/image-02.jpg"} if source == "cnn" else set()
    content = source_header(source) + gallery(source, exclude=excluded) + f"""
<section class="source-section reading-section">
  <div class="section-heading"><p class="kicker">Readable archive</p><h2>Full extracted article</h2></div>
  <div class="reading">{prose_to_html(text)}</div>
  <p class="download-line"><a href="../{source}/content.txt" download>Download plain text ↓</a></p>
</section>"""
    write(PAGES / f"{source}.html", shell(SOURCE_LABELS[source], content, body_class="source-page"))


def build_instagram_page() -> None:
    meta = load_meta("instagram")
    description = html.escape(meta.get("description", "")).replace("\n", "<br>")
    content = source_header("instagram") + f"""
<section class="source-section video-stage">
  <div class="video-frame">
    <video controls preload="metadata" poster="{asset('instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.jpg')}">
      <source src="{asset('instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4')}" type="video/mp4">
      <track kind="subtitles" srclang="en" label="English" src="../instagram/subtitles-en.vtt" default>
      <track kind="subtitles" srclang="de" label="Deutsch" src="../instagram/subtitles-de.vtt">
      Your browser cannot play this video. <a href="{asset('instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4', download=True)}">Download it instead.</a>
    </video>
  </div>
  <div class="video-notes"><p class="kicker">Archived playback · 48 seconds · English + German subtitles</p><h2>{html.escape(meta.get('uploader', 'Instagram'))}</h2><p>{description}</p><p><a class="text-link" href="{asset('instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4', download=True)}" download>Download MP4 ↓</a> · <a class="text-link" href="../instagram/transcript-en.txt">English transcript</a> · <a class="text-link" href="../instagram/transcript-de.txt">Deutsches Transkript</a></p></div>
</section>"""
    write(PAGES / "instagram.html", shell("Instagram reel", content, body_class="source-page"))


def parse_reddit_entries(text: str) -> list[dict[str, str]]:
    parts = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    entries = []
    for part in parts:
        if not part.startswith("## "):
            continue
        lines = part.strip().splitlines()
        title = lines[0][3:].strip()
        author = lines[1].removeprefix("Author: ").strip() if len(lines) > 1 else ""
        updated = lines[2].removeprefix("Updated: ").strip() if len(lines) > 2 else ""
        body = " ".join(line.strip() for line in lines[3:] if line.strip())
        entries.append({"title": title, "author": author, "updated": updated, "body": body})
    return entries


def build_reddit_page() -> None:
    text = (ROOT / "reddit" / "content.txt").read_text(encoding="utf-8")
    entries = parse_reddit_entries(text)
    cards = []
    for index, entry in enumerate(entries):
        search = " ".join(entry.values()).casefold()
        heading = "Original post" if index == 0 else entry["author"]
        cards.append(f"""
<article class="comment-card" data-comment data-search="{html.escape(search, quote=True)}">
  <div class="comment-meta"><b>{html.escape(heading)}</b><time>{html.escape(entry['updated'][:10])}</time></div>
  <p>{html.escape(entry['body'])}</p>
</article>""")
    content = source_header("reddit") + gallery("reddit") + f"""
<section class="source-section">
  <div class="section-heading split-heading"><div><p class="kicker">Swedish audience discussion</p><h2>Post + 198 comments</h2></div><label class="search-box">Search discussion<input type="search" placeholder="Try “bilder”, “mat”, or “AI”" data-comment-search></label></div>
  <p class="result-count" aria-live="polite" data-comment-count>{len(entries)} entries shown</p>
  <div class="comment-list">{''.join(cards)}</div>
  <p class="download-line"><a href="../reddit/content.txt" download>Download complete thread as text ↓</a> · <a href="../reddit/thread.atom">Open Atom archive</a></p>
</section>"""
    write(PAGES / "reddit.html", shell("Reddit discussion", content, body_class="source-page"))


def build_limited_page(source: str) -> None:
    meta = load_meta(source)
    note = meta.get("note", "The source was not fully retrievable.")
    specific = (
        "The title is preserved from the linked interactive. No article body or images are presented here because the retrieved file is only the publisher’s robot-block response."
        if source == "nytimes"
        else "The discovery URL is preserved as supplied. The saved HTML contains TikTok’s application shell and localization data, but no result cards or playable videos."
    )
    content = source_header(source) + f"""
<section class="source-section limitation-panel">
  <div><p class="kicker">Archive limitation</p><h2>What is—and is not—available</h2></div>
  <div><p>{html.escape(note)}</p><p>{html.escape(specific)}</p><p class="download-line"><a href="../{source}/source.html">Inspect saved response</a> · <a href="../{source}/content.txt">Read status note</a></p></div>
</section>"""
    write(PAGES / f"{source}.html", shell(SOURCE_LABELS[source], content, body_class="source-page"))


def relevant_images() -> list[tuple[str, str, str, str]]:
    records: list[tuple[str, str, str, str]] = []
    for source in ("guardian", "cnn", "reddit"):
        meta = load_meta(source)
        for item in meta.get("images", []):
            if source == "cnn" and item["file"] == "images/image-02.jpg":
                continue
            records.append((source, item["file"], item.get("caption_or_alt", ""), SOURCE_LABELS[source]))
    records.append(("instagram", "Video_by_jennyfrennberg-DeUPt1mIz5n.jpg", "Thumbnail for Jenny Frennberg’s reel about AI-generated menu images.", "Instagram"))
    return records


def build_images_page() -> None:
    figures = []
    for source, path, caption, label in relevant_images():
        figures.append(f"""
<figure class="archive-figure">
  <a href="{asset(f'{source}/{path}')}" target="_blank" rel="noopener"><img loading="lazy" src="{asset(f'{source}/{path}')}" alt="{html.escape(caption)}"></a>
  <figcaption><b>{html.escape(label)}</b><span>{html.escape(caption)}</span><a href="{source}.html">Source notes →</a></figcaption>
</figure>""")
    content = f"""
<section class="collection-hero"><a class="back-link" href="../index.html">← Home</a><p class="kicker">Visual archive</p><h1>Images that look wrong<br>before we know why</h1><p class="dek">Seven relevant visual assets from the linked reporting and social sources. Select an image to open the original archived file.</p></section>
<section class="masonry-gallery">{''.join(figures)}</section>"""
    write(PAGES / "images.html", shell("Images", content, body_class="collection-page"))


def build_video_page() -> None:
    meta = load_meta("instagram")
    caption = html.escape(meta.get("description", "")).replace("\n", "<br>")
    content = f"""
<section class="collection-hero"><a class="back-link" href="../index.html">← Home</a><p class="kicker">Video archive</p><h1>A Swedish reaction,<br>preserved in the archive</h1><p class="dek">Jenny Frennberg’s 48-second Instagram reel turns the subject into a direct appeal for authentic restaurant imagery.</p></section>
<section class="cinema">
  <div class="cinema-screen"><video controls preload="metadata" poster="{asset('instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.jpg')}"><source src="{asset('instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4')}" type="video/mp4"><track kind="subtitles" srclang="en" label="English" src="../instagram/subtitles-en.vtt" default><track kind="subtitles" srclang="de" label="Deutsch" src="../instagram/subtitles-de.vtt"></video></div>
  <aside><p class="kicker">Archived reel · English + German subtitles</p><h2>“AI-bilder på menyn? Nej tack.”</h2><p>{caption}</p><p><a class="text-link" href="../instagram/transcript-en.txt">English transcript</a> · <a class="text-link" href="../instagram/transcript-de.txt">Deutsches Transkript</a></p><a class="button primary" href="instagram.html">Full source page</a></aside>
</section>"""
    write(PAGES / "videos.html", shell("Video", content, body_class="collection-page"))


def vtt_cues(path: Path) -> list[tuple[float, float, str]]:
    """(start, end, text) for each cue of a WebVTT file."""
    def seconds(stamp: str) -> float:
        h, m, s = stamp.strip().split(" ")[0].split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    cues = []
    for block in re.split(r"\n{2,}", path.read_text(encoding="utf-8").strip()):
        lines = block.splitlines()
        timing = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing is not None:
            start, end = lines[timing].split("-->")
            cues.append((seconds(start), seconds(end), " ".join(lines[timing + 1:])))
    return cues


def clock(t: float) -> str:
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def cue_list(vtt: Path, lang: str, *, hidden: bool = False) -> str:
    """Clickable transcript (one button per cue) for the [data-clip] player behaviour in site.js."""
    items = "".join(
        f'<li><button type="button" data-start="{start:.2f}" data-end="{end:.2f}"><time>{clock(start)}</time><span>{html.escape(text)}</span></button></li>'
        for start, end, text in vtt_cues(vtt)
    )
    return f'<ol class="cue-list" data-cues="{lang}"{" hidden" if hidden else ""}>{items}</ol>'


def svt_clip(clip: dict, meta: dict) -> str:
    cid = clip["id"]
    info = next(c for c in meta["clips"] if c["id"] == cid)
    tracks = "".join(
        f'<track kind="subtitles" srclang="{lang}" label="{label}" src="../svt/{cid}.{lang}.vtt"{" default" if i == 0 else ""}>'
        for i, (lang, label) in enumerate(SVT_LANGS)
    )
    tabs = "".join(
        f'<button type="button" data-lang="{lang}"' + (' class="active"' if i == 0 else "") + f">{label}</button>"
        for i, (lang, label) in enumerate(SVT_LANGS)
    )
    lists = "".join(cue_list(SVT_DIR / f"{cid}.{lang}.vtt", lang, hidden=i > 0) for i, (lang, _) in enumerate(SVT_LANGS))
    downloads = " · ".join(f'<a href="../svt/{cid}.{lang}.txt">{label} (.txt)</a>' for lang, label in SVT_LANGS)
    return f"""
<section class="interview" id="{cid}" data-clip>
  <div class="interview-screen{' portrait' if clip['portrait'] else ''}">
    <video controls preload="metadata" playsinline poster="{asset(f'svt/{cid}.jpg')}">
      <source src="{asset(f'svt/{cid}.mp4')}" type="video/mp4">{tracks}
      Your browser cannot play this video. <a href="{asset(f'svt/{cid}.mp4', download=True)}">Download it instead.</a>
    </video>
  </div>
  <div class="interview-side">
    <p class="kicker">{html.escape(clip['programme'])} · {html.escape(info['published'])} · {clip['length']}</p>
    <h2>{html.escape(clip['title'])}</h2>
    <p>{html.escape(clip['summary'])}</p>
    <div class="cue-tools">
      <div class="lang-tabs" role="group" aria-label="Subtitle and transcript language">{tabs}</div>
      <input type="search" placeholder="Search transcript" aria-label="Search transcript" data-cue-search>
    </div>
    <div class="cue-box">{lists}</div>
    <p class="download-line"><a href="{html.escape(info['url'])}" target="_blank" rel="noreferrer">Original on SVT ↗</a> · Transcripts: {downloads}</p>
  </div>
</section>"""


def build_svt_page() -> None:
    meta = json.loads((SVT_DIR / "metadata.json").read_text(encoding="utf-8"))
    content = f"""
<section class="collection-hero"><a class="back-link" href="../index.html">← Home</a><p class="kicker">SVT Helsingborg · 26 October 2026</p><h1>The interviews<br>with Joel Sund</h1><p class="dek">Two SVT pieces in which reporter Joel Sund talks to Nils Holmberg, researcher in communication at Lund University, about why AI-generated food images provoke such strong reactions. Choose a subtitle language; click any line of the transcript to jump there.</p></section>
{''.join(svt_clip(clip, meta) for clip in SVT_CLIPS)}
<section class="source-section"><p class="text-detail">{html.escape(meta['subtitles'])} Video {html.escape(meta['rights'])} <a href="../svt/metadata.json">Metadata</a> · <a href="../svt/content.txt">Swedish transcripts as text</a></p></section>"""
    write(PAGES / "svt.html", shell("SVT interviews", content, body_class="collection-page"))


def build_notebook_page() -> None:
    meta = json.loads((NOTEBOOK_DIR / "metadata.json").read_text(encoding="utf-8"))
    audio, info = meta["audio"], meta["infographic"]
    vtt = ROOT / f"{NOTEBOOK_AUDIO}.en.vtt"
    content = f"""
<section class="collection-hero"><a class="back-link" href="../index.html">← Home</a><p class="kicker">AI-generated summaries · Gemini Notebook</p><h1>The argument<br>in one picture</h1><p class="dek">An infographic and an audio overview ({audio['length']}) about AI-generated menu imagery, both generated with Google’s Gemini Notebook. They are machine-made summaries, shown here as companions to the archived sources, not as sources themselves.</p></section>
<section class="source-section infographic">
  <figure>
    <a href="{asset(NOTEBOOK_INFOGRAPHIC + '.png')}" target="_blank" rel="noopener"><img src="{asset(NOTEBOOK_INFOGRAPHIC + '.jpg')}" width="1600" height="893" alt="{html.escape(info['alt'])}"></a>
    <figcaption><b>{html.escape(info['title'])}</b> Infographic generated with Gemini Notebook. <a href="{asset(NOTEBOOK_INFOGRAPHIC + '.png')}" target="_blank" rel="noopener">Full size PNG ({info['width']}×{info['height']}) ↗</a></figcaption>
  </figure>
  <div class="fact-check">
    <p class="kicker">Checking the figures</p>
    <p><b>26%</b> of restaurant owners use AI: reported by CNN from the National Restaurant Association’s annual report. <a class="text-link" href="cnn.html">CNN source page →</a></p>
    <p><b>37%</b> less desire to eat imperfect AI dishes: this figure does not appear in any of the archived sources or in the research article in the bibliography, so treat it as unverified.</p>
  </div>
</section>
<section class="interview" id="audio" data-clip>
  <div class="interview-screen audio-screen">
    <img src="{asset(NOTEBOOK_INFOGRAPHIC + '.jpg')}" alt="" width="1600" height="893">
    <audio controls preload="metadata" src="{asset(NOTEBOOK_AUDIO + '.m4a')}">Your browser cannot play this audio. <a href="{asset(NOTEBOOK_AUDIO + '.m4a', download=True)}">Download it instead.</a></audio>
  </div>
  <div class="interview-side">
    <p class="kicker">Audio overview · {audio['length']} · English</p>
    <h2>{html.escape(audio['title'])}</h2>
    <p>{html.escape(audio['summary'])}</p>
    <div class="cue-tools"><input type="search" placeholder="Search transcript" aria-label="Search transcript" data-cue-search></div>
    <div class="cue-box">{cue_list(vtt, 'en')}</div>
    <p class="download-line">{html.escape(meta['transcript_note'])} <a href="../{NOTEBOOK_AUDIO}.en.txt">Transcript (.txt)</a> · <a href="{asset(NOTEBOOK_AUDIO + '.m4a', download=True)}">Audio (.m4a) ↓</a></p>
  </div>
</section>"""
    write(PAGES / "notebook.html", shell("Infographic and audio overview", content, body_class="collection-page"))


def excerpt(source: str, paragraphs: int = 2) -> str:
    text = (ROOT / source / "content.txt").read_text(encoding="utf-8")
    blocks = [re.sub(r"^#+\s*", "", b.strip()) for b in re.split(r"\n\s*\n", text) if b.strip()]
    return " ".join(blocks[1 : 1 + paragraphs])


def build_texts_page() -> None:
    items = []
    for source in SOURCE_ORDER:
        meta = load_meta(source)
        if source in {"guardian", "cnn"}:
            sample = excerpt(source)
            detail = "Full extracted article"
        elif source == "reddit":
            sample = excerpt(source, 1)
            detail = "Original post + 198 comments"
        elif source == "instagram":
            sample = meta.get("description", "")
            detail = "Full reel caption"
        else:
            sample = meta.get("note", "")
            detail = "Retrieval note"
        items.append(f"""
<article class="text-shelf-item">
  <div><span class="eyebrow">{html.escape(meta.get('kind', 'source'))}</span><h2>{html.escape(SOURCE_LABELS[source])}</h2><p class="text-detail">{html.escape(detail)}</p></div>
  <div><p>{html.escape(sample)}</p><a class="text-link" href="{source}.html">Read source page →</a></div>
</article>""")
    content = f"""
<section class="collection-hero"><a class="back-link" href="../index.html">← Home</a><p class="kicker">Text archive</p><h1>Reporting, reactions,<br>and retrieval notes</h1><p class="dek">Readable versions of everything the archive could access, with limitations kept visible.</p></section>
<section class="text-shelf">{''.join(items)}</section>"""
    write(PAGES / "texts.html", shell("Texts", content, body_class="collection-page"))


LATEX_REPLACEMENTS = [
    (r'{\"a}', "ä"), (r'{\"o}', "ö"), (r'{\"u}', "ü"), (r"{\aa}", "å"), (r"\&", "&"), (r"\%", "%"),
    (r"\$", "$"), (r"\_", "_"), ("``", "“"), ("''", "”"), ("--", "–"),
]


def latex_to_text(value: str) -> str:
    for latex, char in LATEX_REPLACEMENTS:
        value = value.replace(latex, char)
    return re.sub(r"\s+", " ", value.replace("{", "").replace("}", "")).strip()


def parse_bib(path: Path) -> list[dict[str, str]]:
    """Minimal BibTeX reader for the archive's own bibliography (braced or bare field values)."""
    text = path.read_text(encoding="utf-8")
    entries = []
    for match in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        entry = {"type": match.group(1).lower(), "key": match.group(2)}
        pos = match.end()
        while True:
            bare = re.compile(r"\s*(\w+)\s*=\s*(\w+)\s*,?").match(text, pos)
            if bare:
                entry[bare.group(1).lower()] = bare.group(2)
                pos = bare.end()
                continue
            field = re.compile(r"\s*(\w+)\s*=\s*\{").match(text, pos)
            if not field:
                break
            depth, i = 1, field.end()
            while depth:
                depth += {"{": 1, "}": -1}.get(text[i], 0)
                i += 1
            entry[field.group(1).lower()] = text[field.end():i - 1]
            pos = re.compile(r"\s*,?").match(text, i).end()
        entries.append(entry)
    return entries


def bib_authors(raw: str) -> str:
    names = []
    for name in raw.split(" and "):
        name = name.strip()
        if name.startswith("{"):
            names.append(latex_to_text(name))
            continue
        last, _, first = (latex_to_text(part) for part in name.partition(","))
        initials = " ".join(f"{part[0]}." for part in re.split(r"[\s-]+", first) if part)
        names.append(f"{last}, {initials}" if initials else last)
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + ", & " + names[-1]


def bib_short(entry: dict[str, str]) -> str:
    """Author–year label such as “Diel et al. 2025” or “Califano & Spence 2024”."""
    lasts = [latex_to_text(name).split(",")[0] for name in entry.get("author", "").split(" and ")]
    label = lasts[0] if len(lasts) == 1 else f"{lasts[0]} & {lasts[1]}" if len(lasts) == 2 else f"{lasts[0]} et al."
    return f"{label} {entry.get('year', 'n.d.')}"


def bib_group(entry: dict[str, str]) -> str:
    if entry["key"] in BIB_SOURCE_PAGES:
        return "primary"
    return "research" if entry["type"] == "article" else "grey"


MONTHS = dict(zip("jan feb mar apr may jun jul aug sep oct nov dec".split(), (
    "January February March April May June July August September October November December".split())))


def bib_citation(entry: dict[str, str]) -> str:
    """Format an entry as an APA-style reference (HTML)."""
    get = lambda field: latex_to_text(entry.get(field, ""))
    year = get("year") or "n.d."
    if entry.get("month") and entry["type"] != "article":
        day = f" {get('day')}" if entry.get("day") else ""
        year += f", {MONTHS.get(entry['month'].strip().lower(), entry['month'])}{day}"
    title = get("title")
    title += "" if title.endswith(("?", "!", ".")) else "."
    parts = [f"{html.escape(bib_authors(entry.get('author', '')))} ({html.escape(year)}). {html.escape(title)}"]
    if entry["type"] == "article":
        venue = f"<i>{html.escape(get('journal'))}</i>"
        if entry.get("volume"):
            venue += f", <i>{html.escape(get('volume'))}</i>"
        if entry.get("number"):
            venue += f"({html.escape(get('number'))})"
        if entry.get("pages"):
            venue += f", {html.escape(get('pages'))}"
        parts.append(venue + ".")
    else:
        venue = get("howpublished") or get("institution")
        if venue:
            parts.append(f"<i>{html.escape(venue)}</i>.")
    return " ".join(parts)


def bib_note(entry: dict[str, str], keys: set[str]) -> str:
    note = html.escape(latex_to_text(entry.get("note", "")))
    return re.sub(r"\b(" + "|".join(map(re.escape, keys)) + r")\b", r'<a href="#\1">\1</a>', note) if keys else note


def bib_links(entry: dict[str, str]) -> str:
    links = []
    if entry.get("file") and local("references/" + entry["file"]).exists():
        links.append(f'<a href="{asset("references/" + entry["file"])}" target="_blank" rel="noopener">Full text (PDF) ↗</a>')
    if entry.get("doi"):
        doi = entry["doi"]
        links.append(f'<a href="https://doi.org/{html.escape(doi)}" target="_blank" rel="noopener">doi:{html.escape(doi)} ↗</a>')
    elif entry.get("url"):
        links.append(f'<a href="{html.escape(entry["url"])}" target="_blank" rel="noopener">Original URL ↗</a>')
    if entry["key"] in BIB_SOURCE_PAGES:
        links.append(f'<a href="{BIB_SOURCE_PAGES[entry["key"]]}.html">Archived source page →</a>')
    return " · ".join(links)


def build_references_page() -> None:
    if not BIB_FILE.exists():
        return
    entries = parse_bib(BIB_FILE)
    keys = {entry["key"] for entry in entries}
    groups = []
    for group, title, dek in BIB_GROUPS:
        items = "".join(f"""
<article class="text-shelf-item" id="{html.escape(entry['key'])}">
  <div><span class="eyebrow">{BIB_KIND_LABELS.get(entry['type'], entry['type'])}</span><h2>{html.escape(bib_short(entry))}</h2><p class="text-detail"><code>{html.escape(entry['key'])}</code></p></div>
  <div><p>{bib_citation(entry)}</p><p class="text-detail">{bib_note(entry, keys - {entry['key']})}</p><p class="download-line">{bib_links(entry)}</p></div>
</article>""" for entry in entries if bib_group(entry) == group)
        groups.append(f"""
<section class="text-shelf" aria-labelledby="refs-{group}">
  <div class="section-heading"><p class="kicker">{html.escape(dek)}</p><h2 id="refs-{group}">{html.escape(title)}</h2></div>{items}
</section>""")
    content = f"""
<section class="collection-hero"><a class="back-link" href="../index.html">← Home</a><p class="kicker">Bibliography · {len(entries)} entries</p><h1>Works cited<br>and consulted</h1><p class="dek">Research literature, the archived sources, and the reporting they draw on. Keys follow the Google Scholar pattern and match the BibTeX file.</p><p class="download-line"><a href="../references/{BIB_FILE.name}" target="_blank" rel="noopener">Download BibTeX ({BIB_FILE.name}) ↗</a></p></section>
{''.join(groups)}"""
    write(PAGES / "references.html", shell("References", content, body_class="collection-page"))


def main() -> None:
    PAGES.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    build_index()
    build_news_page("guardian")
    build_news_page("cnn")
    build_instagram_page()
    build_reddit_page()
    build_limited_page("tiktok")
    build_limited_page("nytimes")
    build_images_page()
    build_video_page()
    build_svt_page()
    build_notebook_page()
    build_texts_page()
    build_references_page()


if __name__ == "__main__":
    main()
