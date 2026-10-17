#!/usr/bin/env python3
"""Generate a self-contained HTML guide to the food + AI source archive."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PAGES = ROOT / "pages"
ASSETS = ROOT / "web-assets"

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
      <a href="{prefix}pages/images.html">Images</a>
      <a href="{prefix}pages/videos.html">Video</a>
      <a href="{prefix}pages/texts.html">Texts</a>
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


def build_index() -> None:
    cards = "\n".join(source_card(source) for source in SOURCE_ORDER)
    content = f"""
<section class="hero">
  <div class="hero-copy">
    <p class="kicker">SVT interview research · October 2026</p>
    <h1>When food looks <span>almost</span> edible</h1>
    <p class="dek">A compact sourcebook on AI-generated menu imagery, the economics behind it, and the disgust, distrust, and uncanny recognition it can provoke.</p>
    <div class="hero-actions">
      <a class="button primary" href="pages/images.html">Enter the visual archive</a>
      <a class="button secondary" href="#sources">Browse six sources</a>
    </div>
  </div>
  <div class="hero-collage" aria-label="Examples from the source archive">
    <figure class="tile tile-large"><img src="guardian/images/image-01.jpg" alt="Restaurant breakfast menu with generated food images"><figcaption>Menu board · Guardian source</figcaption></figure>
    <figure class="tile tile-small"><img src="cnn/images/image-01.jpg" alt="Uncanny generated shrimp food image"><figcaption>Shrimp scampi · CNN source</figcaption></figure>
    <figure class="tile tile-tall"><img src="reddit/images/image-01.jpg" alt="AI-generated restaurant menu shared on Reddit"><figcaption>Swedish discussion · Reddit</figcaption></figure>
  </div>
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
            f"""<figure class="gallery-item"><a href="../{source}/{html.escape(image['file'])}"><img loading="lazy" src="../{source}/{html.escape(image['file'])}" alt="{html.escape(image.get('caption_or_alt', ''))}"></a><figcaption>{html.escape(image.get('caption_or_alt', 'Source image'))}</figcaption></figure>"""
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
    <video controls preload="metadata" poster="../instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.jpg">
      <source src="../instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4" type="video/mp4">
      Your browser cannot play this video. <a href="../instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4">Download it instead.</a>
    </video>
  </div>
  <div class="video-notes"><p class="kicker">Local playback · 48 seconds</p><h2>{html.escape(meta.get('uploader', 'Instagram'))}</h2><p>{description}</p><a class="text-link" href="../instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4" download>Download MP4 ↓</a></div>
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
  <a href="../{source}/{html.escape(path)}"><img loading="lazy" src="../{source}/{html.escape(path)}" alt="{html.escape(caption)}"></a>
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
<section class="collection-hero"><a class="back-link" href="../index.html">← Home</a><p class="kicker">Video archive</p><h1>A Swedish reaction,<br>preserved locally</h1><p class="dek">Jenny Frennberg’s 48-second Instagram reel turns the subject into a direct appeal for authentic restaurant imagery.</p></section>
<section class="cinema">
  <div class="cinema-screen"><video controls preload="metadata" poster="../instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.jpg"><source src="../instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4" type="video/mp4"></video></div>
  <aside><p class="kicker">Archived reel</p><h2>“AI-bilder på menyn? Nej tack.”</h2><p>{caption}</p><a class="button primary" href="instagram.html">Full source page</a></aside>
</section>"""
    write(PAGES / "videos.html", shell("Video", content, body_class="collection-page"))


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
    build_texts_page()


if __name__ == "__main__":
    main()
