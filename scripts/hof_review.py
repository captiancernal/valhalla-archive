"""Hall of Fame selection screen (used by /update-archive).

  py -P scripts/hof_review.py                      list players awaiting a vote, with career summaries
  py -P scripts/hof_review.py decide "<name>" yes  induct (class = current season)
  py -P scripts/hof_review.py decide "<name>" no   decline (never asked again)

Run scripts/build_data.py first so eligibility is current.
"""
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEC = os.path.join(ROOT, "data", "hof-decisions.json")
T = os.path.join(ROOT, "data", "tables")


def load(name):
    with open(os.path.join(T, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def summary(p):
    lines = [f"{p['name']} ({'/'.join(p['positions'][:2])}, {', '.join(p['teams'])}, {p['seasons'][0]}-{p['seasons'][-1]})"]
    d = p["departure"]
    lines.append(f"  Left after {d['season']} as a {d['overall']} overall; "
                 + (f"drafted in round {d['draft_round']}" if d["drafted"] else d["outcome"]))
    if p.get("recruit"):
        r = p["recruit"]
        lines.append(f"  Recruit: {str(r['stars']) + '-star, ' if r.get('stars') else ''}#{r['natl_rank']} nationally, {r.get('state') or ''}")
    if p["ratings"]:
        lines.append("  Ratings: " + ", ".join(f"{k}: {v}" for k, v in sorted(p["ratings"].items())))
    lines.append("  Awards: " + ", ".join(f"{a['season']} {a['award']}" for a in sorted(p["awards"], key=lambda a: a["season"])))
    lines.append("  All-American: " + ", ".join(str(a["season"]) for a in sorted(p["all_american"], key=lambda a: a["season"])))
    for l in sorted(p["leader_seasons"], key=lambda l: l["season"]):
        lines.append(f"  Led team in {l['category']} {l['season']}: {l['value']:,}")
    for r in p["records"]:
        lines.append(f"  Record: {r['magnitude']} {r['duration'].lower()} {r['type'].lower()}, {r['value']:,}")
    return "\n".join(lines)


def main():
    hof = load("hall_of_fame")
    players = {p["name"]: p for p in load("players")}
    dec = json.load(open(DEC, encoding="utf-8"))
    if len(sys.argv) >= 4 and sys.argv[1] == "decide":
        name, vote = sys.argv[2], sys.argv[3].lower()
        if name not in {h["player"] for h in hof}:
            sys.exit(f"{name} is not on the eligible list")
        season = load("site_control")["current_season"]
        dec["decisions"][name] = {"inducted": vote in ("yes", "y"), "decided": datetime.date.today().isoformat(),
                                  "class_of": season if vote in ("yes", "y") else None}
        with open(DEC, "w", encoding="utf-8") as f:
            json.dump(dec, f, indent=2, ensure_ascii=False)
        print(f"Recorded: {name} -> {'INDUCTED, class of ' + str(season) if vote in ('yes', 'y') else 'not inducted'}")
        return
    pending = [h for h in hof if h["player"] not in dec["decisions"]]
    print(f"{len(pending)} player(s) awaiting a Hall of Fame vote\n")
    for h in pending:
        print(summary(players[h["player"]]) + "\n")


if __name__ == "__main__":
    main()
