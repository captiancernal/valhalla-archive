"""Extract team logos from the tracker's Logos sheet and team colors from the Instructions sheet.

Read-only on the workbook. Writes:
  <out_dir>/logos/<ABBR>.<ext>   one logo per team abbreviation
  <out_dir>/team-colors.json     fill and font colors per abbreviation

Usage: py -P scripts/extract_logos.py "<file>.xlsx" <out_dir>
"""
import hashlib
import json
import os
import sys

import openpyxl


def color_hex(c):
    if c is None or c.type != "rgb" or not isinstance(c.rgb, str):
        return None
    rgb = c.rgb[-6:]
    return None if rgb in ("000000",) and c.rgb.startswith("00") else "#" + rgb


def main(path, out_dir):
    wb = openpyxl.load_workbook(path)  # need images and styles
    logos_dir = os.path.join(out_dir, "logos")
    os.makedirs(logos_dir, exist_ok=True)

    ws = wb["Logos"]
    abbr_at = {}
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.strip():
                abbr_at[(c.row, c.column)] = c.value.strip()

    saved, unmatched, seen_hash = {}, [], {}
    for img in ws._images:
        a = img.anchor._from
        r, col = a.row + 1, a.col + 1  # 1-based
        # Logo sits to the right of its abbreviation on the same row (A->B/C, D->E/F)
        abbr = None
        for dc in range(1, 4):
            abbr = abbr_at.get((r, col - dc))
            if abbr:
                break
        data = img._data()
        h = hashlib.sha1(data).hexdigest()[:10]
        ext = (img.format or "png").lower()
        if not abbr:
            unmatched.append({"row": r, "col": col, "hash": h})
            continue
        if abbr in saved:
            if saved[abbr]["hash"] != h:
                saved[abbr].setdefault("alternates", []).append(h)
            continue
        fn = f"{abbr}.{ext}"
        with open(os.path.join(logos_dir, fn), "wb") as f:
            f.write(data)
        saved[abbr] = {"file": fn, "hash": h, "row": r, "col": col}
        seen_hash.setdefault(h, []).append(abbr)

    # Team colors: the Instructions sheet lists each abbreviation in a colored cell
    colors = {}
    wi = wb["Instructions"]
    for row in wi.iter_rows(min_row=24):
        for c in row:
            if isinstance(c.value, str) and c.value.strip() and len(c.value.strip()) <= 5:
                fill = c.fill.fgColor if c.fill and c.fill.fill_type else None
                colors[c.value.strip()] = {
                    "fill": color_hex(fill) if fill else None,
                    "font": color_hex(c.font.color) if c.font and c.font.color else None,
                    "cell": c.coordinate,
                }

    shared = {h: a for h, a in seen_hash.items() if len(a) > 1}
    with open(os.path.join(out_dir, "team-colors.json"), "w", encoding="utf-8") as f:
        json.dump(colors, f, indent=2)
    with open(os.path.join(out_dir, "logos.json"), "w", encoding="utf-8") as f:
        json.dump({"logos": saved, "unmatched": unmatched, "same_image_multiple_teams": shared}, f, indent=2)

    print(f"logos saved: {len(saved)}  unmatched images: {len(unmatched)}  shared images: {shared}")
    for t in ("CLEV", "OHIO", "M-OH"):
        print(t, saved.get(t), colors.get(t))


if __name__ == "__main__":
    main(*sys.argv[1:])
