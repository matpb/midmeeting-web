#!/usr/bin/env python3
"""Parses og:*/twitter:*/canonical from the five pages and checks og:image files exist."""
import os
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "agents.html", "privacy.html", "thanks.html", "404.html"]

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "link" and d.get("rel") == "canonical":
            self.rows.append(("canonical", d.get("href")))
        if tag == "meta" and (d.get("property", "").startswith("og:") or d.get("name", "").startswith("twitter:")):
            key = d.get("property") or d.get("name")
            self.rows.append((key, d.get("content")))

ok = True
for page in PAGES:
    path = os.path.join(ROOT, page)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    p = MetaParser()
    p.feed(html)
    print(f"\n== {page} ==")
    for key, val in p.rows:
        print(f"  {key}: {val}")
        if key in ("og:image", "twitter:image"):
            rel = val.split("https://midmeeting.com/", 1)[-1]
            local = os.path.join(ROOT, rel)
            if not os.path.isfile(local):
                print(f"    !! MISSING FILE: {local}")
                ok = False

print("\nALL OG IMAGE FILES EXIST" if ok else "\nMISSING FILES DETECTED")
sys.exit(0 if ok else 1)
