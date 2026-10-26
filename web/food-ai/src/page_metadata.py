"""Print citation metadata (title, author, date, site) found in saved HTML pages.

Used to compile references/food-ai.bib from the archived sources and the pages
they cite. Reads Open Graph / article meta tags and JSON-LD.

Usage:
    python src/page_metadata.py page1.html [page2.html ...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from bs4 import BeautifulSoup


def meta_content(soup: BeautifulSoup, *names: str) -> str | None:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"]
    return None


def page_info(path: Path) -> dict:
    soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    info = {
        "title": meta_content(soup, "og:title") or (soup.title.get_text(strip=True) if soup.title else None),
        "author": meta_content(soup, "author", "article:author", "parsely-author", "sailthru.author"),
        "date": meta_content(soup, "article:published_time", "pubdate", "publish-date", "parsely-pub-date", "date", "sailthru.date"),
        "site": meta_content(soup, "og:site_name"),
    }
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data])
        for item in items:
            if isinstance(item, dict) and item.get("datePublished"):
                info.setdefault("ld_date", item["datePublished"])
                authors = item.get("author")
                if authors:
                    authors = authors if isinstance(authors, list) else [authors]
                    info["ld_author"] = [a.get("name") for a in authors if isinstance(a, dict)]
                break
    return info


def main() -> None:
    for name in sys.argv[1:]:
        print(Path(name).name, json.dumps(page_info(Path(name)), ensure_ascii=False))


if __name__ == "__main__":
    main()
