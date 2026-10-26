"""Find likely spelling variants of the same player name across the workbook.

Read-only. Collects every person-name-looking cell, normalizes it, and groups
names that are very similar (case/spacing/punctuation or small edit distance).
Usage: py -P scripts/name_audit.py "<file>.xlsx" [out.json]
"""
import difflib
import json
import re
import sys
from collections import defaultdict

import openpyxl

SKIP_SHEETS = {"Instructions", "Logos", "Standings", "AP Top 25", "Conference Champions", "CFB Playoff Tree"}
NOT_NAMES = re.compile(r"^(N/A|YES|NO|CUT|VS|@|HC|OC|DC|QB|RB|HB|WR|TE|FB|K|P|C|OT|OG|LT|LG|RG|RT|EDGE|DT|LB|CB|S|FS|SS|KR|"
                       r"MLB|LOLB|ROLB|LE|RE|ATH|Player|Team|Class|Pos|POS|Ovr|Stars|State|Offense|Defense|ST)$", re.I)
CLASS_SUFFIX = re.compile(r"\s*[-–]?\s*(FR|SO|JR|SR)\s*(\((RS|SR)\))?\s*$")
RATING_SUFFIX = re.compile(r"\s*-\s*\d{2}\s*$")


def clean(raw):
    s = str(raw).strip()
    s = RATING_SUFFIX.sub("", s)
    s = CLASS_SUFFIX.sub("", s)
    s = re.sub(r"\s*-\s*ROLB$", "", s)
    s = s.replace("*", "").strip(" -")
    s = re.sub(r"\s+", " ", s)
    return s


def looks_like_name(s):
    if not s or NOT_NAMES.match(s) or any(ch.isdigit() for ch in s):
        return False
    parts = s.split(" ")
    return 2 <= len(parts) <= 5 and all(p[:1].isalpha() for p in parts) and not s.isupper()


def key(s):
    return re.sub(r"[^a-z]", "", s.lower())


def main(path, out=None):
    wb = openpyxl.load_workbook(path, data_only=True)
    seen = defaultdict(set)  # cleaned name -> {sheet}
    for ws in wb.worksheets:
        if ws.title in SKIP_SHEETS:
            continue
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str):
                    n = clean(c.value)
                    if looks_like_name(n):
                        seen[n].add(ws.title.strip())
    names = sorted(seen)
    # union-find over similar names
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_last = defaultdict(list)
    for n in names:
        by_last[key(n.split(" ")[-1])[:3]].append(n)
        by_last[key(n.split(" ")[0])[:3]].append(n)
    for bucket in by_last.values():
        for i, a in enumerate(bucket):
            for b in bucket[i + 1:]:
                if find(a) == find(b):
                    continue
                ka, kb = key(a), key(b)
                r = difflib.SequenceMatcher(None, ka, kb).ratio()
                same_last = key(a.split(" ")[-1]) == key(b.split(" ")[-1])
                same_first = key(a.split(" ")[0]) == key(b.split(" ")[0])
                if ka == kb or r >= 0.9 or (r >= 0.8 and (same_last or same_first)):
                    parent[find(a)] = find(b)
    groups = defaultdict(list)
    for n in names:
        groups[find(n)].append(n)
    clusters = [sorted(g) for g in groups.values() if len(g) > 1]
    clusters.sort()
    result = [{"variants": {n: sorted(seen[n]) for n in g}} for g in clusters]
    for r in result:
        print(" | ".join(f"{n} [{', '.join(s)}]" for n, s in r["variants"].items()))
    print(f"\n{len(names)} distinct names, {len(clusters)} variant groups")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)


if __name__ == "__main__":
    main(*sys.argv[1:])
