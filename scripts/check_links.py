"""Check that every internal link, image, data file and stylesheet font in _site/ points at a file that exists.

Matching is case-exact, because GitHub Pages runs on Linux where CLEV.png and clev.png are different
files (Windows treats them as the same, so a case slip would only break online).
It also flags inline scripts and onclick-style attributes, which the pages' security policy would block
(the one allowed inline script is the print-view starter in base.html, allowed by its hash).
Usage: py -P scripts/check_links.py     (exit code 1 on broken links or blocked scripts)
"""
import os
import re
import sys
from collections import defaultdict
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
BASE = os.environ.get("BASE_PATH", "/")
ATTR = re.compile(r'(?:href|src|data-src)="([^"#?]*)(?:[?#][^"]*)?"')
CSSURL = re.compile(r"""url\(["']?([^"')#?]+)""")
_listing = {}
INLINE_JS = re.compile(r"<script(?![^>]*\bsrc=)(?![^>]*application/json)[^>]*>(.*?)</script>", re.S)
ON_ATTR = re.compile(r"<[a-z][^>]*\son[a-z]+=", re.I)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_site import PRINT_BOOT  # noqa: E402


def exists_exact(path):
    """True if the path exists with exactly this upper/lower case in every part."""
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return False
    rel = os.path.relpath(path, OUT)
    cur = OUT
    for part in rel.split(os.sep):
        if part in (".", ""):
            continue
        if cur not in _listing:
            _listing[cur] = set(os.listdir(cur))
        if part not in _listing[cur]:
            return False
        cur = os.path.join(cur, part)
    return True


broken = defaultdict(set)
blocked = defaultdict(set)
pages = 0
for dirpath, _, files in os.walk(OUT):
    for fn in files:
        if not fn.endswith(".html"):
            continue
        pages += 1
        path = os.path.join(dirpath, fn)
        html = open(path, encoding="utf-8").read()
        if "Content-Security-Policy" in html:
            for body in INLINE_JS.findall(html):
                if body != PRINT_BOOT:
                    blocked["inline <script>"].add(os.path.relpath(path, OUT))
            if ON_ATTR.search(html):
                blocked["on...= attribute"].add(os.path.relpath(path, OUT))
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
            if not exists_exact(target):
                broken[u].add(os.path.relpath(path, OUT))

# Fonts and images referenced from stylesheets
for dirpath, _, files in os.walk(os.path.join(OUT, "assets", "css")):
    for fn in files:
        if fn.endswith(".css"):
            css = open(os.path.join(dirpath, fn), encoding="utf-8").read()
            for u in CSSURL.findall(css):
                if u.startswith(("data:", "http:", "https:")):
                    continue
                if not exists_exact(os.path.join(dirpath, unquote(u))):
                    broken[u].add(os.path.join("assets", "css", fn))

print(f"Checked {pages} pages: {len(broken)} broken targets")
for u, srcs in sorted(broken.items())[:30]:
    print(f"  {u}  <- {sorted(srcs)[:3]}")
for kind, srcs in sorted(blocked.items()):
    print(f"  BLOCKED by the security policy: {kind} on {len(srcs)} pages, e.g. {sorted(srcs)[:3]}")
sys.exit(1 if broken or blocked else 0)
