"""Road to next season (M9): returning players and Record Watch, computed from the data.

Record Watch compares each returning Vikings player with the school, Big 12 and NCAA
season and career records (Records sheet, after fixes F24/F27/F28). Game records are
skipped because the tracker has no game-by-game player stats.
Usage: py -P scripts/road.py   (prints the Record Watch list)
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trivia import load_tables  # noqa: E402

TYPES = {  # record type -> (stats category, field)
    "Passing Yards": ("passing", "yds"), "Passing TD": ("passing", "td"),
    "Rushing Yards": ("rushing", "yds"), "Rushing TD": ("rushing", "td"),
    "Receiving Yards": ("receiving", "yds"), "Receiving TD": ("receiving", "td"),
}
MAG_ORDER = {"NCAA": 0, "Big 12": 1, "Cleveland State": 2}
# A record is "within reach" if the gap could be closed by a season like the player's best one,
# with some headroom for growth (career), or if the player's best season is already close (season).
CAREER_REACH = 1.25   # gap <= 1.25 x best season
SEASON_REACH = 0.70   # best season >= 70% of the record


def returning_players(T, cur):
    """Players on the next season's projected chart who aren't departing, plus anyone with
    current-season stats who isn't on the current departures list."""
    nxt = cur + 1
    gone = {d["player"] for d in T["departures"] if d["season"] == cur and d["program"] == "CLEV"}
    names = {d["player"] for d in T["depth_chart"] if d["season"] == nxt and not d.get("departing")}
    names |= {r["player"] for r in T["player_seasons"] if r["season"] == cur and r["program"] == "CLEV"}
    return sorted(n for n in names if n not in gone)


def record_watch(T, cur):
    names = set(returning_players(T, cur))
    ps = defaultdict(list)
    for r in T["player_seasons"]:
        if r["program"] == "CLEV" and r["player"] in names:
            ps[(r["player"], r["category"])].append(r)
    pos = {}
    for d in T["depth_chart"]:
        if d["season"] in (cur, cur + 1) and d["player"] in names:
            pos[d["player"]] = d["slot"].rstrip("123")
    out = []
    for rec in T["records_official"]:
        if rec["type"] not in TYPES or rec["duration"] not in ("Season", "Career"):
            continue
        cat, field = TYPES[rec["type"]]
        for (player, c), rows in ps.items():
            if c != cat:
                continue
            vals = [(r["season"], r.get(field) or 0) for r in rows]
            if not vals:
                continue
            best_season, best = max(vals, key=lambda x: x[1])
            last = next((v for s, v in vals if s == cur), 0)
            career = sum(v for _, v in vals)
            if best <= 0:
                continue
            if rec["duration"] == "Career":
                gap = rec["value"] - career + 1
                if gap <= 0 or gap > CAREER_REACH * best:
                    continue
                current = career
            else:
                if best < SEASON_REACH * rec["value"] or best > rec["value"]:
                    continue
                gap = rec["value"] - best + 1
                current = best
            out.append({
                "player": player, "pos": pos.get(player), "magnitude": rec["magnitude"], "duration": rec["duration"],
                "type": rec["type"], "record": rec["value"], "holder": rec["player"], "year_set": rec["year_set"],
                "current": current, "gap": gap, "last": last, "best": best, "best_season": best_season,
                "seasons": len(vals), "pct": round(min(100, current / rec["value"] * 100), 1),
            })
    # Merge rows where the school and Big 12 (or NCAA) record are the same mark.
    merged = {}
    for w in out:
        k = (w["player"], w["duration"], w["type"], w["record"], w["holder"])
        if k in merged:
            merged[k]["levels"].append(w["magnitude"])
        else:
            w["levels"] = [w["magnitude"]]
            merged[k] = w
    out = list(merged.values())
    for w in out:
        w["levels"].sort(key=lambda m: MAG_ORDER[m])
        w["magnitude"] = w["levels"][0]
    # Strongest chances first: closest, then highest level
    out.sort(key=lambda x: (-x["pct"], MAG_ORDER[x["magnitude"]]))
    return out


def chasers(T, cur):
    """For every season and career record, the returning player who is closest to it."""
    names = set(returning_players(T, cur))
    tot = defaultdict(lambda: {"career": 0, "best": 0, "best_season": None})
    for r in T["player_seasons"]:
        if r["program"] != "CLEV" or r["player"] not in names:
            continue
        for typ, (cat, field) in TYPES.items():
            if r["category"] != cat:
                continue
            v = r.get(field) or 0
            e = tot[(r["player"], typ)]
            e["career"] += v
            if v > e["best"]:
                e["best"], e["best_season"] = v, r["season"]
    rows = []
    seen = set()
    for rec in sorted(T["records_official"], key=lambda r: (r["duration"], r["type"], MAG_ORDER.get(r["magnitude"], 9))):
        if rec["type"] not in TYPES or rec["duration"] not in ("Season", "Career"):
            continue
        key = (rec["duration"], rec["type"], rec["value"], rec["player"])
        levels = [r["magnitude"] for r in T["records_official"]
                  if (r["duration"], r["type"], r["value"], r["player"]) == key]
        if key in seen:
            continue
        seen.add(key)
        fld = "career" if rec["duration"] == "Career" else "best"
        cands = [(p, e) for (p, typ), e in tot.items() if typ == rec["type"] and e[fld] > 0]
        if not cands:
            continue
        p, e = max(cands, key=lambda pe: pe[1][fld])
        rows.append({"duration": rec["duration"], "type": rec["type"], "levels": sorted(set(levels), key=lambda m: MAG_ORDER[m]),
                     "record": rec["value"], "holder": rec["player"], "year_set": rec["year_set"],
                     "player": p, "current": e[fld], "gap": max(0, rec["value"] - e[fld] + 1),
                     "pct": round(min(100, e[fld] / rec["value"] * 100), 1), "season": e["best_season"]})
    rows.sort(key=lambda r: (r["duration"] != "Season", r["type"]))
    return rows


if __name__ == "__main__":
    T = load_tables()
    cur = load_tables()["site_control"]["current_season"]
    print(len(returning_players(T, cur)), "returning players")
    for c in chasers(T, cur):
        print("CHASE", c["duration"], c["type"], c["levels"], c["record"], c["holder"], "|", c["player"], c["current"], f"{c['pct']}%")
    for w in record_watch(T, cur):
        print(f"{w['player']:<22} {'/'.join(w['levels']):<16} {w['duration']:<7} {w['type']:<16} "
              f"{w['current']:>6} / {w['record']:<6} ({w['holder']}, {w['year_set']}) needs {w['gap']}  [{w['pct']}%]  last {w['last']}")
