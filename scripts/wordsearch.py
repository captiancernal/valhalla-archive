"""Word Search puzzle themes generated from the data tables (M8).

Each theme is a list of words (surnames or school names, letters only) with the full
name shown in the word list. The page lays the grid out in the browser.
Usage: py -P scripts/wordsearch.py   (prints the themes)
"""
import os
import re
import sys
import unicodedata
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trivia import load_tables, SHORT, PROGRAMS  # noqa: E402

SUFFIXES = {"JR", "SR", "II", "III", "IV", "V"}
MIN_LEN, MAX_LEN = 3, 13
MAX_WORDS = 14


def surname(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    parts = [re.sub(r"[^A-Za-z]", "", x).upper() for x in s.split()]
    parts = [x for x in parts if x and x not in SUFFIXES]
    return parts[-1] if parts else ""


def letters(text):
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z]", "", s).upper()


def build(title, cat, blurb, items, key):
    """items: list of (word, label). Drops duplicates and words that don't fit."""
    seen, words = set(), []
    for w, label in items:
        if not (MIN_LEN <= len(w) <= MAX_LEN) or w in seen:
            continue
        seen.add(w)
        words.append({"w": w, "label": label})
        if len(words) >= MAX_WORDS:
            break
    if len(words) < 8:
        return None
    return {"id": key, "cat": cat, "title": title, "blurb": blurb, "words": words}


def generate(T):
    teams = {t["id"]: t for t in T["teams"]}
    name = lambda a: SHORT.get(a) or (teams.get(a) or {}).get("school") or a
    puzzles = []

    # Season rosters: Vikings starters from the depth chart
    dc = defaultdict(list)
    for d in T["depth_chart"]:
        if d["program"] == "CLEV" and d["depth"] == 1 and not d.get("projected"):
            dc[d["season"]].append(d)
    for y in sorted(dc):
        items = [(surname(d["player"]), f"{d['player']} ({d['slot'].rstrip('123')})") for d in dc[y]]
        p = build(f"{y} Vikings starters", "Rosters", f"The first-string Cleveland State lineup on the {y} depth chart.", items, f"roster-{y}")
        if p:
            puzzles.append(p)

    # Award winners by year (all schools)
    aw = defaultdict(list)
    for a in T["awards"]:
        aw[a["season"]].append(a)
    for y in sorted(aw):
        rows = sorted(aw[y], key=lambda a: (a["school"] not in PROGRAMS, a["award"]))
        items = [(surname(a["player"]), f"{a['player']} ({a['award']}, {name(a['school'])})") for a in rows]
        p = build(f"{y} award winners", "Award winners", f"The national award winners of {y}.", items, f"awards-{y}")
        if p:
            puzzles.append(p)

    # Program legends: award winners first, then All-Americans
    for prog in PROGRAMS:
        honored = defaultdict(lambda: {"aw": 0, "aa": 0, "years": set()})
        for a in T["awards"]:
            if a["school"] == prog:
                honored[a["player"]]["aw"] += 1
                honored[a["player"]]["years"].add(a["season"])
        for a in T["all_americans"]:
            if a["school"] == prog:
                honored[a["player"]]["aa"] += 1
                honored[a["player"]]["years"].add(a["season"])
        ranked = sorted(honored.items(), key=lambda kv: (-kv[1]["aw"], -kv[1]["aa"], kv[0]))
        for part, chunk in enumerate([ranked[:MAX_WORDS], ranked[MAX_WORDS:MAX_WORDS * 2]], 1):
            items = []
            for pl, h in chunk:
                yrs = sorted(h["years"])
                span = str(yrs[0]) if yrs[0] == yrs[-1] else f"{yrs[0]}-{str(yrs[-1])[2:]}"
                items.append((surname(pl), f"{pl} ({span})"))
            title = f"{SHORT[prog]} legends" + ("" if part == 1 else " II")
            p = build(title, "Legends", f"{SHORT[prog]}'s most decorated players: national award winners and All-Americans.", items, f"legends-{prog}-{part}")
            if p:
                puzzles.append(p)

    # Vikings schedules: opponent school names
    gs = defaultdict(list)
    for g in T["games"]:
        gs[g["season"]].append(g)
    for y in sorted(gs):
        items = []
        for g in gs[y]:
            school = name(g["opponent"])
            w = letters(school.replace("State", "").replace("(OH)", "").replace("(FL)", "")) if len(letters(school)) > MAX_LEN else letters(school)
            items.append((w, f"{school} ({g['result']} {g['clev_score']}-{g['opp_score']})"))
        p = build(f"{y} Vikings schedule", "Schedules", f"Every opponent Cleveland State played in {y}.", items, f"schedule-{y}")
        if p:
            puzzles.append(p)
    return {"puzzles": puzzles}


if __name__ == "__main__":
    d = generate(load_tables())
    from collections import Counter
    print(len(d["puzzles"]), Counter(p["cat"] for p in d["puzzles"]))
    for p in d["puzzles"][:2] + [x for x in d["puzzles"] if x["cat"] == "Legends"][:1] + [x for x in d["puzzles"] if x["cat"] == "Schedules"][-1:]:
        print(p["title"], [w["w"] for w in p["words"]])
