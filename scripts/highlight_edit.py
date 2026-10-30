"""Turn a raw game capture into a broadcast-style highlight, ready for clips.py.

The edit: a title card over the blurred pre-snap crowd, the live play, a white flash into a
slow-motion replay (REPLAY tag + name strip), then a final-score card. Vikings look throughout:
Barlow Condensed, forest green, Valhalla gold, chamfered corners.

Facts on screen come only from two places (the Archive's rules):
  * the game record in data/tables/games.json (season, week or game name, opponent, site, final score)
  * the owner's own words, passed in as --title / --tag / --names / --line
Nothing else is written on the video.

Step 1, find the moments (snap, throw, catch) on a contact sheet of stills:
  py -P scripts/highlight_edit.py sheet "<video>" [--from 6 --to 13 --fps 4]
Step 2, cut the edit:
  py -P scripts/highlight_edit.py make "<video>" --game 2037-CLEV-11 --live 4.4 12.7 --replay 8.4 11.6
        [--title "4th & inches"] [--tag "4th & inches · first down"] [--names Pashos Flannigan Sawyer]
        [--line "Pass knocked loose, caught for the first down"] [--slow 2] [--no-replay]
        [--intro-from 0] [--out "<file.mp4>"]
  It writes content/clips/incoming/<game>-highlight.mp4, moves a raw file that was sitting in
  incoming/ to originals/ ("(raw capture)"), and prints the clips.py add command to finish.

Needs ffmpeg (winget Gyan.FFmpeg) and the extras in requirements-local.txt (fontTools + brotli,
used to read the site's own .woff2 fonts).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clips import INCOMING, ORIGINALS, probe, tool  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = os.path.join(ROOT, "data", "tables")
LOGOS = os.path.join(ROOT, "site", "assets", "logos")
FONTS = os.path.join(ROOT, "site", "assets", "fonts")
WORK = os.path.join(tempfile.gettempdir(), "valhalla-highlights")
W, H = 1920, 1080
SS = 2  # graphics are drawn at 2x and scaled down for smooth edges

# Vikings palette (site/assets/css/tokens.css, [data-program="CLEV"])
GREEN, DEEP = (2, 71, 49), (1, 42, 29)
GOLD, STEEL = (201, 165, 78), (140, 147, 153)
WHITE, BONE, MIST = (255, 255, 255), (246, 243, 236), (196, 202, 207)
SAFE_BOTTOM = 930  # keep graphics above the game's own score bug


# ------------------------------------------------------------------ data
def load(name):
    with open(os.path.join(TABLES, f"{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def game_facts(game_id):
    g = next((x for x in load("games") if x["id"].lower() == game_id.lower()), None)
    if not g:
        sys.exit(f"No game {game_id} in the data. Log it in the tracker first (or check the id on its game page).")
    schools = {t["id"]: t["school"] for t in load("teams")}
    schools.update({p["id"]: p["school"] for p in load("programs")})
    us = schools.get(g["program"], g["program"])
    them = schools.get(g["opponent"], g["opponent"])
    label = f"WEEK {g['week']}" if g["kind"] == "regular" and g.get("week") else (g.get("name") or "").upper()
    if g["site"] == "home":
        left, right, matchup = g["opponent"], g["program"], f"{them} at {us}"
    elif g["site"] == "away":
        left, right, matchup = g["program"], g["opponent"], f"{us} at {them}"
    else:
        left, right, matchup = g["program"], g["opponent"], f"{us} vs {them}"
    return {"id": g["id"], "season": g["season"], "label": label, "program": g["program"], "opponent": g["opponent"],
            "us": us, "them": them, "matchup": matchup, "left": left, "right": right,
            "us_score": g.get("clev_score"), "them_score": g.get("opp_score")}


# ------------------------------------------------------------------ fonts and drawing
def barlow(weight, size):
    """The site's Barlow Condensed (.woff2) converted once to .ttf in a temp folder."""
    path = os.path.join(WORK, "fonts", f"barlow-{weight}.ttf")
    if not os.path.exists(path):
        try:
            from fontTools.ttLib import TTFont
        except ImportError:
            sys.exit("Missing fontTools. Run: py -m pip install --user -r requirements-local.txt")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for f in os.listdir(FONTS):
            if f.startswith("barlow-condensed-normal-latin-") and "-ext-" not in f:
                t = TTFont(os.path.join(FONTS, f))
                t.flavor = None
                t.save(os.path.join(WORK, "fonts", f"barlow-{t['OS/2'].usWeightClass}.ttf"))
        if not os.path.exists(path):
            sys.exit(f"Barlow Condensed weight {weight} not found in site/assets/fonts/.")
    return ImageFont.truetype(path, round(size * SS))


def canvas():
    return Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))


def save_png(img, name):
    path = os.path.join(WORK, name)
    img.resize((W, H), Image.LANCZOS).save(path)
    return path


def chamfer(x0, y0, x1, y1, c):
    c, x0, y0, x1, y1 = (v * SS for v in (c, x0, y0, x1, y1))
    return [(x0 + c, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1), (x0, y1), (x0, y0 + c)]


def width(d, text, f, tracking=0.0):
    return (sum(d.textlength(ch, font=f) for ch in text) + tracking * f.size * (len(text) - 1)) / SS


def draw(d, xy, text, f, fill, tracking=0.0, center=False):
    """Letter-spaced text on a baseline; returns its width in output pixels."""
    w = width(d, text, f, tracking)
    x, y = (xy[0] - (w / 2 if center else 0)) * SS, xy[1] * SS
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += d.textlength(ch, font=f) + tracking * f.size
    return w


def fit(d, text, weight, size, max_w, tracking=0.0, min_size=30):
    """Largest font size (<= size) that keeps the text within max_w."""
    while size > min_size and width(d, text, barlow(weight, size), tracking) > max_w:
        size -= 2
    return barlow(weight, size)


def logo(abbr, max_w, max_h):
    path = os.path.join(LOGOS, f"{abbr}.png")
    if not os.path.exists(path):
        return None
    im = Image.open(path).convert("RGBA")
    s = min(max_w / im.width, max_h / im.height)
    return im.resize((round(im.width * s * SS), round(im.height * s * SS)), Image.LANCZOS)


def paste_center(img, im, cx, cy):
    if im is not None:
        img.alpha_composite(im, (round(cx * SS - im.width / 2), round(cy * SS - im.height / 2)))


def gradient(w, h, a, b, alpha=255):
    """Diagonal gradient from a (top-left) to b (bottom-right)."""
    small = Image.new("RGBA", (64, 36))
    px = small.load()
    for y in range(36):
        for x in range(64):
            t = x / 63 * 0.65 + y / 35 * 0.35
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (alpha,)
    return small.resize((w, h), Image.BICUBIC)


# ------------------------------------------------------------------ the four graphics
def title_card(facts, title):
    img = canvas()
    d = ImageDraw.Draw(img)
    img.alpha_composite(gradient(W * SS, 440 * SS, DEEP, GREEN, 236), (0, 320 * SS))
    d.rectangle([0, 320 * SS, W * SS, 326 * SS], fill=GOLD)
    d.rectangle([0, 754 * SS, W * SS, 760 * SS], fill=GOLD)
    paste_center(img, logo(facts["left"], 270, 190), 230, 540)
    paste_center(img, logo(facts["right"], 270, 190), 1690, 540)
    draw(d, (960, 420), f"{facts['season']}  ·  {facts['label']}", barlow(700, 44), GOLD, 0.18, center=True)
    big = (title or facts["matchup"]).upper()
    draw(d, (960, 610), big, fit(d, big, 800, 172, 1120, 0.02), WHITE, 0.02, center=True)
    if title:
        line = facts["matchup"].upper().replace(" AT ", "  AT  ").replace(" VS ", "  VS  ")
        draw(d, (960, 700), line, fit(d, line, 600, 46, 1120, 0.12), BONE, 0.12, center=True)
    draw(d, (96, 1000), "THE VALHALLA ARCHIVE", barlow(700, 30), BONE, 0.2)
    draw(d, (96, 1036), "HIGHLIGHTS", barlow(700, 26), GOLD, 0.3)
    return save_png(img, "title.png")


def name_strip(names, tag, line):
    """Lower third: gold tag, names with gold chevrons, optional small line. Returns (png, width)."""
    img = canvas()
    d = ImageDraw.Draw(img)
    x0 = 96
    has_line = bool(line)
    panel_h = 150 if has_line else 118
    y0 = SAFE_BOTTOM - 28 - panel_h
    sep = "  ›  "
    parts = [n.upper() for n in names]
    f_big = fit(d, sep.join(parts), 800, 74, 1500, 0.03, 44)
    f_line = barlow(600, 31)
    w_names = width(d, sep.join(parts), f_big, 0.03)
    w_line = width(d, line.upper(), f_line, 0.1) if has_line else 0
    x1 = x0 + 48 + max(w_names, w_line) + 56
    d.polygon(chamfer(x0, y0, x1, y0 + panel_h, 18), fill=GREEN + (242,))
    d.rectangle([x0 * SS, (y0 + 18) * SS, (x0 + 10) * SS, (y0 + panel_h) * SS], fill=GOLD)
    if tag:
        f_tag = barlow(700, 30)
        tw = width(d, tag.upper(), f_tag, 0.16)
        d.polygon(chamfer(x0, y0 - 46, x0 + tw + 40, y0, 10), fill=GOLD + (255,))
        draw(d, (x0 + 20, y0 - 13), tag.upper(), f_tag, DEEP, 0.16)
    x = x0 + 48
    for i, n in enumerate(parts):
        x += draw(d, (x, y0 + 100), n, f_big, WHITE, 0.03)
        if i < len(parts) - 1:
            x += draw(d, (x, y0 + 100), sep, f_big, GOLD, 0.03)
    if has_line:
        draw(d, (x0 + 50, y0 + 137), line.upper(), f_line, MIST, 0.1)
    return save_png(img, "names.png"), x1


def replay_tag():
    img = canvas()
    d = ImageDraw.Draw(img)
    f = barlow(800, 44)
    x1, y0 = W - 72, 64
    x0 = x1 - (width(d, "REPLAY", f, 0.2) + 96)
    d.polygon(chamfer(x0, y0, x1, y0 + 70, 14), fill=GREEN + (240,))
    d.rectangle([x0 * SS, (y0 + 64) * SS, (x1 - 14) * SS, (y0 + 70) * SS], fill=GOLD)
    tx, ty = (x0 + 26) * SS, (y0 + 35) * SS
    d.polygon([(tx, ty - 15 * SS), (tx, ty + 15 * SS), (tx + 24 * SS, ty)], fill=GOLD)
    draw(d, (x0 + 64, y0 + 51), "REPLAY", f, WHITE, 0.2)
    return save_png(img, "replay.png"), x0


def final_card(facts):
    img = gradient(W * SS, H * SS, DEEP, GREEN, 255)
    d = ImageDraw.Draw(img)
    paste_center(img, logo(facts["program"], 300, 230), 960, 265)
    if facts["us_score"] is not None and facts["them_score"] is not None:
        draw(d, (960, 470), "FINAL", barlow(700, 46), GOLD, 0.35, center=True)
        a = f"{facts['us'].upper()}  {facts['us_score']}"
        b = f"{facts['them'].upper()}  {facts['them_score']}"
        draw(d, (960, 600), a, fit(d, a, 800, 110, 1600, 0.02), WHITE, 0.02, center=True)
        draw(d, (960, 720), b, fit(d, b, 700, 84, 1600, 0.03), STEEL, 0.03, center=True)
    else:  # score not in the data: no final line rather than a guess
        m = facts["matchup"].upper()
        draw(d, (960, 640), m, fit(d, m, 800, 96, 1600, 0.02), WHITE, 0.02, center=True)
    d.rectangle([(960 - 60) * SS, 770 * SS, (960 + 60) * SS, 776 * SS], fill=GOLD)
    draw(d, (960, 830), f"{facts['season']}  ·  {facts['label']}", barlow(600, 38), BONE, 0.18, center=True)
    draw(d, (960, 1010), "THE VALHALLA ARCHIVE", barlow(700, 30), BONE, 0.25, center=True)
    return save_png(img, "final.png")


# ------------------------------------------------------------------ commands
def cmd_sheet(a):
    info = probe(a.video)
    os.makedirs(WORK, exist_ok=True)
    start = a.start or 0.0
    end = min(a.end or info["duration"], info["duration"])
    n = max(1, int((end - start) * a.fps))
    cols = 5
    rows = (n + cols - 1) // cols
    out = os.path.join(WORK, re.sub(r"[^\w-]+", "-", os.path.splitext(os.path.basename(a.video))[0]) + "-sheet.jpg")
    font = barlow(700, 22).path.replace("\\", "/").replace(":", "\\:")
    vf = (f"fps={a.fps},scale=480:-2,drawtext=fontfile='{font}':text='%{{pts\\:hms\\:{start}}}':x=6:y=6:"
          f"fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6,tile={cols}x{rows}")
    subprocess.run([tool("ffmpeg"), "-v", "error", "-y", "-ss", str(start), "-t", str(end - start), "-i", a.video,
                    "-vf", vf, "-frames:v", "1", out], check=True)
    print(f"{os.path.basename(a.video)}: {info['duration']:.1f}s, {info['width']}x{info['height']} @ {info['fps']:g} fps, "
          f"{'with' if info['audio'] else 'no'} sound")
    print(f"Contact sheet ({n} stills, {start:g}s to {end:g}s): {out}")


def cmd_make(a):
    info = probe(a.video)
    facts = game_facts(a.game)
    dur = info["duration"]
    live_s, live_e = a.live
    if not (0 <= live_s < live_e <= dur + 0.05):
        sys.exit(f"--live must be inside the clip (0 to {dur:.1f}s).")
    live_e = min(live_e, dur)
    replay = None if a.no_replay else a.replay
    if replay is None and not a.no_replay:
        sys.exit("Give --replay START END (the moment to show again), or --no-replay.")
    if replay and not (0 <= replay[0] < replay[1] <= dur + 0.05):
        sys.exit(f"--replay must be inside the clip (0 to {dur:.1f}s).")
    if (a.names or a.line or a.tag) and not replay:
        sys.exit("The name strip appears on the replay; drop --no-replay or leave out --names/--tag/--line.")

    os.makedirs(WORK, exist_ok=True)
    title = title_card(facts, a.title)
    final = final_card(facts)
    intro_len = 2.6
    intro_s = min(a.intro_from, max(0.0, dur - intro_len))
    end_len, x_in, x_rp, x_end = 2.8, 0.4, 0.3, 0.6
    fps = "60000/1001" if info["fps"] > 50 else "30000/1001"
    fit_frame = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    live_len = live_e - live_s
    rep_len = (replay[1] - replay[0]) * a.slow if replay else 0

    inputs = ["-i", a.video, "-loop", "1", "-t", f"{intro_len}", "-i", title]
    v = [f"[0:v]trim={intro_s}:{intro_s + intro_len},setpts=PTS-STARTPTS,fps={fps},{fit_frame},gblur=sigma=18,"
         f"eq=brightness=-0.2:saturation=0.5[ibg]",
         "[1:v]format=rgba,fade=in:st=0.15:d=0.4:alpha=1[iov]",
         "[ibg][iov]overlay=0:0:shortest=1,fade=in:st=0:d=0.35,format=yuv420p,settb=AVTB[intro]",
         f"[0:v]trim={live_s}:{live_e},setpts=PTS-STARTPTS,fps={fps},{fit_frame},format=yuv420p,settb=AVTB[live]"]
    o1 = intro_len - x_in
    chain = ["[intro][live]xfade=transition=fade:duration=%s:offset=%.3f[v1]" % (x_in, o1)]
    last, pos = "v1", o1 + live_len
    idx = 2
    if replay:
        tag_png, tag_x = replay_tag()
        inputs += ["-loop", "1", "-t", f"{rep_len}", "-i", tag_png]
        tag_in = idx
        idx += 1
        tag_slide = f"if(lt(t,0.15),{W - tag_x},if(lt(t,0.45),{W - tag_x}*pow(1-(t-0.15)/0.3,3),0))"
        v += [f"[0:v]trim={replay[0]}:{replay[1]},setpts={a.slow}*(PTS-STARTPTS),fps={fps},{fit_frame}[rp0]",
              f"[{tag_in}:v]format=rgba[tag]",
              f"[rp0][tag]overlay=x='{tag_slide}':y=0:shortest=1[rp1]"]
        rp = "rp1"
        if a.names:
            strip_png, strip_w = name_strip(a.names, a.tag, a.line)
            inputs += ["-loop", "1", "-t", f"{rep_len}", "-i", strip_png]
            t_in, t_out = min(0.9, rep_len * 0.2), max(rep_len - 0.8, rep_len * 0.6)
            slide = (f"if(lt(t,{t_in}),-{strip_w},if(lt(t,{t_in}+0.35),"
                     f"-{strip_w}+{strip_w}*(1-pow(1-(t-{t_in})/0.35,3)),0))")
            v += [f"[{idx}:v]format=rgba,fade=out:st={t_out}:d=0.3:alpha=1[strip]",
                  f"[rp1][strip]overlay=x='{slide}':y=0:shortest=1[rp2]"]
            idx += 1
            rp = "rp2"
        v.append(f"[{rp}]format=yuv420p,settb=AVTB[replay]")
        o2 = pos - x_rp
        chain.append(f"[{last}][replay]xfade=transition=fadewhite:duration={x_rp}:offset={o2:.3f}[v2]")
        last, pos = "v2", o2 + rep_len
    inputs += ["-loop", "1", "-t", f"{end_len}", "-i", final]
    v.append(f"[{idx}:v]fps={fps},format=yuv420p,fade=out:st={end_len - 0.5}:d=0.5,settb=AVTB[end]")
    o3 = pos - x_end
    chain.append(f"[{last}][end]xfade=transition=fadeblack:duration={x_end}:offset={o3:.3f}[v]")
    total = o3 + end_len

    if info["audio"]:
        tail = max(0.0, min(dur, live_e + end_len) - live_e)
        aud = [f"[0:a]atrim={intro_s}:{intro_s + intro_len},asetpts=PTS-STARTPTS,volume=0.6,afade=in:st=0:d=0.6[ai]",
               f"[0:a]atrim={live_s}:{live_e},asetpts=PTS-STARTPTS[al]"]
        if tail > 0.1:
            aud.append(f"[0:a]atrim={live_e}:{live_e + tail},asetpts=PTS-STARTPTS,volume=0.7,"
                       f"apad=whole_dur={end_len},afade=out:st={end_len - 1.4}:d=1.4[ae]")
        else:
            aud.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{end_len}[ae]")
        aud.append(f"[ai][al]acrossfade=d={x_in}[a1]")
        prev = "a1"
        if replay:
            aud += [f"[0:a]atrim={replay[0]}:{replay[1]},asetpts=PTS-STARTPTS,atempo={1 / a.slow},volume=0.45[ar]",
                    f"[a1][ar]acrossfade=d={x_rp}[a2]"]
            prev = "a2"
        aud.append(f"[{prev}][ae]acrossfade=d={x_end}[a]")
    else:  # silent capture: keep a silent track so every clip plays the same way
        aud = [f"anullsrc=r=48000:cl=stereo,atrim=0:{total:.3f}[a]"]

    out = a.out or unique(os.path.join(INCOMING, f"{facts['id'].lower()}-highlight.mp4"))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    cmd = [tool("ffmpeg"), "-v", "error", "-y", *inputs, "-filter_complex", ";".join(v + chain + aud),
           "-map", "[v]", "-map", "[a]", "-r", fps, "-c:v", "libx264", "-preset", "slow", "-crf", "16",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    print(f"Cutting the highlight for {facts['id']} ({facts['matchup']}, {facts['season']} {facts['label'].title()})...")
    subprocess.run(cmd, check=True)

    # the raw capture leaves the inbox, so incoming/ holds only the edit for clips.py
    src = os.path.abspath(a.video)
    if os.path.dirname(src) == os.path.abspath(INCOMING) and not a.out:
        os.makedirs(ORIGINALS, exist_ok=True)
        stem, ext = os.path.splitext(os.path.basename(src))
        dest = unique(os.path.join(ORIGINALS, f"{stem} (raw capture){ext}"))
        shutil.move(src, dest)
        print(f"Raw capture moved to content/clips/originals/{os.path.basename(dest)}")

    poster = (o1 + live_len - x_rp + rep_len * 0.65) if (replay and a.names) else (o1 + live_len * 0.7)
    print(f"Wrote {os.path.relpath(out, ROOT)}: {total:.1f}s. Live play from {o1:.1f}s"
          + (f", replay from {pos - rep_len:.1f}s" if replay else "") + f", final card from {o3:.1f}s.")
    print("Next (caption in the owner's words, players as they appear on the site):")
    print(f'  py -P scripts/clips.py add "{os.path.relpath(out, ROOT)}" --season {facts["season"]} '
          f'--opponent {facts["opponent"]} --game {facts["id"]} --what "<owner\'s caption>" '
          f'[--player "<Full Name>"]... --poster-at {poster:.1f}')


def unique(path):
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(f"{stem}-{n}{ext}"):
        n += 1
    return f"{stem}-{n}{ext}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet", help="contact sheet of timestamped stills")
    s.add_argument("video")
    s.add_argument("--from", dest="start", type=float)
    s.add_argument("--to", dest="end", type=float)
    s.add_argument("--fps", type=float, default=2)
    s.set_defaults(fn=cmd_sheet)
    m = sub.add_parser("make", help="cut the highlight edit")
    m.add_argument("video")
    m.add_argument("--game", required=True, help="game id, e.g. 2037-CLEV-11 (title and final card come from it)")
    m.add_argument("--live", type=float, nargs=2, required=True, metavar=("START", "END"))
    m.add_argument("--replay", type=float, nargs=2, metavar=("START", "END"))
    m.add_argument("--no-replay", action="store_true")
    m.add_argument("--slow", type=float, default=2.0, help="replay slow-down factor (2 = half speed)")
    m.add_argument("--title", help="big words on the title card (owner's words), e.g. '4th & inches'")
    m.add_argument("--tag", help="small gold tag above the names (owner's words)")
    m.add_argument("--names", nargs="+", help="names on the replay strip, in order (as the owner gave them)")
    m.add_argument("--line", help="small line under the names (owner's words)")
    m.add_argument("--intro-from", type=float, default=0.0, help="where the blurred title-card background starts")
    m.add_argument("--out", help="output file (default: content/clips/incoming/<game>-highlight.mp4)")
    m.set_defaults(fn=cmd_make)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
