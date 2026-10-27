"""Split Decision columns: load, validate and fact-check.

Columns live in content/split-decision/columns/<season>/<game-id>.md:

    ---
    game: 2024-CLEV-01
    headline: "Headline here"
    pierogi: 3            # Mickey's Pierogi Index (wins only, 1-5)
    ---
    ## Mickey
    ...
    ## Ken
    ...
    ## Back and forth
    **Mickey:** ...
    **Ken:** ...
    ## Final Verdict
    One line.

Usage:
  py -P scripts/columns.py check [season]   validate + fact-check (exit 1 on errors)
"""
import glob
import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS = os.path.join(ROOT, "content", "split-decision", "columns")
SECTIONS = ["Mickey", "Ken", "Back and forth", "Final Verdict"]


def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"{path}: missing front matter")
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    parts = re.split(r"^##\s+(.+?)\s*$", body, flags=re.M)
    sections = {}
    for i in range(1, len(parts), 2):
        sections[parts[i].strip()] = parts[i + 1].strip()
    words = len(re.findall(r"[A-Za-z0-9'’.-]+", " ".join(sections.values())))
    return {"meta": meta, "sections": sections, "words": words, "path": path}


def load_all():
    out = []
    for path in sorted(glob.glob(os.path.join(COLS, "*", "*.md"))):
        out.append(parse(path))
    return out


def check(season=None):
    games = json.load(open(os.path.join(ROOT, "data", "tables", "games.json"), encoding="utf-8"))
    by_id = {g["id"]: g for g in games}
    errors, warnings = [], []
    cols = [c for c in load_all() if season is None or str(c["meta"].get("game", "")).startswith(str(season))]
    for c in cols:
        name = os.path.relpath(c["path"], ROOT)
        gid = c["meta"].get("game")
        g = by_id.get(gid)
        if not g:
            errors.append(f"{name}: unknown game id {gid!r}")
            continue
        if not c["meta"].get("headline"):
            errors.append(f"{name}: missing headline")
        for s in SECTIONS:
            if s not in c["sections"] or not c["sections"][s]:
                errors.append(f"{name}: missing section '{s}'")
        if not (300 <= c["words"] <= 450):
            warnings.append(f"{name}: {c['words']} words (target 300-450)")
        pz = c["meta"].get("pierogi")
        if g["result"] == "W" and not (isinstance(pz, int) and 1 <= pz <= 5):
            errors.append(f"{name}: a win needs pierogi 1-5")
        if g["result"] == "L" and pz:
            errors.append(f"{name}: losses get no pierogi")
        # Fact check: every "N-N" must be a real score or record known at this point in the season.
        season_games = [x for x in games if x["season"] == g["season"]]
        upto = season_games[: season_games.index(g) + 1]
        allowed = set()
        w = l = 0
        for x in upto:
            allowed |= {f"{x['clev_score']}-{x['opp_score']}", f"{x['opp_score']}-{x['clev_score']}"}
            w += x["result"] == "W"
            l += x["result"] == "L"
            allowed.add(f"{w}-{l}")
        for x in games:  # earlier seasons are fair game
            if x["season"] < g["season"]:
                allowed |= {f"{x['clev_score']}-{x['opp_score']}", f"{x['opp_score']}-{x['clev_score']}"}
        allowed |= set(c["meta"].get("allowed_pairs", []))
        text = " ".join(c["sections"].values()) + " " + c["meta"].get("headline", "")
        for pair in re.findall(r"(?<![\d.])(\d{1,3}-\d{1,3})(?![\d])", text):
            if pair not in allowed:
                errors.append(f"{name}: '{pair}' is not a score or record from the data at this point")
        is_last = g is season_games[-1]
        big = [n for n in re.findall(r"(?<![\d-])(\d{1,2},\d{3}|\d{3,4})(?![\d-])", text) if int(n.replace(",", "")) not in range(1900, 2100)]
        if big and not is_last:
            warnings.append(f"{name}: large numbers {big}; season totals only belong in the season's final column")
    for e in errors:
        print("ERROR", e)
    for w_ in warnings:
        print("WARN ", w_)
    print(f"{len(cols)} columns checked: {len(errors)} errors, {len(warnings)} warnings")
    return not errors


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        sys.exit(0 if check(sys.argv[2] if len(sys.argv) > 2 else None) else 1)
    print(__doc__)
