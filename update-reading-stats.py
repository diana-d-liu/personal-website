#!/usr/bin/env python3
"""Fetch reading stats from Goodreads RSS and merge new 5-star books into the
hand-curated list.

- reading-stats.json: overwritten with current read / to-read counts.
- five-star-books.json: append-only — preserves existing curated entries
  (titles & authors as Diana has them) and only adds books rated 5 stars
  on Goodreads that aren't already present. Manual edits survive across
  runs; the routine only ever grows the list.
"""

import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET

USER_ID = "34752532"
STATS_OUTPUT = "reading-stats.json"
BOOKS_OUTPUT = "five-star-books.json"

# Strips Goodreads series suffixes like " (Earthsea Cycle, #4)" or " (Dune #3)".
SERIES_SUFFIX_RE = re.compile(r"\s*\([^()]*#[\d\-]+\)\s*$")
NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


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
    # Drop subtitle after the first colon to match the existing short-title style.
    if ":" in title:
        title = title.split(":", 1)[0].strip()
    return title


def normalize(title):
    """Loose match key: lowercase + alphanumeric only. Lets us treat
    'The Magician's Nephew' and 'The Magician’s Nephew' as the same book."""
    return NORMALIZE_RE.sub("", title.lower())


def main():
    read_items = list(fetch_shelf("read"))
    to_read_total = sum(1 for _ in fetch_shelf("to-read"))

    stats = {"booksRead": len(read_items), "toRead": to_read_total}
    with open(STATS_OUTPUT, "w") as f:
        json.dump(stats, f, indent=2)

    curated = {}
    if os.path.exists(BOOKS_OUTPUT):
        with open(BOOKS_OUTPUT) as f:
            curated = json.load(f)
    existing_keys = {normalize(t) for t in curated}

    added = []
    for item in read_items:
        if (item.findtext("user_rating") or "").strip() != "5":
            continue
        title = clean_title((item.findtext("title") or "").strip())
        author = (item.findtext("author_name") or "").strip()
        if not title or normalize(title) in existing_keys:
            continue
        curated[title] = author
        existing_keys.add(normalize(title))
        added.append(title)

    with open(BOOKS_OUTPUT, "w") as f:
        json.dump(curated, f, indent=2, ensure_ascii=False)

    suffix = f" (added: {', '.join(added)})" if added else ""
    print(
        f"Updated: {stats['booksRead']} read, {stats['toRead']} to-read, "
        f"{len(curated)} 5-star (+{len(added)}){suffix}"
    )


if __name__ == "__main__":
    main()
