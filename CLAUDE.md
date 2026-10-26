# CLAUDE.md: The Valhalla Archive

Notes for Claude. Read this first in every session.

## What this is
A static GitHub Pages fan site for the owner's College Football 25 dynasty: the Cleveland State Vikings (CLEV) plus two friends' programs, OHIO and M-OH, covered on equal footing. **The full spec, with every locked decision, is in [docs/spec-v1.md](docs/spec-v1.md).** Read it before starting any milestone.

## Hard rules (short version; the spec has the full list)
- The owner is new to Claude Code and GitHub. Explain in plain English, give one step at a time, ask one question at a time, and always offer a recommended default.
- Never invent stats, scores, records or names. Facts come only from the workbook.
- The Excel file is read-only input. Never edit or write back to the owner's tracker.
- Never change data silently. Ask about each data fix one at a time, and record approved fixes in `data/fixes.json` and name aliases in `data/aliases.json`.
- Stop for approval after each milestone with a preview and a summary.
- Commit often. Ask before anything destructive and before every push.
- The repo is public, so secrets and personal info never go in it.

## Where things are
- GitHub repo: https://github.com/captiancernal/valhalla-archive (public, branch `main`, remote `origin`)
- Future site URL: https://captiancernal.github.io/valhalla-archive/
- Tracker copies: `source/YYYY-MM-DD CSU Vikings Tracker.xlsx` (git-ignored; also archived in Drive under `01 Original Tracker`)
- Google Drive folders: "The Valhalla Archive" with 01 Original Tracker, 02 Clips Source, 03 Print Exports and 04 Backups. Folder IDs are in `CLAUDE.local.md` (git-ignored).
- Backlog (not in v1): [BACKLOG.md](BACKLOG.md)

## Tools on this machine (Windows 11)
- git 2.47, gh 2.102 (signed in as captiancernal), Node 24 / npm 11, Python 3.14 (run it as `py` or `python`; `python3` is not available)
- ffmpeg: NOT installed yet. Install it at M10 (clips pipeline).

## Milestone status
- [x] M0 Setup Day: repo created and linked, folder layout made, Drive folders created, tracker copied to source/
- [ ] M1 Workbook inventory, logo extraction, data-health queue (one fix at a time)
- [ ] M2 Clean data tables + build scripts
- [ ] M3 Design system (palettes need owner approval)
- [ ] M4 Program / season / game / player pages
- [ ] M5 Almanac, Records Book, rivalry hub, Hall of Fame
- [ ] M6 Front page
- [ ] M7 Split Decision (bible, 2024 pilot, backfill)
- [ ] M8 Games
- [ ] M9 Road to 2038, Record Watch, phase tracker
- [ ] M10 Clips pipeline, print mode, accessibility, QA
- [ ] M11 Deploy, README, hand-off

## Decisions log (approved by the owner after the spec)
- 2026-10-26: Project lives at `C:\Users\Owner\Documents\valhalla-archive` (not the OneDrive Desktop, to avoid sync clashes with Git).
- 2026-10-26: `source/` is git-ignored. Tracker copies are never pushed to the public repo.

## Data model
To be written in M2.

## Update workflow
To be written when `/update-archive` is built (see spec section 13).
