#!/usr/bin/env python3
"""Build readable, source-separated archives from the links embedded in svt.pdf."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)

SOURCES = {
    "nytimes": {
        "url": "https://www.nytimes.com/interactive/2026/10/06/technology/ai-slop-food-images-restaurant-menus.html",
        "title": "Why A.I. Food Slop Looks So Gross",
        "kind": "news interactive",
    },
    "guardian": {
        "url": "https://www.theguardian.com/technology/2026/sep/06/ai-food-menu-images",
        "kind": "news article",
    },
    "cnn": {
        "url": "https://edition.cnn.com/2026/09/02/us/ai-food-slop-menus-viral-cec",
        "kind": "news article",
    },
    "instagram": {
        "url": "https://www.instagram.com/reel/DeUPt1mIz5n/",
        "kind": "social video",
    },
    "tiktok": {
        "url": "https://www.tiktok.com/discover/ai-food-looks-disgusting",
        "kind": "social discovery page",
    },
    "reddit": {
        "url": "https://www.reddit.com/r/sweden/comments/1wwl6wv/vad_tycker_ni_om_att_allt_fler_restauranger_har/",
        "kind": "social discussion",
    },
}


def meta_content(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
    return tag.get("content", "").strip() if tag else ""


def clean_article_text(soup: BeautifulSoup) -> str:
    article = soup.find("article")
    if article is None:
        return ""
    for tag in article.find_all(
        ["script", "style", "svg", "button", "nav", "aside", "form", "noscript"]
    ):
        tag.decompose()
    lines: list[str] = []
    for tag in article.find_all(["h1", "h2", "h3", "p", "figcaption"], recursive=True):
        text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
        if text and (not lines or text != lines[-1]):
            prefix = "# " if tag.name == "h1" else "## " if tag.name in {"h2", "h3"} else ""
            lines.append(prefix + text)
    return "\n\n".join(lines).strip() + "\n"


def article_images(soup: BeautifulSoup, source: str) -> list[tuple[str, str]]:
    article = soup.find("article")
    if article is None:
        return []
    candidates: list[tuple[str, str]] = []
    for img in article.find_all("img"):
        caption = img.get("alt", "").strip()
        urls: list[str] = []
        for attr in ("src", "data-src", "data-lazy-src"):
            if img.get(attr):
                urls.append(img[attr])
        for attr in ("srcset", "data-srcset"):
            if img.get(attr):
                choices = [part.strip().split() for part in img[attr].split(",")]
                if choices:
                    urls.append(choices[-1][0])
        for url in reversed(urls):
            if not url.startswith("http"):
                continue
            if source == "guardian" and "i.guim.co.uk/img/media/" not in url:
                continue
            if source == "cnn" and "media.cnn.com/api/v1/images/stellar/prod/" not in url:
                continue
            candidates.append((url, caption))
            break

    # Include the lead image if it is not represented in the article markup.
    og_image = meta_content(soup, "og:image")
    if og_image:
        candidates.append((og_image, "Open Graph lead image"))

    deduped: list[tuple[str, str]] = []
    seen_paths: set[str] = set()
    for url, caption in candidates:
        path = urlparse(url).path
        if path not in seen_paths:
            seen_paths.add(path)
            deduped.append((url, caption))
    return deduped


def download_images(source: str, items: list[tuple[str, str]]) -> list[dict[str, str]]:
    output_dir = ROOT / source / "images"
    output_dir.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    records: list[dict[str, str]] = []
    for index, (url, caption) in enumerate(items, 1):
        response = session.get(url, timeout=60)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";", 1)[0]
        suffix = mimetypes.guess_extension(content_type) or Path(urlparse(url).path).suffix or ".bin"
        if suffix == ".jpe":
            suffix = ".jpg"
        filename = f"image-{index:02d}{suffix}"
        (output_dir / filename).write_bytes(response.content)
        records.append(
            {
                "file": f"images/{filename}",
                "source_url": url,
                "caption_or_alt": caption,
                "content_type": content_type,
            }
        )
    return records


def process_news(source: str) -> dict:
    directory = ROOT / source
    soup = BeautifulSoup((directory / "source.html").read_text(errors="replace"), "lxml")
    record = dict(SOURCES[source])
    record.update(
        {
            "title": meta_content(soup, "og:title") or (soup.title.get_text(" ", strip=True) if soup.title else ""),
            "description": meta_content(soup, "og:description") or meta_content(soup, "description"),
            "download_status": "complete",
        }
    )
    (directory / "content.txt").write_text(clean_article_text(soup), encoding="utf-8")
    record["images"] = download_images(source, article_images(soup, source))
    (directory / "metadata.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return record


def process_instagram() -> dict:
    directory = ROOT / "instagram"
    info_path = next(directory.glob("*.info.json"))
    info = json.loads(info_path.read_text(encoding="utf-8"))
    record = dict(SOURCES["instagram"])
    record.update(
        {
            "title": info.get("title"),
            "description": info.get("description"),
            "uploader": info.get("uploader"),
            "duration_seconds": info.get("duration"),
            "timestamp": info.get("timestamp"),
            "download_status": "complete",
            "media_files": sorted(p.name for p in directory.glob("*.mp4")),
            "thumbnail_files": sorted(p.name for p in directory.glob("*.jpg")),
            "subtitle_files": sorted(p.name for p in directory.glob("*.vtt")),
            "transcript_files": sorted(p.name for p in directory.glob("transcript-*.txt")),
        }
    )
    lines = [
        record.get("title") or "Instagram reel",
        f"Uploader: {record.get('uploader') or ''}",
        f"Duration: {record.get('duration_seconds') or ''} seconds",
        "",
        record.get("description") or "",
        "",
    ]
    (directory / "content.txt").write_text("\n".join(lines), encoding="utf-8")
    (directory / "metadata.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return record


def process_reddit() -> dict:
    directory = ROOT / "reddit"
    atom = BeautifulSoup((directory / "thread.atom").read_text(errors="replace"), "xml")
    entries = atom.find_all("entry")
    lines: list[str] = []
    original_image = ""
    for number, entry in enumerate(entries):
        title = entry.title.get_text(" ", strip=True) if entry.title else ""
        author = entry.author.find("name").get_text(" ", strip=True) if entry.author and entry.author.find("name") else ""
        updated = entry.updated.get_text(strip=True) if entry.updated else ""
        content_html = entry.content.get_text() if entry.content else ""
        content_soup = BeautifulSoup(content_html, "html.parser")
        if number == 0:
            for anchor in content_soup.find_all("a", href=True):
                if "i.redd.it/" in anchor["href"]:
                    original_image = anchor["href"]
                    break
        for tag in content_soup.find_all(["img", "br"]):
            tag.decompose()
        body = re.sub(r"\s+", " ", content_soup.get_text(" ", strip=True)).strip()
        lines.extend([f"## {title}", f"Author: {author}", f"Updated: {updated}", "", body, ""])

    media: list[dict[str, str]] = []
    if original_image:
        media = download_images("reddit", [(original_image, "Menu image attached to the original post")])
    title = atom.feed.title.get_text(" ", strip=True) if atom.feed and atom.feed.title else ""
    record = dict(SOURCES["reddit"])
    record.update(
        {
            "title": title,
            "entry_count": len(entries),
            "download_status": "complete via Atom feed",
            "images": media,
        }
    )
    (directory / "content.txt").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    (directory / "metadata.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return record


def process_limited_sources() -> list[dict]:
    results = []
    for source, status, note in (
        (
            "nytimes",
            "blocked by publisher anti-bot protection",
            "The direct page and a public gift URL both returned the New York Times robot-block page.",
        ),
        (
            "tiktok",
            "page snapshot complete; feed media unavailable",
            "The linked discovery page requires client-side/API loading and returned no server-rendered result videos.",
        ),
    ):
        directory = ROOT / source
        soup = BeautifulSoup((directory / "source.html").read_text(errors="replace"), "lxml")
        record = dict(SOURCES[source])
        record.update(
            {
                "title": SOURCES[source].get("title") or (soup.title.get_text(" ", strip=True) if soup.title else ""),
                "download_status": status,
                "note": note,
            }
        )
        (directory / "content.txt").write_text(note + "\n", encoding="utf-8")
        (directory / "metadata.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        results.append(record)
    return results


def write_manifest() -> None:
    lines = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.name == "MANIFEST.sha256":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(ROOT)}")
    (ROOT / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if "--manifest-only" in sys.argv[1:]:
        write_manifest()
        return
    process_news("guardian")
    process_news("cnn")
    process_instagram()
    process_reddit()
    process_limited_sources()
    write_manifest()


if __name__ == "__main__":
    main()
