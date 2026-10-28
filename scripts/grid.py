"""The Grid (Immaculate Grid style) player tags generated from the data tables (M8).

Every player in the three programs gets a list of condition tags, computed only from
tracker data. The page builds 3x3 grids from these tags in the browser (daily grid
seeded by date, practice grids at random) and only uses grids where every square has
enough real answers.
Usage: py -P scripts/grid.py   (prints condition sizes and a few sample grids)
"""
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trivia import load_tables, SHORT, PROGRAMS, STATES  # noqa: E402

POS = {"QB": "Quarterback", "RB": "Running back", "WR": "Wide receiver", "TE": "Tight end",
       "OL": "Offensive line", "DL": "Defensive line", "LB": "Linebacker", "DB": "Defensive back"}
ERAS = [("2024-28", 2024, 2028), ("2029-33", 2029, 2033), ("2034-37", 2034, 2037)]


def extend_last_era(latest):
    """The last era runs to the newest season in the data (so 2038 lands in "2034-38")."""
    name, a, b = ERAS[-1]
    if latest > b:
        ERAS[-1] = (f"{a}-{str(latest)[2:]}", a, latest)
HOME = ["OH", "MI", "NJ", "FL", "GA", "NY", "TX"]

CONDITIONS = (
    [{"key": f"prog:{p}", "label": SHORT[p], "cat": "program"} for p in PROGRAMS]
    + [{"key": f"pos:{k}", "label": v, "cat": "position"} for k, v in POS.items()]
    + [{"key": "hon:award", "label": "National award winner", "cat": "honor"},
       {"key": "hon:aa", "label": "All-American", "cat": "honor"},
       {"key": "hon:leader", "label": "Led his team in a stat", "cat": "honor"},
       {"key": "hon:none", "label": "Never an All-American", "cat": "honor"}]
    + [None]  # era conditions are filled in by era_conditions() once the newest season is known
    + [{"key": "rec:5", "label": "5-star recruit", "cat": "recruit"},
       {"key": "rec:4", "label": "4-star recruit", "cat": "recruit"},
       {"key": "xfer", "label": "Transferred in", "cat": "recruit"}]
    + [{"key": f"st:{s}", "label": f"From {STATES[s]}", "cat": "state"} for s in HOME]
    + [{"key": "draft:1", "label": "1st-round draft pick", "cat": "draft"},
       {"key": "draft:any", "label": "Drafted", "cat": "draft"},
       {"key": "ovr:90", "label": "Rated 90+ at peak", "cat": "rating"}]
)


def player_tags(p):
    tags = []
    prog = p.get("program")
    if prog not in PROGRAMS:
        return tags
    tags.append(f"prog:{prog}")
    if p.get("position_family") in POS:
        tags.append(f"pos:{p['position_family']}")
    aw, aa, ls = p.get("awards") or [], p.get("all_american") or [], p.get("leader_seasons") or []
    if aw:
        tags.append("hon:award")
    if aa:
        tags.append("hon:aa")
    if ls:
        tags.append("hon:leader")
    if prog == "CLEV" and not aa:
        tags.append("hon:none")  # only meaningful where full rosters are tracked
    years = set(p.get("seasons") or []) | {a["season"] for a in aw} | {a["season"] for a in aa} | {x["season"] for x in ls}
    for k, a, b in ERAS:
        if any(a <= y <= b for y in years):
            tags.append(f"era:{k}")
    rec = p.get("recruit") or {}
    if rec.get("stars") in (5, 5.0):
        tags.append("rec:5")
    if rec.get("stars") in (4, 4.0):
        tags.append("rec:4")
    if p.get("transfer"):
        tags.append("xfer")
    st = p.get("home_state") or rec.get("state")
    if st in HOME:
        tags.append(f"st:{st}")
    dep = p.get("departure") or {}
    if dep.get("drafted"):
        tags.append("draft:any")
        if dep.get("draft_round") == 1:
            tags.append("draft:1")
    if (p.get("peak_rating") or 0) >= 90:
        tags.append("ovr:90")
    return tags


def era_conditions():
    out = []
    for c in CONDITIONS:
        if c is None:
            out += [{"key": f"era:{k}", "label": f"Played in {a}-{str(b)[2:]}", "cat": "era"} for k, a, b in ERAS]
        else:
            out.append(c)
    return out


def generate(T):
    extend_last_era(max(s["season"] for s in T["seasons"]))
    players = []
    for p in T["players"]:
        tags = player_tags(p)
        if tags:
            players.append({"id": p["id"], "n": p["name"], "p": p["program"], "t": tags})
    players.sort(key=lambda x: x["n"])
    return {"conditions": era_conditions(), "players": players, "launch": "2026-10-28", "min": 2}


def make_grid(data, rng, tries=4000):
    """Python mirror of the page's grid builder, used to sanity-check the settings."""
    conds = [c["key"] for c in data["conditions"]]
    cat = {c["key"]: c["cat"] for c in data["conditions"]}
    index = {}
    for p in data["players"]:
        for t in p["t"]:
            index.setdefault(t, set()).add(p["id"])
    for _ in range(tries):
        pick = rng.sample(conds, 6)
        rows, cols = pick[:3], pick[3:]
        if len({cat[c] for c in rows}) < 2 or len({cat[c] for c in cols}) < 2:
            continue
        cells = [[index.get(r, set()) & index.get(c, set()) for c in cols] for r in rows]
        if all(len(x) >= data["min"] for row in cells for x in row):
            return rows, cols, cells
    return None


if __name__ == "__main__":
    data = generate(load_tables())
    cnt = Counter(t for p in data["players"] for t in p["t"])
    print(len(data["players"]), "players")
    for c in data["conditions"]:
        print(f"  {c['label']:<28} {cnt[c['key']]}")
    rng = random.Random(1)
    for i in range(4):
        g = make_grid(data, rng)
        if g:
            rows, cols, cells = g
            print("\nrows:", rows, "\ncols:", cols, "\n", [[len(x) for x in r] for r in cells])
