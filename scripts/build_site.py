"""Render the static website from data/tables/*.json and site/templates into _site/.

Usage:
  py -P scripts/build_site.py                                # local build, links start at "/"
  BASE_PATH=/valhalla-archive/ py -P scripts/build_site.py   # GitHub Pages build
"""
import datetime
import json
import os
import re
import shutil
import unicodedata
from collections import Counter, defaultdict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
import markdown as md_lib
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import columns as sd_columns  # noqa: E402
import trivia as trivia_gen  # noqa: E402
import higher_lower as hl_gen  # noqa: E402
import playerdle as pd_gen  # noqa: E402
import grid as grid_gen  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "data", "tables")
SRC = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "_site")
BASE = os.environ.get("BASE_PATH", "/")
if not BASE.endswith("/"):
    BASE += "/"

PROGRAMS = ["CLEV", "OHIO", "M-OH"]
PROGRAM_SLUGS = {"CLEV": "cleveland-state", "OHIO": "ohio", "M-OH": "miami-oh"}
SHORT = {"CLEV": "Cleveland State", "OHIO": "Ohio", "M-OH": "Miami (OH)"}
LEADER_LABELS = {"passing": "Passing", "rushing": "Rushing", "receiving": "Receiving", "tackles": "Tackles",
                 "sacks": "Sacks", "interceptions": "Interceptions"}
LEADER_UNITS = {"passing": "yds", "rushing": "yds", "receiving": "yds", "tackles": "tkl", "sacks": "sk", "interceptions": "int"}
DEPTH_UNITS = [
    ("Offense", ["QB", "RB", "FB", "WR", "TE", "LT", "LG", "C", "RG", "RT"]),
    ("Defense", ["LE", "DT", "RE", "LOLB", "MLB", "ROLB", "CB1", "CB2", "CB3", "FS", "SS"]),
    ("Special teams", ["K", "P"]),
]


def load(name):
    with open(os.path.join(TABLES, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def year_ranges(years):
    years = sorted(set(years))
    out, start = [], None
    for i, y in enumerate(years):
        if start is None:
            start = y
        if i == len(years) - 1 or years[i + 1] != y + 1:
            out.append(str(start) if start == y else f"{start}-{y}")
            start = None
    return ", ".join(out)


def fmt(n, d=0):
    if n is None or n == "":
        return ""
    if isinstance(n, float) and d:
        return f"{n:,.{d}f}"
    if isinstance(n, float) and n.is_integer():
        n = int(n)
    return f"{n:,}" if isinstance(n, int) else f"{n:,.1f}" if isinstance(n, float) else str(n)


def ordinal(n):
    if n is None:
        return ""
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


class Site:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(os.path.join(SRC, "templates")),
                               autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
        T = {n: load(n) for n in ["site_control", "programs", "seasons", "games", "playoffs", "conference_championships",
                                   "national_championships", "standings", "ap_top25", "player_seasons", "players",
                                   "recruits", "recruiting_classes", "transfers", "departures", "depth_chart", "awards",
                                   "all_americans", "records_official", "records_computed", "teams", "coaches", "hall_of_fame", "columns"]}
        self.T = T
        self.site = T["site_control"]
        self.build_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        updated = datetime.date.fromisoformat(self.site["last_updated"])
        self.site["last_updated_display"] = f"{updated:%B} {updated.day}, {updated.year}"
        self.teams = {t["id"]: t for t in T["teams"]}
        self.players = {p["id"]: p for p in T["players"]}
        self.player_by_name = {p["name"]: p for p in T["players"]}

        self.programs = []
        for p in T["programs"]:
            p = dict(p)
            p["slug"] = PROGRAM_SLUGS[p["id"]]
            p["href"] = f"programs/{p['slug']}/"
            p["short"] = SHORT[p["id"]]
            p["win_pct_text"] = f"{p['career']['win_pct']:.3f}".lstrip("0")
            titles = p["national_titles"]
            p["tagline"] = f"National champions {year_ranges(titles)}" if titles else f"{p['career']['w']}-{p['career']['l']} since {p['first_season']}"
            self.programs.append(p)
        self.prog = {p["id"]: p for p in self.programs}

        self.nav = [{"key": "home", "label": "Home", "href": "", "footer": True}, {"sep": True}]
        for p in self.programs:
            self.nav.append({"key": p["id"], "label": p["short"], "href": p["href"], "logo": p["logo"]})
        self.nav += [{"sep": True},
                     {"key": "split", "label": "Split Decision", "href": "split-decision/", "footer": True},
                     {"key": "players", "label": "Players", "href": "players/", "footer": True},
                     {"key": "almanac", "label": "Almanac", "href": "almanac/", "footer": True},
                     {"key": "records", "label": "Records", "href": "records/", "footer": True},
                     {"key": "rivalry", "label": "Rivalry", "href": "rivalry/", "footer": True},
                     {"key": "hof", "label": "Hall of Fame", "href": "hall-of-fame/", "footer": True},
                     {"key": "play", "label": "Games", "href": "play/", "footer": True}]

        cur = self.site["current_season"]
        champ = next((n for n in T["national_championships"] if n["season"] == cur), None)
        self.banner = None
        if champ and champ["champion"] in self.prog:
            cp = self.prog[champ["champion"]]
            rec = self.season(cp["id"], cur)
            self.banner = {"text": f"{cur} National Champions: {cp['school']} {cp['nickname']}, {rec['w']}-{rec['l']}",
                           "href": f"{cp['href']}{cur}/", "logo": cp["logo"]}

        # Jinja helpers
        g = self.env.globals
        g.update(team=self.team_html, plink=self.player_link, fmt=fmt, ordinal=ordinal, stars=self.stars_html,
                 season_href=self.season_href, game_href=lambda gid: f"{BASE}games/{gid}/", LEADER_LABELS=LEADER_LABELS,
                 LEADER_UNITS=LEADER_UNITS, year_ranges=year_ranges)
        self.pages = 0

    # ---------------------------------------------------------------- helpers
    def season(self, prog, year):
        return next((s for s in self.T["seasons"] if s["program"] == prog and s["season"] == year), None)

    def season_href(self, prog, year):
        if prog in self.prog and self.season(prog, year):
            return f"{BASE}{self.prog[prog]['href']}{year}/"
        return None

    def team_html(self, abbr, logo=True, link=True, short=False):
        if not abbr:
            return ""
        t = self.teams.get(abbr, {})
        name = SHORT.get(abbr) if short and abbr in SHORT else (t.get("school") or abbr)
        img = f'<img class="tlogo" src="{BASE}{t["logo"]}" alt="" loading="lazy" width="20" height="20">' if logo and t.get("logo") else ""
        inner = f'{img}<span>{escape(name)}</span>'
        if link and abbr in self.prog:
            return Markup(f'<a class="team" href="{BASE}{self.prog[abbr]["href"]}">{inner}</a>')
        return Markup(f'<span class="team">{inner}</span>')

    def player_link(self, name, label=None):
        if not name:
            return ""
        p = self.player_by_name.get(name)
        text = escape(label or name)
        if p:
            return Markup(f'<a href="{BASE}players/{p["id"]}/">{text}</a>')
        return Markup(text)

    def stars_html(self, n):
        if n is None:
            return Markup('<span class="muted" title="Not tracked">n/t</span>')
        n = int(n)
        return Markup(f'<span class="stars" aria-label="{n}-star" title="{n}-star">{"★" * n}<span class="dim">{"★" * (5 - n)}</span></span>')

    def postseason_text(self, s):
        if s["national_champion"]:
            return ""
        po = s.get("playoff")
        if po:
            return "Lost National Championship" if s["national_runner_up"] else f"Lost in CFP {po['exit_round']}"
        bowl = s.get("bowl")
        if bowl:
            return f"{'Won' if bowl['result'] == 'W' else 'Lost'} {bowl['name']}"
        return ""

    def render(self, template, path, **ctx):
        base_ctx = {"base": BASE, "site": self.site, "programs": self.programs, "nav": self.nav, "banner": self.banner,
                    "build_id": self.build_id, "program": None, "description": "", "theme_color": None}
        base_ctx.update(ctx)
        html = self.env.get_template(template).render(**base_ctx)
        dest = os.path.join(OUT, path, "index.html")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(html)
        self.pages += 1

    # ---------------------------------------------------------------- program sections
    def program_tabs(self, p):
        pid = p["id"]
        tabs = [("overview", "Overview", ""), ("seasons", "Seasons", "seasons/"), ("leaders", "Leaders", "leaders/")]
        if pid == "CLEV":
            tabs += [("records", "Records", "records/"), ("recruiting", "Recruiting", "recruiting/"),
                     ("departures", "Draft & Departures", "departures/"), ("transfers", "Transfers", "transfers/")]
        tabs += [("honors", "Honors", "honors/"), ("titles", "Titles & Postseason", "titles/")]
        return [{"key": k, "label": l, "href": f"{p['href']}{h}"} for k, l, h in tabs]

    def program_seasons(self, pid):
        out = []
        for s in sorted((dict(x) for x in self.T["seasons"] if x["program"] == pid), key=lambda x: -x["season"]):
            s["postseason_text"] = self.postseason_text(s)
            s["href"] = self.season_href(pid, s["season"])
            out.append(s)
        return out

    def build_program(self, p):
        pid = p["id"]
        tabs = self.program_tabs(p)
        seasons = self.program_seasons(pid)
        common = dict(program=p, program_tabs=tabs, active_nav=pid, theme_color=p["colors"]["primary"])
        name = f"{p['school']} {p['nickname']}"

        honors_awards = [a for a in self.T["awards"] if a["school"] == pid]
        honors_aa = [a for a in self.T["all_americans"] if a["school"] == pid]
        # players who led the team most often
        lead_count = Counter()
        for s in seasons:
            for cat, e in s["leaders"].items():
                lead_count[e["player"]] += 1
        greats = []
        for nm, c in lead_count.most_common(40):
            pl = self.player_by_name.get(nm)
            aw = [a for a in honors_awards if a["player"] == nm]
            aa = [a for a in honors_aa if a["player"] == nm]
            greats.append({"name": nm, "leads": c, "awards": aw, "aa": aa, "peak": pl.get("peak_rating") if pl else None,
                           "score": c + 3 * len(aw) + 2 * len(aa)})
        greats.sort(key=lambda g: -g["score"])
        rclasses = [c for c in self.T["recruiting_classes"] if c["program"] == pid and c.get("natl_rank")]

        self.render("program.html", p["href"], **common, active_tab="overview", seasons=seasons, latest=seasons[0],
                    greats=greats[:8], class_ranks=rclasses,
                    page_title=f"{name} · The Valhalla Archive",
                    description=f"{name} under Coach {p['coach']}: {p['career']['w']}-{p['career']['l']}, "
                                f"{len(p['national_titles'])} national titles, {len(p['big12_titles'])} Big 12 titles.")
        self.render("program_seasons.html", p["href"] + "seasons/", **common, active_tab="seasons", seasons=seasons,
                    page_title=f"Seasons · {name} · The Valhalla Archive",
                    description=f"Every {name} season since {p['first_season']}: records, finishes and leaders.")

        # Leaders
        cats = []
        for cat in LEADER_LABELS:
            rows = [{"season": s["season"], **s["leaders"][cat]} for s in seasons if cat in s["leaders"]]
            top = Counter(r["player"] for r in rows).most_common(3)
            best = max(rows, key=lambda r: r["value"] or 0) if rows else None
            cats.append({"key": cat, "label": LEADER_LABELS[cat], "rows": rows, "most": top, "best": best})
        career = [r for r in self.T["records_computed"] if r["scope"] == "career"] if pid == "CLEV" else []
        self.render("program_leaders.html", p["href"] + "leaders/", **common, active_tab="leaders", cats=cats,
                    career=career, page_title=f"Leaders · {name} · The Valhalla Archive",
                    description=f"{name} season leaders in passing, rushing, receiving, tackles, sacks and interceptions.")

        self.render("program_honors.html", p["href"] + "honors/", **common, active_tab="honors",
                    awards=sorted(honors_awards, key=lambda a: (-a["season"], a["award"])),
                    aas=sorted(honors_aa, key=lambda a: (-a["season"], a["unit"] or "", a["position"] or "")),
                    page_title=f"Honors · {name} · The Valhalla Archive",
                    description=f"{name} national award winners and All-Americans.")

        nat = [n for n in self.T["national_championships"] if pid in (n["champion"], n["runner_up"]) and n["season"] >= 2024]
        ccg = [c for c in self.T["conference_championships"] if pid in (c["champion"], c["runner_up"])]
        po = [x for x in self.T["playoffs"] if pid in (x["team_a"], x["team_b"])]
        po_by = defaultdict(list)
        for x in sorted(po, key=lambda x: (-x["season"], x["round_order"])):
            me_a = x["team_a"] == pid
            po_by[x["season"]].append({**x, "opp": x["team_b"] if me_a else x["team_a"], "us": x["score_a"] if me_a else x["score_b"],
                                       "them": x["score_b"] if me_a else x["score_a"], "won": x["winner"] == pid})
        bowls = [g for g in self.T["games"] if g["kind"] == "bowl"] if pid == "CLEV" else []
        self.render("program_titles.html", p["href"] + "titles/", **common, active_tab="titles", nat=nat,
                    ccg=sorted(ccg, key=lambda c: -c["season"]), playoffs=sorted(po_by.items(), key=lambda kv: -kv[0]),
                    bowls=sorted(bowls, key=lambda g: -g["season"]),
                    page_title=f"Titles & Postseason · {name} · The Valhalla Archive",
                    description=f"{name} national titles, Big 12 championships, playoff games and bowls.")

        if pid == "CLEV":
            off = defaultdict(lambda: defaultdict(list))
            for r in self.T["records_official"]:
                off[r["magnitude"]][r["duration"]].append(r)
            self.render("program_records.html", p["href"] + "records/", **common, active_tab="records",
                        official=[(m, sorted(off[m].items(), key=lambda kv: ["Game", "Season", "Career"].index(kv[0]) if kv[0] in ["Game", "Season", "Career"] else 9))
                                  for m in ["NCAA", "Big 12", "Cleveland State"] if m in off],
                        computed=self.T["records_computed"],
                        page_title=f"Records · {name} · The Valhalla Archive",
                        description="Cleveland State records: official NCAA, Big 12 and school records, plus season and career bests from the stats.")
            classes = sorted((c for c in self.T["recruiting_classes"] if c["program"] == "CLEV" and c.get("signees")),
                             key=lambda c: -c["cycle"])
            recruits = defaultdict(list)
            for r in self.T["recruits"]:
                recruits[r["cycle"]].append(r)
            for c in classes:
                c["recruits"] = sorted(recruits[c["cycle"]], key=lambda r: (r["natl_rank"] or 99999))
            others = [c for c in self.T["recruiting_classes"] if c["program"] != "CLEV" and c.get("natl_rank")]
            self.render("program_recruiting.html", p["href"] + "recruiting/", **common, active_tab="recruiting",
                        classes=classes, others=others, page_title=f"Recruiting · {name} · The Valhalla Archive",
                        description="Every Cleveland State recruiting class: stars, national ranks and home states.")
            deps = defaultdict(list)
            for d in self.T["departures"]:
                deps[d["season"]].append(d)
            dep_list = []
            for yr, ds in sorted(deps.items(), key=lambda kv: -kv[0]):
                ds = sorted(ds, key=lambda d: (d["draft_round"] or 99, -(d["overall"] or 0)))
                dep_list.append({"season": yr, "players": ds, "drafted": sum(1 for d in ds if d["drafted"]),
                                 "first": sum(1 for d in ds if d["draft_round"] == 1), "pending": all(d["outcome"] == "pending" for d in ds)})
            total_drafted = sum(1 for d in self.T["departures"] if d["drafted"])
            first_round = sum(1 for d in self.T["departures"] if d["draft_round"] == 1)
            self.render("program_departures.html", p["href"] + "departures/", **common, active_tab="departures",
                        deps=dep_list, total_drafted=total_drafted, first_round=first_round,
                        page_title=f"Draft & Departures · {name} · The Valhalla Archive",
                        description=f"Cleveland State graduates and draft picks: {total_drafted} drafted, {first_round} in the first round.")
            tr = defaultdict(list)
            for t in self.T["transfers"]:
                tr[t["cycle"]].append(t)
            self.render("program_transfers.html", p["href"] + "transfers/", **common, active_tab="transfers",
                        cycles=sorted(tr.items(), key=lambda kv: -kv[0]),
                        page_title=f"Transfers · {name} · The Valhalla Archive",
                        description="Every transfer into Cleveland State, by cycle, with their previous school.")

        for i, s in enumerate(seasons):
            self.build_season(p, s, prev=seasons[i + 1] if i + 1 < len(seasons) else None, nxt=seasons[i - 1] if i > 0 else None, common=common)

    # ---------------------------------------------------------------- season pages
    def build_season(self, p, s, prev, nxt, common):
        pid, yr = p["id"], s["season"]
        ctx = dict(common, active_tab="seasons", s=s, prev=prev, nxt=nxt)
        cg = [g for g in self.T["games"] if g["season"] == yr]
        if pid == "CLEV":
            w = l = 0
            games = []
            for g in cg:
                g = dict(g)
                if g["result"] == "W":
                    w += 1
                else:
                    l += 1
                g["running"] = f"{w}-{l}"
                games.append(g)
            ctx["games"] = games
            ps = [x for x in self.T["player_seasons"] if x["season"] == yr]
            ctx["stats"] = {c: sorted([x for x in ps if x["category"] == c], key=lambda x: -(x.get("yds") or x.get("fgm") or 0))
                            for c in ["passing", "rushing", "receiving", "kicking"]}
            dc = [d for d in self.T["depth_chart"] if d["season"] == yr and not d["projected"]]
            units = []
            for unit, slots in DEPTH_UNITS:
                rows = []
                for sl in slots:
                    ps_ = sorted([d for d in dc if d["slot"] == sl], key=lambda d: d["depth"])
                    if ps_:
                        rows.append({"slot": sl.replace("CB1", "CB 1").replace("CB2", "CB 2").replace("CB3", "CB 3"), "players": ps_})
                if rows:
                    units.append({"unit": unit, "rows": rows})
            ctx["depth"] = units
            ctx["staff"] = [c for c in self.T["coaches"] if c["program"] == "CLEV" and c["season"] == yr]
            ctx["recruits"] = sorted([r for r in self.T["recruits"] if r["arrival_season"] == yr], key=lambda r: r["natl_rank"] or 99999)
            ctx["transfers_in"] = [t for t in self.T["transfers"] if t["arrival_season"] == yr]
            ctx["departures"] = sorted([d for d in self.T["departures"] if d["season"] == yr], key=lambda d: (d["draft_round"] or 99, -(d["overall"] or 0)))
        else:
            vs = []
            for g in cg:
                if g["opponent"] == pid:
                    vs.append({**g, "us": g["opp_score"], "them": g["clev_score"], "won": g["result"] == "L"})
            ctx["vs_clev"] = vs
            ctx["staff"] = []
        po = []
        for x in self.T["playoffs"]:
            if x["season"] == yr and pid in (x["team_a"], x["team_b"]):
                me_a = x["team_a"] == pid
                po.append({**x, "opp": x["team_b"] if me_a else x["team_a"], "us": x["score_a"] if me_a else x["score_b"],
                           "them": x["score_b"] if me_a else x["score_a"], "won": x["winner"] == pid})
        ctx["playoffs"] = sorted(po, key=lambda x: x["round_order"])
        ctx["ccg"] = next((c for c in self.T["conference_championships"] if c["season"] == yr and c["conference"] == "Big 12"), None)
        ctx["awards"] = [a for a in self.T["awards"] if a["season"] == yr and a["school"] == pid]
        ctx["aas"] = [a for a in self.T["all_americans"] if a["season"] == yr and a["school"] == pid]
        ctx["standing"] = [x for x in self.T["standings"] if x["season"] == yr and x["conference"] == "Big 12"]
        ctx["class_rank"] = next((c for c in self.T["recruiting_classes"] if c["program"] == pid and c["cycle"] == yr and c.get("natl_rank")), None)
        title = f"{yr} {p['school']} {p['nickname']}"
        desc = f"{title}: {s['w']}-{s['l']}"
        if s["conf_rank_text"]:
            desc += f", {s['conf_rank_text']} in the Big 12"
        if s["national_champion"]:
            desc += ", National Champions"
        self.render("season.html", f"{p['href']}{yr}/", **ctx, page_title=f"{title} · The Valhalla Archive", description=desc + ".")

    # ---------------------------------------------------------------- game pages
    def build_games(self):
        games = self.T["games"]
        p = self.prog["CLEV"]
        by_opp = defaultdict(list)
        for g in games:
            by_opp[g["opponent"]].append(g)
        for i, g in enumerate(games):
            prev = games[i - 1] if i > 0 and games[i - 1]["season"] == g["season"] else None
            nxt = games[i + 1] if i + 1 < len(games) and games[i + 1]["season"] == g["season"] else None
            season_games = [x for x in games if x["season"] == g["season"]]
            idx = season_games.index(g)
            w = sum(1 for x in season_games[: idx + 1] if x["result"] == "W")
            l = idx + 1 - w
            series = by_opp[g["opponent"]]
            sw = sum(1 for x in series if x["result"] == "W")
            opp = self.teams.get(g["opponent"], {})
            label = g["name"] or f"Week {g['week']}"
            title = f"{g['season']} {label}: Cleveland State {g['clev_score']}, {opp.get('school') or g['opponent']} {g['opp_score']}"
            col = next((c for c in self.T["columns"] if c["game"] == g["id"]), None)
            self.render("game.html", f"games/{g['id']}/", program=p, active_nav="CLEV", theme_color=p["colors"]["primary"], column=col,
                        g=g, label=label, prev=prev, nxt=nxt, record_after=f"{w}-{l}", series=series,
                        series_rec=f"{sw}-{len(series) - sw}", opp=opp, season=self.season("CLEV", g["season"]),
                        page_title=f"{title} · The Valhalla Archive",
                        description=f"{title} ({'W' if g['result'] == 'W' else 'L'}). Cleveland State's all-time record vs {opp.get('school') or g['opponent']}: {sw}-{len(series) - sw}.")

    # ---------------------------------------------------------------- players
    def build_players(self):
        ps_by = defaultdict(list)
        for r in self.T["player_seasons"]:
            ps_by[r["player"]].append(r)
        index = []
        for p in self.T["players"]:
            pid = p["program"] if p["program"] in self.prog else None
            prog = self.prog.get(pid) if pid else None
            stats = {}
            for c in ["passing", "rushing", "receiving", "kicking"]:
                rows = sorted([r for r in ps_by[p["name"]] if r["category"] == c], key=lambda r: r["season"])
                if rows:
                    tot = {}
                    for k in ("yds", "td", "int", "comp", "att", "car", "rec", "fgm", "fga", "xpm", "xpa", "gp"):
                        vals = [r.get(k) for r in rows if isinstance(r.get(k), (int, float))]
                        if vals:
                            tot[k] = sum(vals)
                    tot["long"] = max([r.get("long") or 0 for r in rows])
                    stats[c] = {"rows": rows, "total": tot}
            ratings = sorted((int(k), v) for k, v in p["ratings"].items())
            spark = self.sparkline(ratings) if len(ratings) >= 2 else None
            journey = []
            if p.get("recruit"):
                r = p["recruit"]
                journey.append(f"Signed with Cleveland State in the {r['cycle']} recruiting cycle"
                               + (f" as a {r['stars']}-star" if r.get("stars") else "") + (f" (#{r['natl_rank']} nationally)" if r.get("natl_rank") else "")
                               + (f" from {r['state']}" if r.get("state") else ""))
            if p.get("transfer"):
                t = p["transfer"]
                frm = self.teams.get(t["from"], {}).get("school") or t["from"]
                to = self.teams.get(t["to"], {}).get("school") or t["to"]
                journey.append(f"Transferred from {frm} to {to} in the {t['cycle']} cycle")
            if p.get("departure"):
                d = p["departure"]
                if d["outcome"] == "drafted":
                    journey.append(f"Drafted in the {ordinal(d['draft_round'])} round after the {d['season']} season")
                elif d["outcome"] == "graduated":
                    journey.append(f"Left after the {d['season']} season (not drafted)")
                elif d["outcome"] == "cut":
                    journey.append(f"Left after the {d['season']} season")
                elif d["outcome"] == "pending":
                    journey.append(f"Departing after the {d['season']} season; draft to come")
            seasons_text = year_ranges(p["seasons"]) if p["seasons"] else ""
            title = p["name"]
            desc_bits = []
            if prog:
                desc_bits.append(f"{prog['school']} {prog['nickname']}")
            elif p["teams"]:
                desc_bits.append(", ".join(self.teams.get(t, {}).get("school") or t for t in p["teams"]))
            if p["positions"]:
                desc_bits.append("/".join(p["positions"][:3]))
            if seasons_text:
                desc_bits.append(seasons_text)
            honors = []
            if p["awards"]:
                honors.append(", ".join(f"{a['season']} {a['award']}" for a in p["awards"]))
            if p["all_american"]:
                honors.append(f"All-American {year_ranges([a['season'] for a in p['all_american']])}")
            self.render("player.html", f"players/{p['id']}/", program=prog, active_nav="players",
                        theme_color=prog["colors"]["primary"] if prog else None, p=p, stats=stats, spark=spark,
                        ratings=ratings, journey=journey, seasons_text=seasons_text,
                        hof=next((h for h in self.T["hall_of_fame"] if h["id"] == p["id"] and h["status"] == "inducted"), None),
                        page_title=f"{title} · The Valhalla Archive",
                        description=" · ".join(desc_bits + honors) or f"{title} in the Valhalla Archive.")
            index.append({"id": p["id"], "n": p["name"], "t": pid or (p["teams"][0] if p["teams"] else ""),
                          "f": p.get("position_family") or "", "pos": "/".join(p["positions"][:2]),
                          "y": seasons_text or year_ranges([a["season"] for a in p["awards"] + p["all_american"]]),
                          "pk": p.get("peak_rating"), "h": len(p["awards"]) + len(p["all_american"])})
        index.sort(key=lambda r: (r["t"] not in PROGRAMS, PROGRAMS.index(r["t"]) if r["t"] in PROGRAMS else 9, r["n"]))
        os.makedirs(os.path.join(OUT, "players"), exist_ok=True)
        self.render("players_index.html", "players/", active_nav="players", rows=index,
                    families=sorted({r["f"] for r in index if r["f"]}),
                    page_title="Players · The Valhalla Archive",
                    description=f"Search {len(index)} players from the Valhalla Archive: Cleveland State, Ohio, Miami (OH) and every award winner and All-American.")

    def sparkline(self, ratings):
        w, h, pad = 280, 80, 14
        ys = [v for _, v in ratings]
        lo, hi = min(ys) - 3, max(ys) + 3
        n = len(ratings)
        pts = []
        for i, (yr, v) in enumerate(ratings):
            x = pad + (w - 2 * pad) * (i / (n - 1))
            y = pad + (h - 2 * pad) * (1 - (v - lo) / (hi - lo))
            pts.append((round(x, 1), round(y, 1), yr, v))
        path = " ".join(f"{'M' if i == 0 else 'L'}{x},{y}" for i, (x, y, _, _) in enumerate(pts))
        dots = "".join(f'<circle cx="{x}" cy="{y}" r="4"/><text x="{x}" y="{y - 9}" text-anchor="middle">{v}</text>'
                       f'<text class="yr" x="{x}" y="{h + 6}" text-anchor="middle">{yr}</text>' for x, y, yr, v in pts)
        label = ", ".join(f"{yr}: {v}" for yr, v in ratings)
        return Markup(f'<svg class="spark" viewBox="0 -4 {w} {h + 14}" role="img" aria-label="Overall rating by season: {label}">'
                      f'<path d="{path}"/>{dots}</svg>')


    # ---------------------------------------------------------------- league almanac
    def build_almanac(self):
        T = self.T
        natl = sorted(T["national_championships"], key=lambda n: -n["season"])
        tally = Counter(n["champion"] for n in natl)
        seasons = sorted({n["season"] for n in natl}, reverse=True)
        confs = ["ACC", "Big 12", "Big Ten", "SEC", "Pac-12", "AAC", "C-USA", "MAC", "Mountain West", "Sun Belt"]
        ccg = {(c["season"], c["conference"]): c for c in T["conference_championships"]}
        matrix = [{"season": y, "cells": [ccg.get((y, c)) for c in confs]} for y in seasons if any(ccg.get((y, c)) for c in confs)]
        self.render("almanac.html", "almanac/", active_nav="almanac", natl=natl, tally=tally.most_common(),
                    seasons=seasons, confs=confs, matrix=matrix,
                    page_title="League Almanac · The Valhalla Archive",
                    description="National champions, playoff brackets, conference champions, AP polls, awards and All-Americans for every season of the dynasty.")
        awards = defaultdict(list)
        for a in T["awards"]:
            awards[a["award"]].append(a)
        order = ["Heisman", "Maxwell", "Camp", "Bednarik", "Nagurski", "O'Brien", "Walker", "Biletnikoff", "Mackey",
                 "Outland", "Rimington", "Lombardi", "Butkus", "Thorpe", "Groza", "Guy"]
        award_list = [{"name": k, "note": awards[k][0]["award_note"], "rows": sorted(awards[k], key=lambda a: -a["season"]),
                       "by_school": Counter(a["school"] for a in awards[k]).most_common(3)} for k in order if k in awards]
        school_tally = Counter(a["school"] for a in T["awards"] if a["season"] >= 2024)
        self.render("almanac_awards.html", "almanac/awards/", active_nav="almanac", awards=award_list,
                    school_tally=school_tally.most_common(10),
                    page_title="Awards by year · League Almanac · The Valhalla Archive",
                    description="Every national award winner in the dynasty, from the Heisman to the Ray Guy.")
        rounds = [("first_round", "First Round"), ("quarterfinal", "Quarterfinals"), ("semifinal", "Semifinals"), ("final", "National Championship")]
        std_order = ["Big 12", "ACC", "Big Ten", "SEC", "Pac-12", "AAC", "C-USA", "Independents", "MAC", "Mountain West", "Sun Belt"]
        for i, y in enumerate(seasons):
            games = [g for g in T["playoffs"] if g["season"] == y]
            bracket = [{"key": k, "label": l, "games": [g for g in games if g["round"] == k]} for k, l in rounds]
            bracket = [r for r in bracket if r["games"]]
            std = defaultdict(list)
            for x in T["standings"]:
                if x["season"] == y:
                    std[x["conference"]].append(x)
            aa = [a for a in T["all_americans"] if a["season"] == y]
            self.render("almanac_year.html", f"almanac/{y}/", active_nav="almanac", y=y,
                        natl=next((n for n in natl if n["season"] == y), None), bracket=bracket,
                        ccg=sorted([c for c in T["conference_championships"] if c["season"] == y], key=lambda c: confs.index(c["conference"]) if c["conference"] in confs else 99),
                        standings=[(c, sorted(std[c], key=lambda x: x["place"])) for c in std_order if std.get(c)],
                        ap=[a for a in T["ap_top25"] if a["season"] == y],
                        awards=sorted([a for a in T["awards"] if a["season"] == y], key=lambda a: order.index(a["award"]) if a["award"] in order else 99),
                        aa_units=[(u, [a for a in aa if a["unit"] == u]) for u in ("Offense", "Defense", "Special Teams") if any(a["unit"] == u for a in aa)],
                        prev=seasons[i + 1] if i + 1 < len(seasons) else None, nxt=seasons[i - 1] if i > 0 else None,
                        page_title=f"{y} season · League Almanac · The Valhalla Archive",
                        description=f"The {y} college football season: national champion, playoff bracket, conference champions, final AP Top 25, award winners and All-Americans.")

    # ---------------------------------------------------------------- records book
    def build_records(self):
        T = self.T
        off = defaultdict(lambda: defaultdict(list))
        for r in T["records_official"]:
            off[r["magnitude"]][r["duration"]].append(r)
        official = [(m, sorted(off[m].items(), key=lambda kv: ["Game", "Season", "Career"].index(kv[0]) if kv[0] in ["Game", "Season", "Career"] else 9))
                    for m in ["NCAA", "Big 12", "Cleveland State"] if m in off]
        seasons = T["seasons"]

        def ranked(rows, keyfn):
            keys = [keyfn(r) for r in rows]
            for r, k in zip(rows, keys):
                n = 1 + sum(1 for o in keys if o > k)
                r["rank"] = f"T-{n}" if keys.count(k) > 1 else str(n)
            return rows

        def top(label, unit, fn, n=5, key=None, disp=None):
            key = key or fn
            rows = sorted((s for s in seasons if fn(s) is not None), key=lambda s: key(s), reverse=True)[:n]
            out = [{"program": s["program"], "season": s["season"], "value": disp(s) if disp else fn(s), "_k": key(s)} for s in rows]
            ranked(out, lambda r: r["_k"])
            return {"label": label, "unit": unit, "rows": out}
        team_bests = [
            top("Best record", "", lambda s: s["w"], key=lambda s: (s["w"], -s["l"]), disp=lambda s: f"{s['w']}-{s['l']}"),
            top("Points per game", "", lambda s: s["team"].get("ppg")),
            top("Team passing yards", "", lambda s: s["team"].get("pass_yds")),
            top("Team rushing yards", "", lambda s: s["team"].get("rush_yds")),
        ]
        leader_bests = []
        for cat in LEADER_LABELS:
            rows = sorted(((s, s["leaders"][cat]) for s in seasons if cat in s["leaders"] and s["leaders"][cat]["value"] is not None),
                          key=lambda x: -x[1]["value"])[:5]
            lrows = [{"program": s["program"], "season": s["season"], "player": e["player"], "value": e["value"]} for s, e in rows]
            ranked(lrows, lambda r: r["value"])
            leader_bests.append({"label": f"{LEADER_LABELS[cat]}", "unit": LEADER_UNITS[cat], "rows": lrows})
        self.render("records_book.html", "records/", active_nav="records", official=official, computed=T["records_computed"],
                    team_bests=team_bests, leader_bests=leader_bests,
                    page_title="Records Book · The Valhalla Archive",
                    description="Official NCAA, Big 12 and Cleveland State records, plus team and individual bests across Cleveland State, Ohio and Miami (OH).")

    # ---------------------------------------------------------------- rivalry hub
    def build_rivalry(self):
        T = self.T
        pids = PROGRAMS
        meetings = defaultdict(list)
        for g in T["games"]:
            if g["opponent"] in ("OHIO", "M-OH"):
                meetings[("CLEV", g["opponent"])].append({"season": g["season"], "name": g["name"] or f"Week {g['week']}", "id": g["id"],
                                                          "winner": "CLEV" if g["result"] == "W" else g["opponent"],
                                                          "score": f"{max(g['clev_score'], g['opp_score'])}-{min(g['clev_score'], g['opp_score'])}"})
        for x in T["playoffs"]:
            if {x["team_a"], x["team_b"]} == {"OHIO", "M-OH"}:
                meetings[("OHIO", "M-OH")].append({"season": x["season"], "name": "CFP " + x["round_name"] if x["round"] != "final" else "National Championship",
                                                   "id": None, "winner": x["winner"], "score": f"{max(x['score_a'], x['score_b'])}-{min(x['score_a'], x['score_b'])}"})
        for c in T["conference_championships"]:
            if {c["champion"], c["runner_up"]} == {"OHIO", "M-OH"}:
                meetings[("OHIO", "M-OH")].append({"season": c["season"], "name": "Big 12 Championship", "id": None, "winner": c["champion"],
                                                   "score": f"{c['champion_score']}-{c['runner_up_score']}"})
        series = []
        for (a, b), ms in meetings.items():
            ms.sort(key=lambda m: -m["season"])
            wa = sum(1 for m in ms if m["winner"] == a)
            streak_team, streak = None, 0
            for m in ms:
                if streak_team in (None, m["winner"]):
                    streak_team, streak = m["winner"], streak + 1
                else:
                    break
            series.append({"a": a, "b": b, "games": ms, "wa": wa, "wb": len(ms) - wa, "streak_team": streak_team,
                           "streak": streak, "complete": a == "CLEV"})
        series.sort(key=lambda x: (not x["complete"], x["b"]))

        tallies = {}
        for pid in pids:
            p = self.prog[pid]
            ss = [x for x in T["seasons"] if x["program"] == pid]
            po = [x for x in T["playoffs"] if pid in (x["team_a"], x["team_b"])]
            h2h_w = sum(1 for ser in series for m in ser["games"] if pid in (ser["a"], ser["b"]) and m["winner"] == pid)
            h2h_g = sum(len(ser["games"]) for ser in series if pid in (ser["a"], ser["b"]))
            tallies[pid] = {
                "win_pct": p["career"]["win_pct"], "record": f"{p['career']['w']}-{p['career']['l']}",
                "natl": len(p["national_titles"]), "natl_years": p["national_titles"], "b12": len(p["big12_titles"]),
                "b12_years": p["big12_titles"], "playoff_wins": sum(1 for x in po if x["winner"] == pid),
                "playoff_apps": len(p["playoff_appearances"]),
                "title_games": len([n for n in T["national_championships"] if pid in (n["champion"], n["runner_up"]) and n["season"] >= 2024]),
                "h2h_pct": round(h2h_w / h2h_g, 3) if h2h_g else 0, "h2h": f"{h2h_w}-{h2h_g - h2h_w}",
                "awards": sum(1 for a in T["awards"] if a["school"] == pid),
                "heismans": sum(1 for a in T["awards"] if a["school"] == pid and a["award"] == "Heisman"),
                "aas": sum(1 for a in T["all_americans"] if a["school"] == pid),
                "top10": sum(1 for x in ss if x["ap_final_rank"] and x["ap_final_rank"] <= 10),
                "unbeaten": [x["season"] for x in ss if x["l"] == 0],
            }
        cup_cats = [("Career winning percentage", lambda t: t["win_pct"], lambda t: f"{t['win_pct']:.3f}".lstrip("0") + f" ({t['record']})"),
                    ("National titles", lambda t: t["natl"], lambda t: str(t["natl"])),
                    ("Big 12 titles", lambda t: t["b12"], lambda t: str(t["b12"])),
                    ("Playoff wins", lambda t: t["playoff_wins"], lambda t: str(t["playoff_wins"])),
                    ("Head-to-head vs the other two", lambda t: t["h2h_pct"], lambda t: t["h2h"]),
                    ("National award winners", lambda t: t["awards"], lambda t: str(t["awards"])),
                    ("All-Americans", lambda t: t["aas"], lambda t: str(t["aas"])),
                    ("Final AP top-10 finishes", lambda t: t["top10"], lambda t: str(t["top10"]))]
        cup_rows, totals = [], Counter()
        for label, val, disp in cup_cats:
            vals = {pid: val(tallies[pid]) for pid in pids}
            row = []
            for pid in pids:
                pts = 3 - sum(1 for o in pids if vals[o] > vals[pid])
                totals[pid] += pts
                row.append({"pid": pid, "disp": disp(tallies[pid]), "pts": pts, "best": vals[pid] == max(vals.values())})
            cup_rows.append({"label": label, "cells": row})
        standings = sorted(pids, key=lambda pid: -totals[pid])

        def finish_key(x):
            po = x.get("playoff")
            rnd = {"First Round": 1, "Quarterfinal": 2, "Semifinal": 3, "National Championship": 4}.get(po["exit_round"], 0) if po else 0
            return (x["national_champion"], x["national_runner_up"], rnd, -(x["ap_final_rank"] or 99), x["w"])
        years = []
        for y in sorted({x["season"] for x in T["seasons"]}, reverse=True):
            row = [self.season(pid, y) for pid in pids]
            best = max(row, key=finish_key)
            years.append({"season": y, "cells": [{"pid": x["program"], "s": x, "best": x is best,
                                                  "text": "National Champions" if x["national_champion"] else self.postseason_text(x)} for x in row]})
        crowns = Counter(c["pid"] for yr in years for c in yr["cells"] if c["best"])
        self.render("rivalry.html", "rivalry/", active_nav="rivalry", series=series, tallies=tallies, pids=pids,
                    cup_rows=cup_rows, totals=totals, standings=standings, years=years, crowns=crowns,
                    page_title="Rivalry Hub · The Valhalla Archive",
                    description="Josh Dolan vs Tim Slocombe vs Joe Snyderwine: head-to-head results, title counts and the Coaches' Cup.")

    # ---------------------------------------------------------------- hall of fame
    def build_hof(self):
        inducted = [dict(h, p=self.players[h["id"]]) for h in self.T["hall_of_fame"] if h["status"] == "inducted"]
        inducted.sort(key=lambda h: (h["class_of"] or 0, h["left_after"] or 0))
        classes = defaultdict(list)
        for h in inducted:
            classes[h["class_of"]].append(h)
        self.render("hall_of_fame.html", "hall-of-fame/", active_nav="hof", classes=sorted(classes.items(), key=lambda kv: -kv[0]),
                    count=len(inducted), page_title="Hall of Fame · The Valhalla Archive",
                    description=f"The Ring of Honor: {len(inducted)} inductees, the best of the Valhalla Archive.")



    # ---------------------------------------------------------------- split decision
    def column_context(self, c):
        """Render a column's Markdown sections and build its data-only facts box."""
        parsed = sd_columns.parse(os.path.join(ROOT, c["path"]))
        conv = lambda t: Markup(md_lib.markdown(t, extensions=["smarty"]))
        g = next(x for x in self.T["games"] if x["id"] == c["game"])
        season_games = [x for x in self.T["games"] if x["season"] == g["season"]]
        idx = season_games.index(g)
        w = sum(1 for x in season_games[: idx + 1] if x["result"] == "W")
        opp = self.teams.get(g["opponent"], {})
        facts = {"game": g["name"] or f"Week {g['week']}", "date": g["date"], "opponent": g["opponent"], "opp_name": opp.get("school") or g["opponent"],
                 "site": {"home": "Home", "away": "Away", "neutral": "Neutral site"}[g["site"]],
                 "score": f"{g['clev_score']}-{g['opp_score']}", "result": g["result"], "record": f"{w}-{idx + 1 - w}", "season": g["season"]}
        exchange = []
        for line in parsed["sections"].get("Back and forth", "").splitlines():
            m = re.match(r"^\*\*(Mickey|Ken):\*\*\s*(.+)$", line.strip())
            if m:
                exchange.append({"who": m.group(1), "text": conv(m.group(2))})
        return {"c": c, "g": g, "facts": facts, "mickey": conv(parsed["sections"].get("Mickey", "")),
                "ken": conv(parsed["sections"].get("Ken", "")), "exchange": exchange,
                "verdict": conv(parsed["sections"].get("Final Verdict", ""))}

    def build_split_decision(self):
        cols = self.T["columns"]
        if not cols:
            return
        games = {g["id"]: g for g in self.T["games"]}
        p = self.prog["CLEV"]
        for i, c in enumerate(cols):
            ctx = self.column_context(c)
            prev = cols[i - 1] if i > 0 else None
            nxt = cols[i + 1] if i + 1 < len(cols) else None
            self.render("column.html", f"split-decision/{c['id']}/", active_nav="split", prev=prev, nxt=nxt, **ctx,
                        page_title=f"{c['headline']} · Split Decision · The Valhalla Archive",
                        description=f"Split Decision on {ctx['facts']['season']} {ctx['facts']['game']}: Cleveland State {ctx['facts']['score']} vs {ctx['facts']['opp_name']}. Mickey Bridges and Lil Ken Hogmanes argue it out.")
        by_season = defaultdict(list)
        for c in cols:
            g = games[c["game"]]
            by_season[c["season"]].append({**c, "g": g, "opp": self.teams.get(g["opponent"], {}).get("school") or g["opponent"]})
        latest = cols[-1]
        self.render("split_decision.html", "split-decision/", active_nav="split", seasons=sorted(by_season.items(), key=lambda kv: -kv[0]),
                    latest=self.column_context(latest), count=len(cols),
                    page_title="Split Decision · The Valhalla Archive",
                    description="Split Decision: Mickey Bridges believes, Lil Ken Hogmanes doubts. A column on every Cleveland State game.")

    # ---------------------------------------------------------------- front page
    def build_home(self):
        T = self.T
        cur = self.site["current_season"]
        order = ["Heisman", "Maxwell", "Camp", "Bednarik", "Nagurski", "O'Brien", "Walker", "Biletnikoff", "Mackey",
                 "Outland", "Rimington", "Lombardi", "Butkus", "Thorpe", "Groza", "Guy"]
        by_year = defaultdict(list)
        for a in T["awards"]:
            t = self.teams.get(a["school"], {})
            pl = self.player_by_name.get(a["player"])
            by_year[a["season"]].append({
                "award": a["award"], "note": a["award_note"], "player": a["player"], "school": a["school"],
                "school_name": t.get("school") or a["school"], "logo": (BASE + t["logo"]) if t.get("logo") else None,
                "href": f"{BASE}players/{pl['id']}/" if pl else None, "ours": a["school"] in PROGRAMS})
        for y in by_year:
            by_year[y].sort(key=lambda a: (a["school"] != "CLEV", order.index(a["award"]) if a["award"] in order else 99))
        years = sorted(by_year, reverse=True)
        aa_counts = {y: Counter(a["school"] for a in T["all_americans"] if a["season"] == y) for y in years}
        award_json = {str(y): {"awards": by_year[y], "aa": {p: aa_counts[y].get(p, 0) for p in PROGRAMS},
                               "clev": sum(1 for a in by_year[y] if a["school"] == "CLEV")} for y in years}

        # Road to next season: phase tracker + teasers built only from logged data
        nxt = cur + 1
        phases = self.site["phases"]
        cur_phase = self.site["current_phase"]
        phase_idx = phases.index(cur_phase) if cur_phase in phases else 0
        deps = sorted([d for d in T["departures"] if d["season"] == cur], key=lambda d: -(d["overall"] or 0))
        proj = [d for d in T["depth_chart"] if d["season"] == nxt and d["depth"] == 1]
        key_slots = ["QB", "RB", "WR", "TE", "LT", "LE", "MLB", "CB1", "FS"]
        proj_show, seen = [], set()
        for sl in key_slots:
            for d in proj:
                if d["slot"] == sl and (sl, d["player"]) not in seen:
                    seen.add((sl, d["player"]))
                    proj_show.append(d)
                    break
        incoming = sorted([r for r in T["recruits"] if r["arrival_season"] == nxt], key=lambda r: r["natl_rank"] or 99999)
        next_games = [g for g in T["games"] if g["season"] == nxt]
        teasers = [
            {"key": "departures", "title": "Departing seniors & draft watch", "unlocked": bool(deps),
             "unlock_phase": "Player Departures and Draft",
             "summary": f"{len(deps)} players leaving after {cur}" + (f"; {sum(1 for d in deps if d['drafted'])} drafted" if any(d['drafted'] for d in deps) else "; draft to come"),
             "rows": [{"name": d["player"], "meta": f"{d['position']} · {d['overall']} OVR", "tag": (f"Rd {d['draft_round']}" if d["drafted"] else None)} for d in deps[:5]]},
            {"key": "depth", "title": f"Projected {nxt} depth chart", "unlocked": bool(proj),
             "unlock_phase": f"{nxt} Preseason",
             "summary": f"Early look at the {nxt} starters" + (" (players still listed as departing are flagged)" if any(d["departing"] for d in proj) else ""),
             "rows": [{"name": d["player"], "meta": d["slot"].replace("CB1", "CB"), "tag": "Departing" if d["departing"] else None} for d in proj_show]},
            {"key": "recruits", "title": f"Incoming {nxt} recruits", "unlocked": bool(incoming), "unlock_phase": "Final Recruiting",
             "summary": f"{len(incoming)} signees logged" if incoming else "Cards reveal as each recruit is logged",
             "rows": [{"name": r["player"], "meta": f"{r['position'] or ''} · #{r['natl_rank']}" if r["natl_rank"] else (r["position"] or ""), "tag": (f"{int(r['stars'])}★" if r["stars"] else None)} for r in incoming[:5]]},
            {"key": "schedule", "title": f"{nxt} schedule & rivalry previews", "unlocked": bool(next_games), "unlock_phase": f"{nxt} Preseason",
             "summary": f"{len(next_games)} games set" if next_games else "Unlocks when the schedule is set",
             "rows": [{"name": self.teams.get(g["opponent"], {}).get("school") or g["opponent"], "meta": g["name"] or f"Week {g['week']}", "tag": None} for g in next_games[:5]]},
        ]
        champ = next((n for n in T["national_championships"] if n["season"] == cur), None)
        champ_season = self.season(champ["champion"], cur) if champ and champ["champion"] in self.prog else None
        columns = T.get("columns") or []
        clips = T.get("clips") or []
        self.render("home.html", "", page_title="The Valhalla Archive", active_nav="home",
                    description=f"The almanac of a College Football 25 dynasty: Cleveland State, Ohio and Miami (OH). {cur} national champions: "
                                + (f"{self.prog[champ['champion']]['school']} {self.prog[champ['champion']]['nickname']}." if champ_season else f"{(self.teams.get(champ['champion'], {}) or {}).get('school', '')}." if champ else ""),
                    years=years, award_year=years[0], award_json=award_json, cur=cur, nxt=nxt,
                    phases=phases, phase_idx=phase_idx, teasers=teasers, champ=champ, champ_season=champ_season,
                    latest_col=self.column_context(columns[-1]) if columns else None, columns=columns, clips=clips)

    # ---------------------------------------------------------------- games (M8)
    def build_play(self):
        qs = trivia_gen.generate(self.T)
        data_dir = os.path.join(OUT, "assets", "data")
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, "trivia.json"), "w", encoding="utf-8") as f:
            json.dump({"generated": self.site.get("last_updated"), "questions": qs}, f, ensure_ascii=False, separators=(",", ":"))
        hl = hl_gen.generate(self.T)
        with open(os.path.join(data_dir, "higherlower.json"), "w", encoding="utf-8") as f:
            json.dump(hl, f, ensure_ascii=False, separators=(",", ":"))
        pdl = pd_gen.generate(self.T)
        with open(os.path.join(data_dir, "playerdle.json"), "w", encoding="utf-8") as f:
            json.dump(pdl, f, ensure_ascii=False, separators=(",", ":"))
        grd = grid_gen.generate(self.T)
        with open(os.path.join(data_dir, "grid.json"), "w", encoding="utf-8") as f:
            json.dump(grd, f, ensure_ascii=False, separators=(",", ":"))
        eras = [{"key": k, "label": f"{a}-{b}"} for k, a, b in trivia_gen.ERAS]
        games = [
            {"key": "trivia", "ready": True, "href": "play/trivia/", "kicker": "Ten questions a round", "title": "Archive Trivia",
             "text": "Champions, awards, stat leaders, big games and recruits. Pick a program, an era and a difficulty."},
            {"key": "higherlower", "ready": True, "href": "play/higher-lower/", "kicker": "Stat duel", "title": "Higher or Lower",
             "text": "Two real stat lines or records. Which one is bigger?"},
            {"key": "playerdle", "ready": True, "href": "play/playerdle/", "kicker": "Daily puzzle", "title": "Playerdle",
             "text": "Guess the mystery player in a few tries using clues about program, position, class and more."},
            {"key": "grid", "ready": True, "href": "play/grid/", "kicker": "Nine squares", "title": "The Grid",
             "text": "Fill each square with a player who fits both its row and its column."},
            {"key": "wordsearch", "ready": False, "kicker": "Printable too", "title": "Word Search",
             "text": "Themed grids of rosters, award winners and program legends."},
        ]
        self.render("play_hub.html", "play/", active_nav="play", page_title="Games · The Valhalla Archive",
                    description="Trivia and puzzle games built from the Valhalla Archive's dynasty data.", games=games)
        self.render("play_trivia.html", "play/trivia/", active_nav="play", page_title="Archive Trivia · The Valhalla Archive",
                    description=f"Trivia from the dynasty's records: {len(qs)} questions on Cleveland State, Ohio, Miami (OH) and the league.",
                    eras=eras, total=f"{len(qs):,}")
        self.render("play_higherlower.html", "play/higher-lower/", active_nav="play", page_title="Higher or Lower · The Valhalla Archive",
                    description="Guess whether the next real stat line from the dynasty is higher or lower. Keep the streak alive.",
                    total=f"{len(hl['cards']):,}")
        self.render("play_playerdle.html", "play/playerdle/", active_nav="play", page_title="Playerdle · The Valhalla Archive",
                    description="Guess the mystery player from the dynasty in eight tries. A new daily puzzle every day, plus unlimited practice.")
        self.render("play_grid.html", "play/grid/", active_nav="play", page_title="The Grid · The Valhalla Archive",
                    description="Fill a 3x3 grid with dynasty players who fit both their row and their column. Daily grid plus practice.",
                    total=f"{len(grd['players']):,}")

    # ---------------------------------------------------------------- run
    def build(self):
        if os.path.isdir(OUT):
            shutil.rmtree(OUT)
        os.makedirs(OUT)
        shutil.copytree(os.path.join(SRC, "assets"), os.path.join(OUT, "assets"))
        shutil.copytree(os.path.join(SRC, "design"), os.path.join(OUT, "design"))
        open(os.path.join(OUT, ".nojekyll"), "w").close()
        self.build_home()
        for p in self.programs:
            self.build_program(p)
        self.build_games()
        self.build_players()
        self.build_almanac()
        self.build_records()
        self.build_rivalry()
        self.build_hof()
        self.build_split_decision()
        self.build_play()
        print(f"Built {self.pages} pages into _site/ (base path {BASE})")


if __name__ == "__main__":
    Site().build()
