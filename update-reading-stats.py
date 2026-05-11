#!/usr/bin/env python3
"""Fetch reading stats and 5-star books from Goodreads RSS."""

import json
import re
import urllib.request
import xml.etree.ElementTree as ET

USER_ID = "34752532"
STATS_OUTPUT = "reading-stats.json"
BOOKS_OUTPUT = "five-star-books.json"

# Strips Goodreads series suffixes like " (Earthsea Cycle, #4)" or " (Dune #3)".
SERIES_SUFFIX_RE = re.compile(r"\s*\([^()]*#[\d\-]+\)\s*$")


def fetch_shelf(shelf):
    """Yield all items on a Goodreads shelf, paginating the RSS feed."""
    page = 1
    while True:
        url = (
            f"https://www.goodreads.com/review/list_rss/{USER_ID}"
            f"?shelf={shelf}&per_page=200&page={page}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read()
        items = ET.fromstring(xml_data).findall(".//item")
        if not items:
            return
        for item in items:
            yield item
        page += 1


def clean_title(title):
    title = SERIES_SUFFIX_RE.sub("", title).strip()
    # Drop subtitle after the first colon to match the existing short-title style
    # (e.g. "Breakneck: China's Quest..." -> "Breakneck").
    if ":" in title:
        title = title.split(":", 1)[0].strip()
    return title


def main():
    read_items = list(fetch_shelf("read"))
    to_read_items = list(fetch_shelf("to-read"))

    five_star = {}
    for item in read_items:
        if (item.findtext("user_rating") or "").strip() != "5":
            continue
        title = clean_title((item.findtext("title") or "").strip())
        author = (item.findtext("author_name") or "").strip()
        if title and title not in five_star:
            five_star[title] = author

    stats = {"booksRead": len(read_items), "toRead": len(to_read_items)}
    with open(STATS_OUTPUT, "w") as f:
        json.dump(stats, f, indent=2)

    with open(BOOKS_OUTPUT, "w") as f:
        json.dump(five_star, f, indent=2, ensure_ascii=False)

    print(
        f"Updated: {stats['booksRead']} read, "
        f"{stats['toRead']} to-read, {len(five_star)} 5-star"
    )


if __name__ == "__main__":
    main()
