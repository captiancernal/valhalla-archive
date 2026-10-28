"""Trivia questions generated from the data tables (M8).

Every question comes from the tracker data only. Wrong answers are real values
from the same data (other players, teams, scores, seasons), never invented.

Usage:
  py -P scripts/trivia.py sample [N] [seed]   print N random questions for review
  py -P scripts/trivia.py stats               counts by category, era and difficulty
build_site.py imports generate() and writes _site/assets/data/trivia.json.
"""
import hashlib
import json
import os
import random
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "data", "tables")
PROGRAMS = ["CLEV", "OHIO", "M-OH"]
SHORT = {"CLEV": "Cleveland State", "OHIO": "Ohio", "M-OH": "Miami (OH)"}
ERAS = [("2023-27", 2023, 2027), ("2028-32", 2028, 2032), ("2033-37", 2033, 2037)]
LEADER_TEXT = {"passing": ("passing", "passing yards"), "rushing": ("rushing", "rushing yards"),
               "receiving": ("receiving", "receiving yards"), "tackles": ("tackles", "tackles"),
               "sacks": ("sacks", "sacks"), "interceptions": ("interceptions", "interceptions")}
MAJOR_AWARDS = ["Heisman", "Maxwell", "Camp", "O'Brien", "Walker", "Biletnikoff"]
AWARD_NAMES = {"Camp": "Walter Camp", "Walker": "Doak Walker", "O'Brien": "Davey O'Brien",
               "Bednarik": "Chuck Bednarik", "Nagurski": "Bronko Nagurski", "Butkus": "Dick Butkus",
               "Thorpe": "Jim Thorpe", "Groza": "Lou Groza", "Guy": "Ray Guy", "Mackey": "John Mackey",
               "Lombardi": "Lombardi", "Outland": "Outland", "Rimington": "Rimington", "Heisman": "Heisman",
               "Maxwell": "Maxwell", "Biletnikoff": "Biletnikoff"}
STATES = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
          "CT": "Connecticut", "DE": "Delaware", "DC": "Washington, D.C.", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
          "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
          "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
          "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
          "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
          "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
          "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
          "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"}
ROUND_ORDER = {"First Round": 1, "Quarterfinal": 2, "Semifinal": 3, "National Championship": 4}


def era_of(year):
    for name, a, b in ERAS:
        if a <= year <= b:
            return name
    return ERAS[-1][0]


def fmt(n):
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    return f"{n:,}" if isinstance(n, int) else str(n)


class Gen:
    def __init__(self, T):
        self.T = T
        self.teams = {t["id"]: t for t in T["teams"]}
        self.out = []
        self.seen = set()

    def name(self, abbr):
        if abbr in SHORT:
            return SHORT[abbr]
        return (self.teams.get(abbr) or {}).get("school") or abbr

    def add(self, key, cat, season, diff, q, correct, pool, why, topic):
        """pool: other real values from the data to use as wrong answers."""
        correct = str(correct)
        wrong = []
        for v in pool:
            v = str(v)
            if v != correct and v not in wrong:
                wrong.append(v)
        if len(wrong) < 3:
            return
        qid = hashlib.md5(key.encode()).hexdigest()[:10]
        if qid in self.seen:
            return
        self.seen.add(qid)
        rng = random.Random(qid)
        picks = rng.sample(wrong, 3)
        choices = picks + [correct]
        rng.shuffle(choices)
        self.out.append({"id": qid, "cat": cat, "era": era_of(season) if season else "all", "season": season,
                         "diff": diff, "topic": topic, "q": q, "choices": choices,
                         "answer": choices.index(correct), "why": why})

    # ------------------------------------------------------------ generators
    def national_champions(self):
        T = self.T
        po_teams = defaultdict(set)
        for p in T["playoffs"]:
            po_teams[p["season"]].update([p["team_a"], p["team_b"]])
        ap = defaultdict(list)
        for r in sorted(T["ap_top25"], key=lambda r: r["rank"]):
            ap[r["season"]].append(r["team"])
        for n in T["national_championships"]:
            y, c, ru = n["season"], n["champion"], n["runner_up"]
            pool = [self.name(t) for t in (sorted(po_teams[y]) + ap[y][:10]) if t not in (c,)]
            cat = c if c in PROGRAMS else "LEAGUE"
            diff = 1 if c in PROGRAMS or ru in PROGRAMS else 2
            self.add(f"natl:{y}", cat, y, diff, f"Who won the {y} national championship?", self.name(c), pool,
                     f"{self.name(c)} beat {self.name(ru)} {n['score']} in the title game.", "Champions")
            if ru in PROGRAMS or c in PROGRAMS:
                self.add(f"natl-ru:{y}", ru if ru in PROGRAMS else cat, y, 2,
                         f"Who lost the {y} national championship game to {self.name(c)}?", self.name(ru),
                         [self.name(t) for t in sorted(po_teams[y]) if t not in (c, ru)] + [self.name(t) for t in ap[y][:8] if t not in (c, ru)],
                         f"{self.name(c)} won it {n['score']} over {self.name(ru)}.", "Champions")

    def big12(self):
        T = self.T
        b12 = defaultdict(list)
        for s in T["standings"]:
            if s["conference"] == "Big 12":
                b12[s["season"]].append(s["team"])
        for c in T["conference_championships"]:
            if c["conference"] != "Big 12":
                continue
            y, w, l = c["season"], c["champion"], c["runner_up"]
            pool = [self.name(t) for t in b12[y] + PROGRAMS + ["KSU", "OKST", "UTAH", "TCU", "BYU"] if t != w]
            cat = w if w in PROGRAMS else ("LEAGUE" if l not in PROGRAMS else l)
            self.add(f"b12:{y}", cat, y, 1 if w in PROGRAMS else 2, f"Who won the {y} Big 12 Championship Game?",
                     self.name(w), pool, f"{self.name(w)} beat {self.name(l)} {c['champion_score']}-{c['runner_up_score']}.", "Champions")

    def other_conferences(self):
        """League questions: every other conference's title game, from the Conference Champions sheet."""
        T = self.T
        conf_teams = defaultdict(set)
        for s in T["standings"]:
            conf_teams[(s["season"], s["conference"])].add(s["team"])
        by_conf = defaultdict(set)
        for c in T["conference_championships"]:
            by_conf[c["conference"]].update([c["champion"], c["runner_up"]])
        for c in T["conference_championships"]:
            if c["conference"] == "Big 12" or not c["champion"] or not c["runner_up"]:
                continue
            y, conf, w, l = c["season"], c["conference"], c["champion"], c["runner_up"]
            pool = [self.name(t) for t in sorted(conf_teams[(y, conf)] | by_conf[conf]) if t != w]
            score = f"{c['champion_score']}-{c['runner_up_score']}" if c.get("champion_score") is not None else ""
            self.add(f"conf:{conf}:{y}", "LEAGUE", y, 3, f"Who won the {y} {conf} championship?", self.name(w), pool,
                     f"{self.name(w)} beat {self.name(l)}{(' ' + score) if score else ''} for the {conf} title.", "Conferences")

    def awards(self):
        T = self.T
        by_year = defaultdict(list)
        for a in T["awards"]:
            by_year[a["season"]].append(a)
        for y, rows in by_year.items():
            names = [r["player"] for r in rows]
            for a in rows:
                ours = a["school"] in PROGRAMS
                if not ours and a["award"] not in MAJOR_AWARDS:
                    continue
                full = AWARD_NAMES.get(a["award"], a["award"])
                label = f"{full} Trophy" if a["award"] == "Heisman" else f"{full} Award"
                n0 = a.get("award_note") or ""
                note = f" ({n0[0].lower() + n0[1:]})" if n0 and a["award"] != "Heisman" else ""
                diff = 1 if a["award"] == "Heisman" and ours else (2 if ours or a["award"] in ("Heisman", "Maxwell") else 3)
                other_years = [r["player"] for yy, rr in by_year.items() if abs(yy - y) <= 2 for r in rr if r["award"] == a["award"]]
                self.add(f"award:{y}:{a['award']}", a["school"] if ours else "LEAGUE", y, diff,
                         f"Who won the {y} {label}{note}?", a["player"], names + other_years,
                         f"{a['player']} of {self.name(a['school'])} won the {y} {label}.", "Awards")
                if ours and a["award"] in ("Heisman", "Biletnikoff", "Walker", "Mackey", "Outland", "Butkus", "Thorpe", "Nagurski", "Bednarik", "Lombardi", "Rimington", "O'Brien"):
                    self.add(f"award-school:{y}:{a['award']}", a["school"], y, 2,
                             f"{a['player']} won the {y} {label}. Which program did he play for?", self.name(a["school"]),
                             [SHORT[p] for p in PROGRAMS] + [self.name(r["school"]) for r in rows],
                             f"{a['player']} played for {self.name(a['school'])}.", "Awards")

    def leaders(self):
        T = self.T
        by_prog_cat = defaultdict(list)
        for s in T["seasons"]:
            for cat, v in (s.get("leaders") or {}).items():
                if v and v.get("player"):
                    by_prog_cat[(s["program"], cat)].append((s["season"], v))
        for (pid, cat), rows in by_prog_cat.items():
            names = [v["player"] for _, v in rows]
            for y, v in rows:
                word, unit = LEADER_TEXT[cat]
                same_year = [vv["player"] for s in T["seasons"] if s["program"] == pid and s["season"] == y
                             for vv in (s.get("leaders") or {}).values() if vv]
                others = [n for n in names if n != v["player"]]
                self.add(f"leader:{pid}:{y}:{cat}", pid, y, 2, f"Who led {SHORT[pid]} in {word} in {y}?", v["player"],
                         others if len(set(others)) >= 3 else others + same_year,
                         f"{v['player']} led {SHORT[pid]} with {fmt(v['value'])} {unit}.", "Stat leaders")
                if cat in ("passing", "rushing", "receiving") and isinstance(v["value"], (int, float)):
                    vals = [fmt(vv["value"]) for _, vv in rows if vv["value"] != v["value"]]
                    self.add(f"leaderval:{pid}:{y}:{cat}", pid, y, 3,
                             f"{v['player']} led {SHORT[pid]} in {word} in {y}. How many {unit}?", fmt(v["value"]), vals,
                             f"{v['player']} had {fmt(v['value'])} {unit} for {SHORT[pid]} in {y}.", "Stat leaders")

    def records(self):
        T = self.T
        seasons = [s for s in T["seasons"] if s["program"] in PROGRAMS]
        by_prog = defaultdict(list)
        for s in seasons:
            by_prog[s["program"]].append(s)
        for pid, rows in by_prog.items():
            recs = [f"{s['w']}-{s['l']}" for s in rows]
            for s in rows:
                extra = ""
                if s.get("national_champion"):
                    extra = ", national champions"
                elif s.get("national_runner_up"):
                    extra = ", national runner-up"
                elif s.get("conference_champion"):
                    extra = ", Big 12 champions"
                elif s.get("bowl"):
                    b = s["bowl"]
                    extra = f", {'won' if b['result'] == 'W' else 'lost'} the {b['name']}"
                self.add(f"record:{pid}:{s['season']}", pid, s["season"], 2,
                         f"What was {SHORT[pid]}'s record in {s['season']}?", f"{s['w']}-{s['l']}", recs,
                         f"{SHORT[pid]} went {s['w']}-{s['l']} in {s['season']}{extra}.", "Seasons")
                if s.get("ap_final_rank"):
                    r = s["ap_final_rank"]
                    pool = [f"No. {x}" for x in range(max(1, r - 4), r + 6)]
                    self.add(f"ap:{pid}:{s['season']}", pid, s["season"], 3,
                             f"Where did {SHORT[pid]} finish in the final {s['season']} AP poll?", f"No. {r}", pool,
                             f"{SHORT[pid]} finished No. {r} in the final {s['season']} AP Top 25.", "Seasons")

    def clev_games(self):
        T = self.T
        games = T["games"]
        def line(g):
            opp = self.name(g["opponent"])
            if g["result"] == "W":
                return f"Cleveland State won {g['clev_score']}-{g['opp_score']}"
            return f"{opp} won {g['opp_score']}-{g['clev_score']}"
        for g in games:
            big = g["opponent"] in ("OHIO", "M-OH") or g["kind"] in ("playoff", "conference_championship")
            if not big:
                continue
            same_opp = [line(x) for x in games if x["opponent"] == g["opponent"] and x["id"] != g["id"]]
            same_kind = [line(x) for x in games if x["kind"] == g["kind"] and x["id"] != g["id"] and x["season"] == g["season"]]
            pool = same_opp + same_kind + [line(x) for x in games if x["season"] == g["season"] and x["id"] != g["id"]]
            where = {"home": "in Cleveland", "away": "on the road", "neutral": "at a neutral site"}[g["site"]]
            label = g["name"] or "regular season"
            self.add(f"game:{g['id']}", "CLEV", g["season"], 3,
                     f"{g['season']} {label}: Cleveland State vs {self.name(g['opponent'])} {where}. What was the result?",
                     line(g), pool, f"{line(g)}.", "Games")
            if g["kind"] == "playoff" and g["result"] == "W":
                opp_pool = [self.name(p["team_a"]) for p in T["playoffs"] if p["season"] == g["season"]] + \
                           [self.name(p["team_b"]) for p in T["playoffs"] if p["season"] == g["season"]]
                self.add(f"po:{g['id']}", "CLEV", g["season"], 2,
                         f"Who did Cleveland State beat in the {g['season']} CFP {g['name'].replace('CFP ', '')}?",
                         self.name(g["opponent"]), [o for o in opp_pool if o != "Cleveland State"],
                         f"Cleveland State beat {self.name(g['opponent'])} {g['clev_score']}-{g['opp_score']}.", "Games")

    def series(self):
        T = self.T
        for opp in ("OHIO", "M-OH"):
            gs = [g for g in T["games"] if g["opponent"] == opp]
            w = sum(1 for g in gs if g["result"] == "W")
            l = len(gs) - w
            pool = [f"{a}-{b}" for a in range(w - 3, w + 4) for b in range(l - 2, l + 3) if (a, b) != (w, l) and a >= 0 and b >= 0]
            self.add(f"series:{opp}", "CLEV", None, 3,
                     f"What is Cleveland State's all-time record against {SHORT[opp]} (2024-{max(g['season'] for g in gs)}), playoffs included?",
                     f"{w}-{l}", pool, f"Cleveland State is {w}-{l} against {SHORT[opp]} across {len(gs)} meetings.", "Rivalry")
        for p in T["programs"]:
            titles = p.get("national_titles") or []
            if titles:
                self.add(f"titles:{p['id']}", p["id"], None, 1,
                         f"How many national championships did {SHORT[p['id']]} win from 2024 to 2037?",
                         str(len(titles)), [str(n) for n in range(0, 7)],
                         f"{SHORT[p['id']]} won {len(titles)}: {', '.join(map(str, titles))}.", "Champions")
            self.add(f"coach:{p['id']}", p["id"], None, 1, f"Who is the head coach of {SHORT[p['id']]}?", p["coach"],
                     [q["coach"] for q in T["programs"]] + ["Kirk Ferentz", "Dabo Swinney"],
                     f"Coach {p['coach']} has led {SHORT[p['id']]} for the whole dynasty.", "Coaches")

    def records_book(self):
        T = self.T
        recs = T["records_official"]
        holders = [r["player"] for r in recs]
        for b in T["records_computed"]:  # other real Vikings stat leaders as wrong answers
            holders += [x["player"] for x in b["leaders"][:5]]
        for r in recs:
            mag = {"Cleveland State": "Cleveland State", "Big 12": "Big 12", "NCAA": "NCAA"}[r["magnitude"]]
            self.add(f"rb:{mag}:{r['duration']}:{r['type']}", "CLEV", None, 2,
                     f"Who holds the {mag} {r['duration'].lower()} record for {r['type'].lower()}?",
                     r["player"], holders, f"{r['player']}: {fmt(r['value'])} ({r['year_set']}).", "Records")

    def roster(self):
        T = self.T
        drafted = [d for d in T["departures"] if d["program"] == "CLEV" and d["drafted"]]
        for d in drafted:
            pool = [f"Round {n}" for n in range(1, 8)]
            self.add(f"draft:{d['season']}:{d['player']}", "CLEV", d["season"], 3,
                     f"In which round of the draft was {d['player']} ({d['position']}) picked after the {d['season']} season?",
                     f"Round {d['draft_round']}", pool, f"{d['player']} went in round {d['draft_round']}.", "Draft")
        froms = [self.name(t["from"]) for t in T["transfers"] if t["to"] == "CLEV"]
        for t in T["transfers"]:
            if t["to"] != "CLEV":
                continue
            self.add(f"xfer:{t['arrival_season']}:{t['player']}", "CLEV", t["arrival_season"], 3,
                     f"{t['player']} ({t['position']}) transferred to Cleveland State in {t['arrival_season']}. From which school?",
                     self.name(t["from"]), froms, f"{t['player']} came from {self.name(t['from'])}.", "Transfers")
        top = [r for r in T["recruits"] if r["natl_rank"] and r["natl_rank"] <= 60 and r["state"] in STATES]
        states = sorted({STATES[r["state"]] for r in T["recruits"] if r["state"] in STATES})
        for r in top:
            self.add(f"recruit:{r['cycle']}:{r['player']}", "CLEV", r["arrival_season"], 3,
                     f"Cleveland State signed {r['player']}, the No. {r['natl_rank']} recruit in the country, for {r['arrival_season']}. What was his home state?",
                     STATES[r["state"]], states, f"{r['player']} came from {STATES[r['state']]}" + (f" as a {int(r['stars'])}-star {r['position']}." if r.get("stars") else "."), "Recruiting")

    def milestones(self):
        """Easy questions about the dynasty's big storylines, all computed from the data."""
        T = self.T
        champs = sorted(T["national_championships"], key=lambda n: n["season"])
        all_names = [SHORT[p] for p in PROGRAMS] + [self.name(n["champion"]) for n in champs]
        i = 0
        while i < len(champs):
            j = i
            while j + 1 < len(champs) and champs[j + 1]["champion"] == champs[i]["champion"]:
                j += 1
            run = j - i + 1
            c = champs[i]["champion"]
            if run >= 2 and c in PROGRAMS:
                a, b = champs[i]["season"], champs[j]["season"]
                self.add(f"streak:{c}:{a}", c, a, 1, f"Which program won {run} straight national championships from {a} to {b}?",
                         SHORT[c], all_names, f"{SHORT[c]} won every title from {a} through {b}.", "Champions")
            i = j + 1
        for p in T["programs"]:
            for y in p.get("national_titles") or []:
                n = next(x for x in champs if x["season"] == y)
                self.add(f"titleopp:{p['id']}:{y}", p["id"], y, 1,
                         f"{SHORT[p['id']]} won the {y} national championship. Who did they beat in the title game?",
                         self.name(n["runner_up"]),
                         [self.name(x["runner_up"]) for x in champs] + [self.name(x["champion"]) for x in champs],
                         f"{SHORT[p['id']]} beat {self.name(n['runner_up'])} {n['score']}.", "Champions")
            b12 = p.get("big12_titles") or []
            if b12:
                self.add(f"firstb12:{p['id']}", p["id"], b12[0], 1, f"In what year did {SHORT[p['id']]} win its first Big 12 title of the dynasty?",
                         str(b12[0]), [str(y) for y in range(2024, 2038)], f"{SHORT[p['id']]}'s first Big 12 title came in {b12[0]}.", "Champions")
        heis = defaultdict(int)
        for a in T["awards"]:
            if a["award"] == "Heisman" and a["school"] in PROGRAMS:
                heis[a["school"]] += 1
        for pid, n in heis.items():
            self.add(f"heiscount:{pid}", pid, None, 1, f"How many Heisman Trophy winners has {SHORT[pid]} had since 2024?",
                     str(n), [str(k) for k in range(0, 8)], f"{SHORT[pid]} has had {n}.", "Awards")

    def run(self):
        self.milestones()
        self.national_champions()
        self.big12()
        self.other_conferences()
        self.awards()
        self.leaders()
        self.records()
        self.clev_games()
        self.series()
        self.records_book()
        self.roster()
        return self.out


def load_tables():
    T = {}
    for fn in os.listdir(TABLES):
        if fn.endswith(".json") and not fn.startswith("_"):
            with open(os.path.join(TABLES, fn), encoding="utf-8") as f:
                T[fn[:-5]] = json.load(f)
    return T


def generate(T):
    return Gen(T).run()


if __name__ == "__main__":
    qs = generate(load_tables())
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "stats":
        print(len(qs), "questions")
        print("by category:", Counter(q["cat"] for q in qs))
        print("by era:", Counter(q["era"] for q in qs))
        print("by difficulty:", Counter(q["diff"] for q in qs))
        print("by topic:", Counter(q["topic"] for q in qs))
    else:
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
        rng = random.Random(seed)
        for i, q in enumerate(rng.sample(qs, n), 1):
            print(f"{i}. [{q['cat']} · {q['era']} · {'easy medium hard'.split()[q['diff']-1]} · {q['topic']}] {q['q']}")
            for j, c in enumerate(q["choices"]):
                print(f"   {'*' if j == q['answer'] else ' '} {c}")
            print(f"   -> {q['why']}")
