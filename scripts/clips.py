"""Highlight clips: compress raw game captures into small web videos with a poster image.

The owner drops MP4s into content/clips/incoming/ (git-ignored). Each clip gets a caption
from the owner (season, opponent, what happened); this script never invents one.

  py -P scripts/clips.py status                 new files waiting, published clips, space used
  py -P scripts/clips.py add "<file>" --season 2037 --opponent OHIO --what "Pashos to Flannigan for 94 yards"
        [--game 2037-CLEV-17] [--player "Paul Flannigan"]... [--poster-at 12.5]
  py -P scripts/clips.py list                   every published clip
  py -P scripts/clips.py remove <clip-id>       take a clip off the site
  py -P scripts/clips.py check                  validation used by the build (exit 1 on problems)

Output: content/clips/<id>.mp4 (H.264 + AAC, at most 1080p, fast-start), content/clips/<id>.jpg
(poster), and an entry in content/clips/clips.json. The original moves to
content/clips/originals/ (git-ignored); archive it in Drive "02 Clips Source".
No Git LFS (GitHub Pages can't serve LFS files): clips are committed as normal files, so the
script keeps a size budget and warns early.
"""
import argparse
import datetime as dt
import difflib
import glob
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIPS = os.environ.get("CLIPS_DIR") or os.path.join(ROOT, "content", "clips")
INCOMING = os.path.join(CLIPS, "incoming")
ORIGINALS = os.path.join(CLIPS, "originals")
INDEX = os.path.join(CLIPS, "clips.json")
TABLES = os.path.join(ROOT, "data", "tables")

# Size rules. GitHub Pages sites must stay under 1 GB and GitHub asks that repos stay small,
# so clips get a 500 MB total budget with a warning at 75%.
CLIP_CAP_MB = 25          # one clip, after compression
BUDGET_MB = 500           # all clips together
WARN_AT = 0.75
LONG_CLIP_S = 120         # longer clips are allowed but flagged
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi")


# ------------------------------------------------------------------ helpers
def tool(name):
    """ffmpeg/ffprobe from PATH, or from the winget install folder if PATH isn't refreshed yet."""
    found = shutil.which(name)
    if found:
        return found
    pattern = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages", "Gyan.FFmpeg*", "*", "bin", name + ".exe")
    hits = sorted(glob.glob(pattern))
    if hits:
        return hits[-1]
    sys.exit(f"{name} not found. Install it with: winget install --id Gyan.FFmpeg -e")


def probe(path):
    out = subprocess.run([tool("ffprobe"), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode:
        sys.exit(f"Can't read {os.path.basename(path)} as a video: {out.stderr.strip()[:300]}")
    info = json.loads(out.stdout)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if not v:
        sys.exit(f"{os.path.basename(path)} has no video track.")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    fps = v.get("avg_frame_rate") or v.get("r_frame_rate") or "30/1"
    num, den = (fps.split("/") + ["1"])[:2]
    return {"duration": float(info["format"].get("duration") or v.get("duration") or 0),
            "width": int(v["width"]), "height": int(v["height"]),
            "fps": round(float(num) / float(den or 1), 2) if float(den or 1) else 30.0,
            "audio": a is not None, "size": os.path.getsize(path)}


def mb(n):
    return n / 1024 / 1024


def load_index():
    if os.path.exists(INDEX):
        with open(INDEX, encoding="utf-8") as f:
            return json.load(f)
    return {"about": "Highlight clips shown on the site. Captions are written by the owner. Managed by scripts/clips.py.", "clips": []}


def save_index(idx):
    idx["clips"].sort(key=lambda c: (-c["season"], c.get("game") or "", c["id"]))
    with open(INDEX, "w", encoding="utf-8", newline="\n") as f:
        json.dump(idx, f, indent=2, ensure_ascii=False)
        f.write("\n")


def table(name):
    with open(os.path.join(TABLES, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def teams():
    with open(os.path.join(ROOT, "data", "reference", "teams.json"), encoding="utf-8") as f:
        return json.load(f)["teams"]


def resolve_team(text):
    t = teams()
    key = text.strip()
    if key.upper() in t:
        return key.upper()
    low = {v.lower(): k for k, v in t.items()}
    if key.lower() in low:
        return low[key.lower()]
    near = [f"{k} ({v})" for k, v in t.items() if key.lower() in v.lower()]
    near += [f"{low[m]} ({t[low[m]]})" for m in difflib.get_close_matches(key.lower(), list(low), n=3, cutoff=0.75)]
    sys.exit(f"Unknown opponent '{text}'." + (f" Did you mean: {', '.join(near[:6])}?" if near else " Use the abbreviation, e.g. OHIO or M-OH."))


def resolve_game(season, opp, game_id=None):
    """Return (game, message). A game that isn't in the tracker yet is allowed (linked on a later build)."""
    games = table("games")
    if game_id:
        g = next((x for x in games if x["id"].lower() == game_id.lower()), None)
        if not g:
            sys.exit(f"No game with id {game_id}.")
        if g["season"] != season or g["opponent"] != opp:
            sys.exit(f"{g['id']} is {g['season']} vs {g['opponent']}, not {season} vs {opp}.")
        return g, None
    hits = [x for x in games if x["season"] == season and x["opponent"] == opp]
    if len(hits) == 1:
        return hits[0], None
    if len(hits) > 1:
        opts = "; ".join(f"{g['id']} ({g['name'] or 'Week ' + str(g['week'])}, {g['clev_score']}-{g['opp_score']})" for g in hits)
        sys.exit(f"Cleveland State played {opp} {len(hits)} times in {season}. Add --game with one of: {opts}")
    seasons = {x["season"] for x in games}
    if season in seasons:
        sys.exit(f"Cleveland State didn't play {opp} in {season} according to the tracker.")
    return None, f"No {season} games are in the tracker yet; the clip will link to its game once that game is logged."


def canon_player(name):
    with open(os.path.join(ROOT, "data", "aliases.json"), encoding="utf-8") as f:
        aliases = json.load(f)
    amap = {}
    for canon, variants in (aliases.get("players") or {}).items():  # canonical name -> misspellings
        for v in variants:
            amap[v.lower()] = canon
    players = table("players")
    names = {p["name"].lower(): p for p in players}
    n = amap.get(name.lower(), name)
    p = names.get(n.lower())
    if not p:
        near = difflib.get_close_matches(n, [x["name"] for x in players], n=5, cutoff=0.75)
        sys.exit(f"No player named '{name}'." + (f" Did you mean: {', '.join(near)}?" if near else ""))
    return p


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def used_bytes(idx):
    total = 0
    for c in idx["clips"]:
        for k in ("file", "poster"):
            p = os.path.join(CLIPS, c[k])
            if os.path.exists(p):
                total += os.path.getsize(p)
    return total


def budget_line(idx):
    used = mb(used_bytes(idx))
    pct = used / BUDGET_MB
    line = f"Clips use {used:.1f} MB of the {BUDGET_MB} MB budget ({pct:.0%})."
    if pct >= 1:
        line += " OVER BUDGET: remove or shorten clips before publishing."
    elif pct >= WARN_AT:
        line += " Getting full: talk to the owner before adding more."
    return line


# ------------------------------------------------------------------ encoding
def encode(src, dest, info, bitrate_k=None, height=None):
    h = height or min(1080, info["height"])
    vf = f"scale=-2:'min({h},ih)':flags=lanczos"
    if info["fps"] > 60.5:
        vf += ",fps=60"
    cmd = [tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-map", "0:v:0"]
    if info["audio"]:
        cmd += ["-map", "0:a:0"]
    cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p"]
    if bitrate_k:
        cmd += ["-b:v", f"{bitrate_k}k", "-maxrate", f"{int(bitrate_k * 1.5)}k", "-bufsize", f"{bitrate_k * 2}k"]
    else:
        cmd += ["-crf", "24", "-maxrate", "5M", "-bufsize", "10M"]
    if info["audio"]:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-ac", "2"]
    cmd += ["-movflags", "+faststart", "-map_metadata", "-1", dest]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit("ffmpeg failed: " + r.stderr.strip()[:500])


def poster(src, dest, at):
    cmd = [tool("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{at:.2f}", "-i", src,
           "-frames:v", "1", "-vf", "scale='min(1280,iw)':-2:flags=lanczos", "-q:v", "3", dest]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode or not os.path.exists(dest):
        sys.exit("Couldn't make the poster image: " + r.stderr.strip()[:300])


# ------------------------------------------------------------------ commands
def incoming_files():
    if not os.path.isdir(INCOMING):
        return []
    return sorted(f for f in os.listdir(INCOMING) if f.lower().endswith(VIDEO_EXT))


def cmd_status(_):
    idx = load_index()
    files = incoming_files()
    print(f"Waiting in content/clips/incoming/: {len(files)}")
    for f in files:
        i = probe(os.path.join(INCOMING, f))
        flag = "  (long clip)" if i["duration"] > LONG_CLIP_S else ""
        print(f"  {f}: {i['duration']:.1f}s, {i['width']}x{i['height']} @ {i['fps']:g} fps, {mb(i['size']):.1f} MB{flag}")
    print(f"Published clips: {len(idx['clips'])}")
    print(budget_line(idx))


def cmd_add(a):
    src = a.file if os.path.isabs(a.file) else os.path.join(INCOMING, os.path.basename(a.file))
    if not os.path.exists(src):
        sys.exit(f"Can't find {a.file} in content/clips/incoming/.")
    what = " ".join(a.what.split())
    if len(what) < 8:
        sys.exit("Please give a caption that says what happened (at least a few words).")
    opp = resolve_team(a.opponent)
    if opp == "CLEV":
        sys.exit("The opponent can't be Cleveland State.")
    game, note = resolve_game(a.season, opp, a.game)
    players = [canon_player(n) for n in (a.player or [])]
    idx = load_index()
    if any(c.get("source_name") == os.path.basename(src) and c.get("source_bytes") == os.path.getsize(src) for c in idx["clips"]):
        sys.exit(f"{os.path.basename(src)} was already added.")

    base = (game["id"].lower() if game else f"{a.season}-{slug(opp)}")
    n = 1
    while any(c["id"] == f"{base}-{n}" for c in idx["clips"]):
        n += 1
    cid = f"{base}-{n}"
    info = probe(src)
    if info["duration"] <= 0:
        sys.exit("That video has no length.")
    mp4, jpg = os.path.join(CLIPS, cid + ".mp4"), os.path.join(CLIPS, cid + ".jpg")

    print(f"Compressing {os.path.basename(src)} ({info['duration']:.1f}s, {info['width']}x{info['height']}, {mb(info['size']):.1f} MB)...")
    encode(src, mp4, info)
    size = os.path.getsize(mp4)
    if mb(size) > CLIP_CAP_MB:
        # Too big: drop to 720p at a bitrate that lands under the cap.
        kbps = int((CLIP_CAP_MB * 0.92 * 8 * 1024) / info["duration"]) - (128 if info["audio"] else 0)
        if kbps < 600:
            os.remove(mp4)
            sys.exit(f"This clip is too long to fit the {CLIP_CAP_MB} MB cap at a watchable quality. Trim it and try again.")
        print(f"  {mb(size):.1f} MB is over the {CLIP_CAP_MB} MB cap; re-encoding at 720p, {kbps} kb/s...")
        encode(src, mp4, info, bitrate_k=kbps, height=720)
        size = os.path.getsize(mp4)
    out = probe(mp4)
    at = a.poster_at if a.poster_at is not None else min(out["duration"] * 0.4, max(0.0, out["duration"] - 0.5))
    poster(mp4, jpg, at)

    entry = {
        "id": cid, "season": a.season, "opponent": opp, "game": game["id"] if game else None,
        "what": what, "players": [p["id"] for p in players],
        "file": cid + ".mp4", "poster": cid + ".jpg",
        "duration": round(out["duration"], 1), "width": out["width"], "height": out["height"],
        "bytes": size, "added": dt.date.today().isoformat(),
        "source_name": os.path.basename(src), "source_bytes": info["size"],
    }
    idx["clips"].append(entry)
    if mb(used_bytes(idx)) > BUDGET_MB:
        os.remove(mp4); os.remove(jpg)
        sys.exit(f"Adding this clip would go over the {BUDGET_MB} MB budget. Nothing was added.")
    save_index(idx)
    os.makedirs(ORIGINALS, exist_ok=True)
    shutil.move(src, os.path.join(ORIGINALS, os.path.basename(src)))
    print(f"Added {cid}: {mb(size):.1f} MB ({out['width']}x{out['height']}, {out['duration']:.1f}s), poster at {at:.1f}s.")
    if note:
        print("  " + note)
    if info["duration"] > LONG_CLIP_S:
        print(f"  Note: this clip is over {LONG_CLIP_S // 60} minutes; shorter clips keep the site light.")
    print(f"  Original moved to content/clips/originals/ (archive it in Drive '02 Clips Source').")
    print(budget_line(idx))


def cmd_list(_):
    idx = load_index()
    for c in idx["clips"]:
        print(f"{c['id']:<22} {c['season']} vs {c['opponent']:<6} {c['duration']:>6.1f}s {mb(c['bytes']):>5.1f} MB  {c['what']}")
    print(f"{len(idx['clips'])} clips. " + budget_line(idx))


def cmd_remove(a):
    idx = load_index()
    c = next((x for x in idx["clips"] if x["id"] == a.id), None)
    if not c:
        sys.exit(f"No clip {a.id}.")
    for k in ("file", "poster"):
        p = os.path.join(CLIPS, c[k])
        if os.path.exists(p):
            os.remove(p)
    idx["clips"].remove(c)
    save_index(idx)
    print(f"Removed {a.id} from the site. Note: a clip that was already committed stays in the git history,")
    print("so removing it doesn't shrink the repository.")


def problems():
    """Checks used by validate/build: files exist, games/players exist, sizes within limits."""
    idx = load_index()
    games = {g["id"]: g for g in table("games")}
    players = {p["id"] for p in table("players")}
    seasons = {g["season"] for g in games.values()}
    errs = []
    ids = set()
    for c in idx["clips"]:
        if c["id"] in ids:
            errs.append(f"duplicate clip id {c['id']}")
        ids.add(c["id"])
        for k in ("file", "poster"):
            if not os.path.exists(os.path.join(CLIPS, c[k])):
                errs.append(f"{c['id']}: missing {c[k]}")
        if c.get("game"):
            g = games.get(c["game"])
            if not g:
                errs.append(f"{c['id']}: game {c['game']} not in the data")
            elif g["season"] != c["season"] or g["opponent"] != c["opponent"]:
                errs.append(f"{c['id']}: season/opponent don't match {c['game']}")
        elif c["season"] in seasons and not any(g["season"] == c["season"] and g["opponent"] == c["opponent"] for g in games.values()):
            errs.append(f"{c['id']}: no {c['season']} game vs {c['opponent']} in the data")
        for pid in c.get("players", []):
            if pid not in players:
                errs.append(f"{c['id']}: unknown player {pid}")
        if mb(c.get("bytes", 0)) > CLIP_CAP_MB:
            errs.append(f"{c['id']}: {mb(c['bytes']):.1f} MB is over the {CLIP_CAP_MB} MB cap")
        if not c.get("what"):
            errs.append(f"{c['id']}: no caption")
    if mb(used_bytes(idx)) > BUDGET_MB:
        errs.append(budget_line(idx))
    return errs


def cmd_check(_):
    errs = problems()
    for e in errs:
        print("PROBLEM:", e)
    print(f"{len(load_index()['clips'])} clips, {len(errs)} problems. " + budget_line(load_index()))
    sys.exit(1 if errs else 0)


def main():
    ap = argparse.ArgumentParser(description="Highlight clips pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    p = sub.add_parser("add")
    p.add_argument("file")
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--opponent", required=True, help="abbreviation (OHIO, M-OH, KENT) or school name")
    p.add_argument("--what", required=True, help="the owner's caption: what happened")
    p.add_argument("--game", help="game id, only needed when the Vikings played that opponent twice that season")
    p.add_argument("--player", action="append", help="a player in the clip (repeatable); links to the player card")
    p.add_argument("--poster-at", type=float, help="seconds into the clip for the poster frame")
    p.set_defaults(fn=cmd_add)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("remove")
    p.add_argument("id")
    p.set_defaults(fn=cmd_remove)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
