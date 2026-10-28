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
- [x] M1 Workbook inventory, logo extraction, data-health queue. All 21 items resolved: 20 fixes in `data/fixes.json` (F01-F22, F20/F21 live in `data/aliases.json`), 56 canonical player names + 3 coach names in `data/aliases.json`. Awaiting owner sign-off before M2.
- [x] M2 Clean data tables + build scripts (build_data.py, validate.py: 76 checks passing). All queue items resolved; awaiting owner sign-off.
- [x] M3 Design system: palettes approved 2026-10-26; shell (header/nav/banner/footer, program band + tabs) built. Awaiting owner sign-off.
- [x] M4 Program / season / game / player pages: 1,158 pages (program sections, 42 season pages, 209 game pages, 886 player cards, searchable index). Awaiting owner sign-off.
- [x] M5 Almanac (almanac/, almanac/<year>/, almanac/awards/), Records Book (records/), Rivalry Hub + Coaches' Cup (rivalry/), Hall of Fame (hall-of-fame/). Class of 2037 inducted: Fannin, Nwangwu, Okoronkwo, Molinaro, Reece, Ladd. Awaiting owner sign-off.
- [x] M6 Front page: champion masthead, awards showcase (year picker, CSU winners first + spotlit), Road to next season (phase tracker + 4 teasers that unlock from logged data). Split Decision and highlight-reel modules render only when columns/clips exist (templates _split_decision_teaser.html / _highlight_reel.html to be written in M7 / M10). Awaiting owner sign-off.
- [x] M7 Split Decision: approved 2026-10-27. All 209 columns (2024-2037) written, fact-checked and approved season by season; continuity log complete through 2037. Data fixes F24-F26 were approved during the backfill.
- [~] M8 Games (started 2026-10-27): spec section 11 (Trivia, Playerdle, Word search, Higher/Lower, Grid puzzle, Games hub; all in-browser, personal stats in localStorage with fallback).
- [ ] M9 Road to 2038, Record Watch, phase tracker
- [ ] M10 Clips pipeline, print mode, accessibility, QA
- [ ] M11 Deploy, README, hand-off
- [ ] **Final task (owner request, 2026-10-26):** produce a corrected COPY of the latest tracker (`source/corrected/<date> CSU Vikings Tracker (corrected).xlsx`) with every approved fix from `data/fixes.json` and every alias from `data/aliases.json` applied, plus a "Valhalla Changes" sheet listing sheet / cell / old value / new value / fix id, so the owner can copy-paste the edits into the live spreadsheet. Never modify the original or any dated copy in `source/`.

## Decisions log (approved by the owner after the spec)
- 2026-10-26: Project lives at `C:\Users\Owner\Documents\valhalla-archive` (not the OneDrive Desktop, to avoid sync clashes with Git).
- 2026-10-26: `source/` is git-ignored. Tracker copies are never pushed to the public repo.
- 2026-10-26: Source priority for games (F05): Playoff Tree decides playoff scores, champions and round names; Conference Champions decides other teams' title games; Schedule is used only for CLEV games.
- 2026-10-26: Coach display names: Josh Dolan, Tim Slocombe, Joe Snyderwine.
- 2026-10-26: Palettes approved: CLEV "Valhalla Forest" (#024731, steel, gold; condensed caps; chamfered corners), OHIO "Bobcat Green" (#00694E, cream, tan; slab serif; rounded), M-OH "RedHawk" (#B61E2E, black, white; wide italic caps; diagonal cuts). Archive chrome: ink/bone/brass, Source Serif 4 + Inter.
- 2026-10-26: Static pages are generated at build time (one HTML page per program/season/player/game) for real titles and share previews; GitHub Actions will build and deploy.
- 2026-10-26: Records Book = the tracker's Records sheet as entered + a separate CLEV "computed from the stats" bests list (F12).
- 2026-10-26: Don't publish the Awards-sheet trophy photos (auction watermarks); design our own award marks.
- 2026-10-26: Owner context for Split Decision color (use lightly, never as fact): the 2035 title-game loss (M-OH 73, CLEV 70) still stings ("sour grapes"); "funky stuff happened in-game".

## Workbook facts learned in M1 (see data/data-health.md for the full picture)
- Python: run scripts as `py -P scripts/<name>.py` (openpyxl + pillow installed with `--user`; `-I` would hide them).
- Sheet "Coach Tim Slocombe " has a trailing space in its name.
- Only CLEV has schedule, stat tables, depth chart, recruit lists, graduates and transfers. All three coach sheets have the same fields; columns sit in slightly different places.
- Stats tabs use real Excel tables (4 per tab: passing, rushing, receiving, kicking). Conference Champions has 15 Excel tables (2024-2038; the first has no year in its title).
- Standings blocks (top 4 each) in order: AAC, ACC, Big 12, Big Ten, C-USA, Independents, MAC, Mountain West, Pac-12, SEC, Sun Belt. Row 3 = national champion, row 4 = runner-up.
- Recruiting block year = the recruiting cycle; those players arrive the NEXT season (Amar'e Hocker is in the 2024 block and was a 2025 FR). The 2037 block (which adds a "Stage" column) is the class now being recruited for 2038 and is empty: it fills during the Final Recruiting phase.
- Recruiting summary rows 41-43 (2024 at C-H, 2025 at K-P) are CLEV, M-OH, OHIO (identified by logos). 2029-31 summaries are copies of 2025.
- Depth chart cells are "Name - OVR"; bold = 90+, italic = drafted, * = transfer. Coaching staff (HC/OC/DC) with footnotes sits in rows 25-31.
- Playoff Tree: one 16-row block per year starting at row 2 (2023) in a fixed bracket layout; logos overlay the cells.
- Logos: `site/assets/logos/<ABBR>.png` (resized to 256px), conference marks in `site/assets/conferences/`. Team colors in `data/source-meta/team-colors.json`.

## Website build (M3)
- `site/` is SOURCE: `templates/` (Jinja2), `assets/` (css: tokens.css + base.css; js/site.js; logos; img), `design/` (style guide, noindex).
- `py -P scripts/build_site.py` renders into `_site/` (git-ignored). `BASE_PATH=/valhalla-archive/` for the GitHub Pages build; default `/` for local.
- Local preview: `py -m http.server 8037 --bind 127.0.0.1 --directory _site` then http://localhost:8037/ (also in `.claude/launch.json`).
- Nav only links sections that exist (no dead links). Program pages set `data-program` on <body> to re-theme; Archive chrome stays constant.
- Program URLs: programs/cleveland-state/, programs/ohio/, programs/miami-oh/. Sections: seasons/, leaders/, honors/, titles/, plus CLEV-only records/, recruiting/, departures/, transfers/. Seasons: programs/<slug>/<year>/. Games: games/<id>/. Players: players/<id>/ and players/ (search).
- Templates: base.html -> program_layout.html (band + tabs) -> section templates; components in assets/css/components.css. Jinja helpers: team(), plink(), fmt(), stars(), season_href(), game_href().
- Link check: `py -P scripts/check_links.py` (must report 0 broken).
- Hall of Fame: eligibility computed in build_data.py (table hall_of_fame); votes in data/hof-decisions.json via `py -P scripts/hof_review.py [decide "<name>" yes|no]`.
- Coaches' Cup (my format, owner may change): 8 categories, 3/2/1 points, ties share the higher score.
- Fonts load from Google Fonts for now; self-host before launch (M10).

## Split Decision (M7)
- Bible: content/split-decision/character-bible.md (approved). Continuity log: content/split-decision/continuity.md (update every season).
- Columns: content/split-decision/columns/<season>/<game-id>.md (front matter: game, headline, pierogi for wins). Check with `py -P scripts/columns.py check <season>` (0 errors required).
- Facts box is generated from data at build time. Pages: split-decision/ and split-decision/<game-id>/; game pages link to their column; front page shows the latest.

## Data model and build (M2)
- Full table list and conventions: [docs/data-model.md](docs/data-model.md).
- Build: `py -P scripts/build_data.py` (newest `source/*.xlsx`, or pass a path). Writes `data/tables/*.json`, `data/snapshot/*.json` (raw cell values, for diffs), `data/build-report.md`.
- Validate: `py -P scripts/validate.py` writes `data/validation-report.md` and exits 1 on any failure. Add a check whenever the owner approves a new fix.
- Fixes are applied in code by fix id (search `FIXES[` in build_data.py). A new fix in fixes.json needs matching code.
- Owner-set inputs not in the tracker: `data/site-control.json` (season + phase), `data/reference/teams.json` (abbreviation -> school).

## Update workflow
To be written when `/update-archive` is built (see spec section 13).
