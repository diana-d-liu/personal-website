#!/usr/bin/env python3
"""Fetch reading stats from Goodreads RSS and write to reading-stats.json."""

import json
import urllib.request
import xml.etree.ElementTree as ET

USER_ID = "34752532"
OUTPUT = "reading-stats.json"

def count_shelf(shelf):
    """Count total books on a Goodreads shelf by paginating the RSS feed."""
    total = 0
    page = 1
    while True:
        url = f"https://www.goodreads.com/review/list_rss/{USER_ID}?shelf={shelf}&per_page=200&page={page}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        items = root.findall(".//item")
        if not items:
            break
        total += len(items)
        page += 1
    return total

def main():
    read_count = count_shelf("read")
    to_read_count = count_shelf("to-read")

    stats = {
        "booksRead": read_count,
        "toRead": to_read_count,
    }

    with open(OUTPUT, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Updated: {read_count} read, {to_read_count} to-read")

if __name__ == "__main__":
    main()
