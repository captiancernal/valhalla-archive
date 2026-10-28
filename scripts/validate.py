"""Spot-check the built Site Database against known facts and internal consistency.

Usage: py -P scripts/validate.py      (exit code 1 if any check fails)
Writes data/validation-report.md.
"""
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, "data", "tables")


def load(name):
    with open(os.path.join(T, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


results = []


def check(label, ok, detail=""):
    results.append((bool(ok), label, detail))


programs = {p["id"]: p for p in load("programs")}
seasons = load("seasons")
games = load("games")
natl = {n["season"]: n for n in load("national_championships")}
ccg = load("conference_championships")
standings = load("standings")
pseasons = load("player_seasons")
players = load("players")
classes = load("recruiting_classes")
aliases = json.load(open(os.path.join(ROOT, "data", "aliases.json"), encoding="utf-8"))
teams = {t["id"]: t for t in load("teams")}

# --- Owner-confirmed facts (spot checks)
for pid, rec in {"CLEV": (180, 29), "OHIO": (175, 34), "M-OH": (174, 32)}.items():
    c = programs[pid]["career"]
    check(f"{pid} career record {rec[0]}-{rec[1]}", (c["w"], c["l"]) == rec, f"got {c['w']}-{c['l']}")
check("CLEV national titles 2028, 2037", programs["CLEV"]["national_titles"] == [2028, 2037], programs["CLEV"]["national_titles"])
check("OHIO national titles 2029-33", programs["OHIO"]["national_titles"] == [2029, 2030, 2031, 2032, 2033], programs["OHIO"]["national_titles"])
check("M-OH national titles 2034-36", programs["M-OH"]["national_titles"] == [2034, 2035, 2036], programs["M-OH"]["national_titles"])
s = {(x["program"], x["season"]): x for x in seasons}
check("CLEV 2037 is 16-1", (s[("CLEV", 2037)]["w"], s[("CLEV", 2037)]["l"]) == (16, 1))
check("CLEV 2034 is 15-2 (F02)", (s[("CLEV", 2034)]["w"], s[("CLEV", 2034)]["l"]) == (15, 2))
nc37 = [g for g in games if g["season"] == 2037 and g["name"] == "National Championship"]
check("2037 title game CLEV 56-39 OHIO (F05)", nc37 and (nc37[0]["clev_score"], nc37[0]["opp_score"], nc37[0]["opponent"]) == (56, 39, "OHIO"), nc37)
lsu = [g for g in games if g["season"] == 2036 and g["opponent"] == "LSU"]
check("2036 playoff vs LSU 37-3 (F05)", lsu and (lsu[0]["clev_score"], lsu[0]["opp_score"]) == (37, 3), lsu)
check("2027 national champion BAMA (F05)", natl[2027]["champion"] == "BAMA", natl[2027])
b12_29 = [c for c in ccg if c["season"] == 2029 and c["conference"] == "Big 12"]
check("2029 Big 12 champion M-OH (F03)", b12_29 and b12_29[0]["champion"] == "M-OH", b12_29)
mac34 = [x["team"] for x in standings if x["season"] == 2034 and x["conference"] == "MAC" and x["place"] == 2]
check("2034 MAC #2 is EMU (F16)", mac34 == ["EMU"], mac34)
rec32 = max((p for p in pseasons if p["season"] == 2032 and p["category"] == "receiving"), key=lambda p: p["yds"] or 0)
check("2032 receiving leader Dakota McNitt 1853 (F04)", (rec32["player"], rec32["yds"]) == ("Dakota McNitt", 1853), rec32["player"])
c25 = next(c for c in classes if c["program"] == "CLEV" and c["cycle"] == 2025)
check("CLEV 2025 class stars 2/6/11 from list (F13)", [c25["stars"][k] for k in "543"] == [2, 6, 11], c25["stars"])
c26 = next(c for c in classes if c["program"] == "CLEV" and c["cycle"] == 2026)
check("CLEV 2026 stars not tracked (F14)", c26["stars"] is None)

aa = load("all_americans")
og = [a["school"] for a in aa if a["player"] == "Ollie Gordon III" and a["season"] == 2023]
check("2023 Ollie Gordon III All-American at OKST (F23)", og == ["OKST"], og)
ro = {(r["player"], r["duration"], r["type"]): r["value"] for r in load("records_official") if r["magnitude"] == "Cleveland State"}
f24 = [ro.get(("Baraka Nwangwu", "Career", "Rushing Yards")), ro.get(("Kenny Tongues", "Career", "Receiving Yards")),
       ro.get(("Kenny Tongues", "Career", "Receiving TD"))]
check("career rushing record is full total 6074 (F24)", f24[0] == 6074, f24)
cb = {}
for b in load("records_computed"):
    cb[(b["scope"].title(), b["label"])] = b["leaders"][0]["value"]
stale = [(k, v) for k, v in ro.items() if k[1] in ("Season", "Career") and cb.get((k[1], k[2])) not in (None, v)]
check("school season/career records match the stats-tab bests (F24, F27)", not stale, stale)
rec29 = {r["player"]: r["rec"] for r in pseasons if r["season"] == 2029 and r["category"] == "receiving"}
f25 = [rec29.get(p) for p in ("Dakota McNitt", "Stephen Everett", "Nazir McNitt", "Isaiah Boutte", "Baraka Nwangwu")]
check("2029 catch counts 56/52/48/38/42 (F25)", f25 == [56, 52, 48, 38, 42], f25)
check("2029 Big 12 rank CLEV 3rd, OHIO 2nd (F26)",
      (s[("CLEV", 2029)]["conf_rank"], s[("OHIO", 2029)]["conf_rank"]) == (3, 2),
      (s[("CLEV", 2029)]["conf_rank"], s[("OHIO", 2029)]["conf_rank"]))

# --- Internal consistency
by = defaultdict(lambda: [0, 0])
for g in games:
    by[g["season"]][0 if g["result"] == "W" else 1] += 1
for (prog, yr), x in s.items():
    if prog == "CLEV":
        check(f"CLEV {yr} games add up to coach-sheet record", tuple(by[yr]) == (x["w"], x["l"]), f"games {by[yr]} vs {x['w']}-{x['l']}")
for yr in sorted({x["season"] for x in pseasons}):
    lead = s[("CLEV", yr)]["leaders"]
    for cat in ("passing", "rushing", "receiving"):
        top = max((p for p in pseasons if p["season"] == yr and p["category"] == cat), key=lambda p: p["yds"] or 0)
        e = lead.get(cat, {})
        check(f"CLEV {yr} {cat} leader matches stats tab", (e.get("player"), e.get("value")) == (top["player"], top["yds"]),
              f"coach sheet {e.get('player')} {e.get('value')} vs stats {top['player']} {top['yds']}")
pids = {p["name"] for p in players}
missing = sorted({p["player"] for p in pseasons} - pids)
check("every stat line links to a player", not missing, missing[:5])
bad = [p["name"] for p in players if re.search(r"\d", p["name"]) or len(p["name"].split()) < 2]
check("no malformed player names", not bad, bad[:10])
variants = {v for vs in aliases["players"].values() for v in vs}
blob = json.dumps([load(n) for n in ("players", "player_seasons", "seasons", "awards", "all_americans", "depth_chart", "recruits", "departures", "transfers", "records_official")])
leaked = sorted(v for v in variants if f'"{v}"' in blob)
check("no non-canonical name spellings remain", not leaked, leaked[:10])
used = {g["opponent"] for g in games}
unnamed = sorted(t for t in used if not (teams.get(t) or {}).get("school"))
check("every CLEV opponent has a school name", not unnamed, unnamed)

fails = [r for r in results if not r[0]]
with open(os.path.join(ROOT, "data", "validation-report.md"), "w", encoding="utf-8") as f:
    f.write(f"# Validation report\n\n{len(results) - len(fails)} passed, {len(fails)} failed.\n\n")
    for ok, label, detail in results:
        f.write(f"- {'PASS' if ok else 'FAIL'}: {label}" + (f"  ({detail})" if not ok and detail else "") + "\n")
print(f"{len(results) - len(fails)} passed, {len(fails)} failed")
for ok, label, detail in fails:
    print(" FAIL:", label, detail)
sys.exit(1 if fails else 0)
