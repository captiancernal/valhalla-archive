"""Playerdle player pool generated from the data tables (M8).

Pool (owner decision 2026-10-28): notable players from all three programs, meaning
award winners, All-Americans and season stat leaders. Attributes the tracker doesn't
keep (common for Ohio and Miami (OH)) are left as null and shown as "not tracked".
Usage: py -P scripts/playerdle.py   (prints pool size and coverage)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trivia import load_tables, SHORT, PROGRAMS, STATES  # noqa: E402


def generate(T):
    pool = []
    for p in T["players"]:
        prog = p.get("program")
        if prog not in PROGRAMS:
            continue
        aw = p.get("awards") or []
        aa = p.get("all_american") or []
        ls = p.get("leader_seasons") or []
        if not (aw or aa or ls):
            continue
        years = set(p.get("seasons") or [])
        years |= {a["season"] for a in aw} | {a["season"] for a in aa} | {x["season"] for x in ls}
        if not years:
            continue
        rec = p.get("recruit") or {}
        honors = sorted({f"{a['season']} {a['award']}" for a in aw}) + [f"{a['season']} All-American" for a in aa]
        state = p.get("home_state") or rec.get("state")
        pool.append({
            "id": p["id"], "n": p["name"], "p": prog,
            "pos": p.get("position_family") if p.get("position_family") not in (None, "Other") else None,
            "first": min(years), "last": max(years),
            "hon": len(aw) + len(aa), "hl": honors[:6],
            "st": STATES.get(state) if state else None,
            "stars": int(rec["stars"]) if rec.get("stars") else None,
            "ovr": p.get("peak_rating"),
        })
        # Daily puzzles need enough clues to be fair: a known position or at least one honor.
        pool[-1]["daily"] = bool(prog == "CLEV" or pool[-1]["pos"] or pool[-1]["hon"])
    pool.sort(key=lambda x: x["n"])
    return {"programs": SHORT, "players": pool, "launch": "2026-10-28"}


if __name__ == "__main__":
    from collections import Counter
    d = generate(load_tables())
    ps = d["players"]
    print(len(ps), "players", Counter(p["p"] for p in ps))
    for k in ("pos", "st", "stars", "ovr"):
        print(k, Counter((p["p"], p[k] is not None) for p in ps))
