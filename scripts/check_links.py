"""Check that every internal link and image in _site/ points at a file that exists.

Usage: py -P scripts/check_links.py     (exit code 1 on broken links)
"""
import os
import re
import sys
from collections import defaultdict
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
BASE = os.environ.get("BASE_PATH", "/")
ATTR = re.compile(r'(?:href|src)="([^"#?]*)(?:[?#][^"]*)?"')

broken = defaultdict(set)
pages = 0
for dirpath, _, files in os.walk(OUT):
    for fn in files:
        if not fn.endswith(".html"):
            continue
        pages += 1
        path = os.path.join(dirpath, fn)
        html = open(path, encoding="utf-8").read()
        for url in ATTR.findall(html):
            if not url or url.startswith(("http:", "https:", "mailto:", "data:", "javascript:")):
                continue
            u = unquote(urlparse(url).path)
            if u.startswith(BASE):
                target = os.path.join(OUT, u[len(BASE):])
            elif u.startswith("/"):
                target = os.path.join(OUT, u.lstrip("/"))
            else:
                target = os.path.join(dirpath, u)
            if target.endswith(("/", "\\")) or os.path.isdir(target):
                target = os.path.join(target, "index.html")
            if not os.path.exists(target):
                broken[u].add(os.path.relpath(path, OUT))

print(f"Checked {pages} pages: {len(broken)} broken targets")
for u, srcs in sorted(broken.items())[:30]:
    print(f"  {u}  <- {sorted(srcs)[:3]}")
sys.exit(1 if broken else 0)
