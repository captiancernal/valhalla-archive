"""Render the static website from data/tables/*.json and site/templates into _site/.

Usage:
  py -P scripts/build_site.py                 # local build, links start at "/"
  BASE_PATH=/valhalla-archive/ py -P scripts/build_site.py   # GitHub Pages build
"""
import datetime
import json
import os
import shutil
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "data", "tables")
SRC = os.path.join(ROOT, "site")
OUT = os.path.join(ROOT, "_site")
BASE = os.environ.get("BASE_PATH", "/")
if not BASE.endswith("/"):
    BASE += "/"

PROGRAM_SLUGS = {"CLEV": "cleveland-state", "OHIO": "ohio", "M-OH": "miami-oh"}
SHORT = {"CLEV": "Cleveland State", "OHIO": "Ohio", "M-OH": "Miami (OH)"}


def load(name):
    with open(os.path.join(TABLES, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def year_ranges(years):
    """[2029, 2030, 2031, 2033] -> '2029-2031, 2033'."""
    years = sorted(years)
    out, start = [], None
    for i, y in enumerate(years):
        if start is None:
            start = y
        if i == len(years) - 1 or years[i + 1] != y + 1:
            out.append(str(start) if start == y else f"{start}-{y}")
            start = None
    return ", ".join(out)


def postseason_text(s):
    if s["national_champion"]:
        return ""  # shown as a "National Champions" pill
    po = s.get("playoff")
    if po:
        if s["national_runner_up"]:
            return "Lost National Championship"
        return f"Lost in CFP {po['exit_round']}"
    bowl = s.get("bowl")
    if bowl:
        return f"{'Won' if bowl['result'] == 'W' else 'Lost'} {bowl['name']} vs {bowl['opponent']}, {bowl['score']}"
    return ""


class Site:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(os.path.join(SRC, "templates")),
                               autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
        self.site = load("site_control")
        self.programs_raw = load("programs")
        self.seasons = load("seasons")
        self.natl = load("national_championships")
        self.build_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        updated = datetime.date.fromisoformat(self.site["last_updated"])
        self.site["last_updated_display"] = updated.strftime("%B %-d, %Y") if os.name != "nt" else updated.strftime("%B %#d, %Y")

        self.programs = []
        for p in self.programs_raw:
            p = dict(p)
            p["slug"] = PROGRAM_SLUGS[p["id"]]
            p["href"] = f"programs/{p['slug']}/"
            p["win_pct_text"] = f"{p['career']['win_pct']:.3f}".lstrip("0")
            titles = p["national_titles"]
            p["tagline"] = (f"National champions {year_ranges(titles)}" if titles else f"{p['career']['w']}-{p['career']['l']} since {p['first_season']}")
            self.programs.append(p)

        # Nav: only sections that exist get a link (no dead links).
        self.nav = [{"key": "home", "label": "Home", "href": "", "footer": True}, {"sep": True}]
        for p in self.programs:
            self.nav.append({"key": p["id"], "label": SHORT[p["id"]], "href": p["href"], "logo": p["logo"]})

        cur = self.site["current_season"]
        champ = next((n for n in self.natl if n["season"] == cur), None)
        self.banner = None
        if champ:
            cp = next((p for p in self.programs if p["id"] == champ["champion"]), None)
            if cp:
                rec = next(s for s in self.seasons if s["program"] == cp["id"] and s["season"] == cur)
                self.banner = {"text": f"{cur} National Champions: {cp['school']} {cp['nickname']}, {rec['w']}-{rec['l']}",
                               "href": cp["href"], "logo": cp["logo"]}

    def render(self, template, path, **ctx):
        base_ctx = {"base": BASE, "site": self.site, "programs": self.programs, "nav": self.nav,
                    "banner": self.banner, "build_id": self.build_id, "program": None}
        base_ctx.update(ctx)
        html = self.env.get_template(template).render(**base_ctx)
        dest = os.path.join(OUT, path, "index.html") if not path.endswith(".html") else os.path.join(OUT, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(html)
        return dest

    def build(self):
        if os.path.isdir(OUT):
            shutil.rmtree(OUT)
        os.makedirs(OUT)
        shutil.copytree(os.path.join(SRC, "assets"), os.path.join(OUT, "assets"))
        shutil.copytree(os.path.join(SRC, "design"), os.path.join(OUT, "design"))
        open(os.path.join(OUT, ".nojekyll"), "w").close()

        pages = []
        pages.append(self.render("home.html", "", page_title="The Valhalla Archive",
                                 description="The almanac of a College Football 25 dynasty: Cleveland State, Ohio and Miami (OH), 2024 to today.",
                                 active_nav="home"))
        for p in self.programs:
            seasons = sorted((dict(s) for s in self.seasons if s["program"] == p["id"]), key=lambda s: -s["season"])
            for s in seasons:
                s["postseason_text"] = postseason_text(s)
            tabs = [{"key": "overview", "label": "Overview", "href": p["href"]}]
            pages.append(self.render(
                "program.html", p["href"].rstrip("/"), program=p, seasons=seasons, program_tabs=tabs,
                active_tab="overview", active_nav=p["id"], theme_color=p["colors"]["primary"],
                page_title=f"{p['school']} {p['nickname']} · The Valhalla Archive",
                description=f"{p['school']} {p['nickname']} under Coach {p['coach']}: {p['career']['w']}-{p['career']['l']}, "
                            f"{len(p['national_titles'])} national titles, {len(p['big12_titles'])} Big 12 titles."))
        print(f"Built {len(pages)} pages into _site/ (base path {BASE})")


if __name__ == "__main__":
    Site().build()
