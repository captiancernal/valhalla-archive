"""Share-preview images (1200x630) shown when a link to the site is posted in a chat or on social media.

One general Archive card plus one card per program, drawn with the site's own fonts and approved
palettes. Every number comes from data/tables (programs.json); nothing is invented.
Called by build_site.py on every build; can also run alone:  py -P scripts/share_images.py
"""
import glob
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "site", "assets", "fonts")
W, H = 1200, 630

INK, BONE, BRASS = "#15171b", "#f6f3ec", "#c4a35a"
PALETTE = {  # approved 2026-10-26 (tokens.css)
    "CLEV": {"bg": "#024731", "deep": "#012a1d", "accent": "#c9a54e", "text": "#ffffff"},
    "OHIO": {"bg": "#00694e", "deep": "#00402f", "accent": "#e9d8b4", "text": "#ffffff"},
    "M-OH": {"bg": "#b61e2e", "deep": "#7a0f1b", "accent": "#ffffff", "text": "#ffffff"},
}


def font(prefix, size, name=None, axes=None):
    """Load a self-hosted woff2 (Latin set). `name` picks a static weight by its internal name."""
    for f in sorted(glob.glob(os.path.join(FONTS, f"{prefix}-latin-[0-9a-f]*.woff2"))):
        ft = ImageFont.truetype(f, size)
        if name and " ".join(ft.getname()) != name:
            continue
        if axes:
            ft.set_variation_by_axes(axes)
        return ft
    raise FileNotFoundError(f"font {prefix} {name or ''} not found; run scripts/fetch_fonts.py")


def serif(size, weight=700):
    return font("source-serif-4-normal", size, axes=[weight, 60])


def ui(size, weight=500):
    return font("inter-normal", size, axes=[weight])


def display(pid, size):
    if pid == "CLEV":
        return font("barlow-condensed-normal", size, "Barlow Condensed ExtraBold Regular")
    if pid == "OHIO":
        return font("zilla-slab-normal", size, "Zilla Slab Bold")
    return font("archivo-italic", size, axes=[850, 112])


def shield(d, x, y, s):
    """The Archive's shield-and-V mark (same shape as the header SVG, 30x34 units)."""
    k = s / 34
    pts = [(15, 1), (28, 6), (28, 17), (24, 26), (15, 33), (6, 26), (2, 17), (2, 6)]
    d.line([(x + px * k, y + py * k) for px, py in pts + pts[:1]], fill=BRASS, width=max(2, int(2 * k)), joint="curve")
    d.line([(x + 8 * k, y + 10 * k), (x + 15 * k, y + 25 * k), (x + 22 * k, y + 10 * k)], fill=BONE, width=max(3, int(2.6 * k)), joint="curve")


def fit(d, text, make, size, max_w):
    while size > 20:
        f = make(size)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return make(size)


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def archive_card(programs, site, logos_dir, champ_line):
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 14, W, H], fill=BRASS)
    shield(d, 80, 92, 120)
    d.text((232, 104), "THE", font=ui(26, 700), fill=BRASS)
    d.text((228, 132), "Valhalla Archive", font=serif(92, 700), fill=BONE)
    d.text((82, 262), "The almanac of a College Football 25 dynasty", font=ui(34, 500), fill="#d8d4ca")
    if champ_line:
        d.text((82, 312), champ_line, font=ui(28, 600), fill=BRASS)
    x = 82
    for p in programs:
        logo = Image.open(os.path.join(logos_dir, p["id"] + ".png")).convert("RGBA")
        logo.thumbnail((84, 84))
        plate = Image.new("RGBA", (104, 104), (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle([0, 0, 103, 103], 14, fill=BONE)
        plate.alpha_composite(logo, ((104 - logo.width) // 2, (104 - logo.height) // 2))
        im.paste(plate, (x, 410), plate)
        d.text((x + 120, 422), p["short"], font=ui(28, 700), fill=BONE)
        d.text((x + 120, 460), f"{p['career']['w']}-{p['career']['l']}", font=ui(26, 500), fill="#b9b5ab")
        x += 360
    d.text((82, 566), f"Data through the {site['latest_season_in_tracker']} season", font=ui(22, 500), fill="#9a968d")
    return im


def program_card(p, logos_dir):
    c = PALETTE[p["id"]]
    im = Image.new("RGB", (W, H), c["bg"])
    d = ImageDraw.Draw(im)
    # Program shapes, echoing each theme: chamfer stripes (CLEV), rounded base (OHIO), diagonal cut (M-OH)
    if p["id"] == "CLEV":
        for i in range(0, W + H, 34):
            d.line([(W * 0.55 + i, 0), (W * 0.55 + i - H, H)], fill="#0a5239", width=3)
    elif p["id"] == "M-OH":
        d.polygon([(W - 330, 0), (W - 170, 0), (W - 330, H), (W - 490, H)], fill="#9c1726")
    d.rectangle([0, H - 16, W, H], fill=c["accent"])
    logo = Image.open(os.path.join(logos_dir, p["id"] + ".png")).convert("RGBA")
    logo.thumbnail((250, 250))
    if p["id"] == "CLEV":
        im.paste(logo, (80, 150), logo)
    else:
        plate = Image.new("RGBA", (290, 290), (0, 0, 0, 0))
        pd = ImageDraw.Draw(plate)
        if p["id"] == "OHIO":
            pd.ellipse([0, 0, 289, 289], fill="#f4efe1", outline=c["accent"], width=10)
        else:
            pd.polygon([(28, 0), (289, 0), (261, 289), (0, 289)], fill="#ffffff")
        plate.alpha_composite(logo, ((290 - logo.width) // 2, (290 - logo.height) // 2))
        im.paste(plate, (60, 130), plate)
    tx = 400
    d.text((tx, 120), f"{p['school'].upper()} · {p['conference'].upper()}", font=ui(26, 700), fill=c["accent"])
    name = p["nickname"].upper() if p["id"] != "OHIO" else p["nickname"]
    d.text((tx - 4, 158), name, font=fit(d, name, lambda s: display(p["id"], s), 150, W - tx - 60), fill=c["text"])
    d.text((tx, 330), f"Coach {p['coach']}", font=ui(32, 600), fill=c["text"])
    bits = [f"{p['career']['w']}-{p['career']['l']} since {p['first_season']}"]
    if p["national_titles"]:
        bits.append(plural(len(p["national_titles"]), "national title"))
    if p["big12_titles"]:
        bits.append(plural(len(p["big12_titles"]), "Big 12 title"))
    d.text((tx, 384), "  ·  ".join(bits), font=ui(30, 500), fill=c["text"])
    d.rectangle([0, 520, W, H - 16], fill=c["deep"])
    shield(d, 60, 540, 52)
    d.text((118, 548), "The Valhalla Archive", font=serif(36, 700), fill=BONE)
    return im


def make_all(out_dir, programs, site, logos_dir, champ_line=None):
    os.makedirs(out_dir, exist_ok=True)
    made = {}
    archive_card(programs, site, logos_dir, champ_line).save(os.path.join(out_dir, "archive.png"), optimize=True)
    made["archive"] = "archive.png"
    for p in programs:
        fn = f"{p['slug']}.png"
        program_card(p, logos_dir).save(os.path.join(out_dir, fn), optimize=True)
        made[p["id"]] = fn
    return made


if __name__ == "__main__":
    import json
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    progs = json.load(open(os.path.join(ROOT, "data", "tables", "programs.json"), encoding="utf-8"))
    for p in progs:
        p["slug"] = {"CLEV": "cleveland-state", "OHIO": "ohio", "M-OH": "miami-oh"}[p["id"]]
        p["short"] = {"CLEV": "Cleveland State", "OHIO": "Ohio", "M-OH": "Miami (OH)"}[p["id"]]
    site = json.load(open(os.path.join(ROOT, "data", "tables", "site_control.json"), encoding="utf-8"))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "_site", "assets", "share")
    print(make_all(out, progs, site, os.path.join(ROOT, "site", "assets", "logos")))
