"""Higher/Lower decks generated from the data tables (M8).

Each deck is a list of real stat lines that share one stat, so every comparison
is like-for-like. Usage: py -P scripts/higher_lower.py   (prints deck sizes)
build_site.py imports generate() and writes _site/assets/data/higherlower.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trivia import load_tables, SHORT, PROGRAMS  # noqa: E402

DECKS = [
    {"key": "passing", "label": "Passing yards", "unit": "passing yards", "scope": "in a season"},
    {"key": "rushing", "label": "Rushing yards", "unit": "rushing yards", "scope": "in a season"},
    {"key": "receiving", "label": "Receiving yards", "unit": "receiving yards", "scope": "in a season"},
    {"key": "tackles", "label": "Tackles", "unit": "tackles", "scope": "team leader, in a season"},
    {"key": "sacks", "label": "Sacks", "unit": "sacks", "scope": "team leader, in a season"},
    {"key": "ppg", "label": "Team points per game", "unit": "points per game", "scope": "in a season"},
    {"key": "gamepts", "label": "Vikings points in a game", "unit": "points", "scope": "in one game"},
]
MIN = {"passing": 500, "rushing": 300, "receiving": 300}


def generate(T):
    teams = {t["id"]: t for t in T["teams"]}
    name = lambda a: SHORT.get(a) or (teams.get(a) or {}).get("school") or a
    cards = []

    def add(deck, title, prog, season, sub, value, reveal=None):
        if value is None:
            return
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        cards.append({"d": deck, "t": title, "p": prog, "s": season, "sub": sub, "v": value, "r": reveal})

    # Cleveland State: every stat line from the stats tabs
    for r in T["player_seasons"]:
        if r["category"] in MIN and (r.get("yds") or 0) >= MIN[r["category"]]:
            add(r["category"], r["player"], "CLEV", r["season"], r.get("position") or "", r["yds"])
    # Ohio and Miami (OH): the season leaders are the only individual stats tracked
    for s in T["seasons"]:
        if s["program"] not in PROGRAMS:
            continue
        for cat, v in (s.get("leaders") or {}).items():
            if not v or v.get("value") is None:
                continue
            if cat in ("passing", "rushing", "receiving") and s["program"] != "CLEV":
                add(cat, v["player"], s["program"], s["season"], "Team leader", v["value"])
            elif cat in ("tackles", "sacks"):
                add(cat, v["player"], s["program"], s["season"], "Team leader", v["value"])
        ppg = (s.get("team") or {}).get("ppg")
        add("ppg", name(s["program"]), s["program"], s["season"], f"{s['w']}-{s['l']} season", ppg)
    # Every Vikings game
    for g in T["games"]:
        where = {"home": "home", "away": "away", "neutral": "neutral site"}[g["site"]]
        label = g["name"] or f"Week {g['week']}"
        res = "W" if g["result"] == "W" else "L"
        add("gamepts", f"vs {name(g['opponent'])}", "CLEV", g["season"], f"{label} · {where}", g["clev_score"],
            f"{res} {g['clev_score']}-{g['opp_score']}")
    return {"decks": DECKS, "cards": cards}


if __name__ == "__main__":
    data = generate(load_tables())
    from collections import Counter
    print(len(data["cards"]), "cards")
    print(Counter(c["d"] for c in data["cards"]))
    print(Counter((c["d"], c["p"]) for c in data["cards"]))
