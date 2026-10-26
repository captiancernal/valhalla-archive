# The Valhalla Archive: Master Spec (v1)

This is the owner's master prompt, saved word for word as the source of truth for every locked decision. If anything in CLAUDE.md conflicts with this file, this file wins unless the owner has since approved a change (recorded in the "Decisions log" in CLAUDE.md).

---

You are my lead developer, data engineer, designer and head writer. We are building The Valhalla Archive, a professional, living fan website for my College Football 25 dynasty centered on the Cleveland State Vikings (CLEV), with equal-footing coverage of my two friends' programs. Work autonomously and make good decisions, but follow every locked decision below.

## Working agreements (important)

- I have never used Claude Code or GitHub. Explain every setup step in plain English, one step at a time, and wait for me to confirm before the next. Never assume I know a term.
- Ask me one question at a time when you need input. Offer your recommended default with each question.
- Never invent statistics, scores, records or names. Facts come only from the data. Invented color (anecdotes, banter) must never contradict the data.
- Work in milestones (listed at the end). After each, show me a preview, summarize what changed, and stop for my approval.
- Commit to git often with clear messages. Ask before anything destructive or before pushing live.
- Keep a README.md for me (plain English) and a CLAUDE.md for yourself that records these decisions, the data model and the update workflow, so future sessions pick up instantly.

## 1. The project in one paragraph

A GitHub Pages website named The Valhalla Archive that reads like a very professional university athletics site crossed with a Sports-Reference-style almanac. It has an interactive front page, deep season-by-season history, player career cards, a league almanac, records, a rivalry hub among the three coaches, a weekly first-take column called Split Decision, a set of games with personal stat tracking, and a "living" feel driven by an offseason phase tracker and 2038 teasers. The link is public and shareable. Phone and desktop get equal design attention. The name should feel like it could someday support a print edition.

## 2. Locked decisions

| Topic | Decision |
|---|---|
| Name | The Valhalla Archive |
| Hosting | GitHub Pages, static site, public repository (free Pages requires it). Never commit secrets, keys or personal info. |
| Data | Excel in, site out: my tracker stays separate and untouched; for each update I download it and give Claude Code a fresh Excel file, and one command rebuilds the site |
| Database | You build a clean normalized "Site Database" set of data tables from each Excel file I show you. The Excel file is the database; there is no Google Sheet, and nothing writes back to my tracker |
| Data entry | Only I enter data, for all three programs |
| Audience | Me, my two friends, and anyone with the link |
| Coverage | Equal profiles, records and information for all three programs. My friends track fewer stats, so the stats that exist must be prominent and use the screen well. |
| Look | Full re-theme per program page (CSU, OHIO, M-OH each wear their own colors) |
| Devices | Phone and desktop equally |
| Highlights | MP4 clips I upload, stored in the repo, compressed |
| Print | A discreet "print mode" (see section 9). No print clutter on the main screens. |
| Game stats | Personal, in-browser only (streaks, accuracy). No shared leaderboard in v1. |
| Data cleanup | Ask me about each fix one at a time |

## 3. The source data (what I found; verify all of it)

The workbook has 31 sheets: Instructions, Logos, Schedule, Depth Chart, three coach sheets (Coach Josh Dolan = CLEV, Coach Tim Slocombe = OHIO, Coach Joe Snyderwine = M-OH), Records, Hall of Fame, Conference Champions, Standings, AP Top 25, CFB Playoff Tree, All-Americans, Awards, Recruiting, Graduates, Transfers, and one Stats sheet per season, 2024 to 2037. It also contains about 186 embedded images (team logos) that you must extract.

- Time span: the league baseline is 2023; my CLEV coaching years are 2024 to 2037 (14 seasons).
- CONFIRMED: 2037 is the season just completed. CLEV won the 2037 national title (16-1), and the tracker's 2038 columns are empty. I have confirmed this: it is the 2037 offseason.
- Layouts are wide blocks laid side by side by year, not tidy tables. Standings, AP Top 25, Awards, All-Americans, Recruiting, Graduates, Transfers and Depth Chart all repeat per year across columns. Parse them by block.
- Coach sheets hold the season record, conference record and rank, and team leaders (passing, rushing, receiving, tackles, sacks, INTs) plus team passing yards, rushing yards, PPG and PPG rank.
- Tim's and Joe's coach sheets have fewer fields (record, conference rank, passing/rushing/receiving leaders at least). Inventory exactly what exists for each program and design to it. Do not fabricate the rest. The spreadsheet is the only quantitative data that exists for any program.
- Stat sheets have passing, rushing and other tables per season with fields like YDS, COMP, ATT, TD, INT, RATE, YPA, LONG, SACKS, CAR, YPC, YPG, FUMB, YAC, 20+.
- Records sheet columns: Player, POS, Magnitude (NCAA, BIG 12, CLEVELAND STATE), Duration (Game, Season, Career), Type, Record, Year Set.

Known data problems (log them all in a data-health queue and ask me about each, one at a time):

- Numbers stored as text (for example '10', '3,817') and mixed formats
- #DIV/0! and #REF! cells, and the stale Career Record cell on my coach sheet (shows 41-11; by my count the true total is 180-29)
- The 2026 stats tab header says "2025 SEASON STATS"; the second table on the 2037 tab says "2036 SEASON STATS"; the 2029 tab has a stray "2027" label
- Name variants, for example Jacob Rizy / Rizi, Kenny Tonges / Tongues, Marquel Bahktiari / Bakhtiari / Bakhtiari; Baraka Nwangwu spelling; "Josh Dolan" vs "Joshua"
- Inconsistent class labels (SR (RS), SR, FR (RS)) and inconsistent position labels (RB vs HB, RG vs OG)
- Stray cells in odd places (the coach sheet has text at far-right rows)

Data-fix rule: never change my data silently. Present each problem with your proposed fix, wait for my yes or no, then record the approved decision in data/fixes.json (and a name-alias table at data/aliases.json) so the same fix applies on every future rebuild. Batch similar items only if I say so.

## 4. Folders and Google Drive

Google Drive (create via the Drive connector if available, otherwise walk me through creating them):

```
The Valhalla Archive/
  01 Original Tracker/      (dated Excel downloads, never edited)
  02 Clips Source/          (raw game captures)
  03 Print Exports/         (PDFs saved from print mode)
  04 Backups/               (dated snapshots of the data folder)
```

Local project and repo:

```
valhalla-archive/
  CLAUDE.md  README.md
  .claude/commands/          (update-archive.md, new-season.md)
  source/                    (original xlsx, git-ignored if large)
  data/                      (fixes.json, aliases.json, sheet snapshot, built JSON)
  content/split-decision/    (character-bible.md, columns/)
  content/clips/             (compressed MP4s, posters, clips.json)
  scripts/                   (extract, validate, build, compress-clip)
  site/                      (the static website that Pages serves)
  .github/workflows/         (Pages deploy)
```

Data access: the Excel file is the database. I will show you the .xlsx for each update; read it directly, never edit it, and never write back to it. Archive every file I show you, by date, in source/ (and in 01 Original Tracker in Drive) so any rebuild can be reproduced. No Google connector is needed to build the site; use Drive only to create and organize the folders if a connector is available. Credentials never go in the repo.

## 5. The data layer (clean tables built from the Excel file)

From the Excel file, build normalized tables (JSON files in the data folder), one tidy table each, with stable IDs and a program column (CLEV, OHIO, M-OH) everywhere: Site Control (current_season, current_phase, last_updated), Programs, Coaches, Seasons (record, conference record and rank, team stats, leaders), Games, PlayerSeasons (all stat rows), Players (ID, canonical name, position, home state, recruit stars and rank where known), Recruits, Transfers, Departures (graduates and draft, with round), DepthChart, Awards, AllAmericans, Records, Championships (national and conference), AP Top 25, Playoffs, Clips, Columns.

Input workflow (decided): the Excel file is the database. I keep my original tracker separate and never connect it to anything, so nothing in it can be overwritten or deleted. For each update I show you a fresh download of it. Treat every copy as read-only input and never write to my original. The Site Control values (current season and phase) are not in the tracker, so ask me for them during each update.

## 6. Pages and features

Per program (CSU, OHIO, M-OH), each with its own theme: overview with big prominent tracked stats; season-by-season table (record, conference finish, rank, leaders); season pages; game logs where schedule data exists; roster and depth chart where it exists; stat leaders and career leaders; recruiting classes; draft and graduates; transfers; records; awards and All-Americans; championships and bowl history.

Adaptive layouts: each program page renders modules by the data that exists for that program. Where a program has fewer stats, enlarge and elevate what is tracked (record, ranks, leaders, titles) so no page looks empty. Never leave placeholder boxes.

Players: a full career card for every player: yearly stats, rating progression where depth-chart data exists, recruit info (stars, rank, state), transfer path, graduation or draft result, awards and All-American honors, records held. Searchable index.

League Almanac: national champions and runners-up by year, playoff brackets, conference champions, AP Top 25 by year, awards by year (Heisman, Maxwell, Camp, Bednarik, Nagurski, O'Brien, Walker, Biletnikoff, Mackey, Outland, Rimington, Lombardi, Butkus, Thorpe, Groza, Guy), All-Americans, and the Records Book (NCAA, conference, school; game, season, career).

Rivalry hub: head-to-head results among the three coaches built from the data that exists, title tallies (OHIO's 2029-33 run, M-OH's 2034-36 run, CSU's 2028 and 2037), and a "Coaches' Cup" summary.

Hall of Fame: a Ring of Honor. A player is eligible when they left the roster (graduated, drafted or transferred out) as a 90+ overall, won at least one award from the Awards tab, and earned at least one All-American selection (the tracker only lists first-team All-Americans, so any listing counts). Eligibility alone inducts no one: build a selection screen (a review step inside /update-archive) that shows each newly eligible player's career summary and asks me yes or no. Save my decisions in data/hof-decisions.json so nobody is asked twice.

Do not build in v1: a compare-two-players tool and a shared leaderboard (put them in a BACKLOG.md).

## 7. Visual identity

Very professional: editorial athletics-site feel, strong typography, generous data density, excellent tables, subtle motion, high contrast, responsive and accessible.

- Pull each program's colors from the tracker's team-color data and the extracted logos.
- Note: CSU and OHIO are both green-and-white in real life. Give them clearly different secondary colors, type treatment and shape language so pages never feel interchangeable. Show me the three palettes and ask me to approve them before building.
- Each program section has its own header, accent system and logo lockup. The shared Archive chrome (nav, footer) stays constant.

## 8. Front page

Order, top to bottom, is my priority ranking:

1. Awards and honors showcase: latest season's winners as an elegant, interactive gallery with a year selector, CSU winners spotlighted.
2. Split Decision: the latest column with both columnists, plus link to the archive.
3. Highlight reel: the hero-style player of my MP4 clips with captions, muted autoplay loop with tap-to-unmute, lazy loading, and respect for reduced-motion settings.
4. Road to 2038: the offseason phase tracker and teasers.

A slim banner can announce the 2037 national champions. The site must feel alive: "current phase" is read from Site Control. The current phase is Post-Championship Season Recap. Phases: Season Recap, Final Recruiting, Player Departures and Draft, Transfer Window, 2038 Preseason.

## 9. Living features and print mode

Road to 2038 (trailer-style teasers with locked cards that unlock as I log data): returning starters and a projected 2038 depth chart; departing seniors and draft watch; 2038 schedule and rivalry previews; incoming recruit class (cards reveal as I log recruits). Add a Record Watch for 2038 that finds returning players within reach of school, conference or NCAA records and shows how far away they are.

Print mode: a small, unobtrusive toggle (for example in the footer or an overflow menu). Turning it on re-lays out the current page for print (white background, simplified header, page breaks, tables fit). Only in print mode does a Save as PDF button appear. No mention of printing elsewhere. Suggest a 'print edition' style for season recaps, the Records Book and player cards, but keep it modest.

## 10. Split Decision

A weekly first-take column in which two fictional journalists debate the Cleveland State Vikings.

- Mickey Bridges is the believer. "Lil" Ken Hogmanes is the perpetual doubter.
- They are loosely inspired by Skip Bayless and Stephen A. Smith only in strength of conviction. Do not copy catchphrases, mannerisms or real-person details, and never put words in real people's mouths.
- Tone: CSU-focused, sharp, witty, college-bar humor, no profane language, a wide and playful vocabulary. Friendly-but-pointed jabs at OHIO and M-OH are welcome. Because the site is public, keep it clean.
- Character bible first: before writing columns, create content/split-decision/character-bible.md with, for each columnist, full demographics, psychographics, fictional history, anecdotes, speech patterns, recurring bits, wardrobe, physical description and voice, detailed enough for consistent AI-generated video later. Ask me up to five quick questions about their personalities, then show me the bible for approval.
- Column format: headline, game facts box (generated from data only), Mickey's take, Ken's rebuttal, one back-and-forth exchange, and a Final Verdict line. About 300 to 450 words.
- Every CSU game across all 14 seasons gets a column (about 200 columns). Do it in this order: pilot with the 2024 season, get my approval on voice, then backfill one season at a time, with a checkpoint between seasons. Going forward, /update-archive drafts new columns from new game data.
- Columns are saved as files in content/split-decision/columns/ and rendered by the site. Each links to its game and season page.

## 11. Games (first build)

All games use only dynasty data, run entirely in the browser, and store personal stats (plays, streaks, accuracy, best scores) in localStorage with graceful fallback if storage is blocked. Player pools include all three programs.

- Trivia: rounds of 10, graded at the end, categories by program and era, difficulty tiers, a one-line explanation after each answer. Generate questions from the data and review a sample with me.
- Playerdle (player-themed Wordle): guess the mystery player in a limited number of tries. Clues compare attributes (program, position, class, home state, recruit stars, peak rating, seasons played). Daily puzzle plus unlimited practice, with a shareable emoji result.
- Word search: themed grids (a season's roster, award winners, a program's legends) with a printable version.
- Higher/Lower: compare real stat lines and records.
- Grid puzzle (Immaculate Grid style): rows and columns are constraints (program, position, award, class year, home state) and each cell needs a qualifying player.
- A shared Games hub page shows my personal stats across all games.

## 12. Highlight clips

I drop MP4s into content/clips/incoming/. Your workflow: detect new files, ask me to caption each one (season, opponent, what happened), compress with ffmpeg to web-friendly H.264 (target about 720p to 1080p, with a sensible size cap per clip and a total budget that keeps the repo comfortably under GitHub's limits), generate a poster image, and add it to clips.json. Do not use Git LFS (it does not work with Pages). Warn me before the repo gets large.

## 13. The update workflow

Create a Claude Code slash command /update-archive that: (1) reads the Excel file I show you in source/ (always a fresh download of my tracker; never touch the original); (2) validates and walks me through any new data problems one at a time; (3) shows a plain-English summary of what is new; (4) processes new clips; (5) drafts Split Decision columns for new games; (6) runs the Hall of Fame selection screen for newly eligible players; (7) asks me for the current season and phase, then updates Site Control and unlocks teaser cards; (8) regenerates the data tables and the site; (9) opens a local preview; (10) after I approve, commits and pushes so GitHub Pages deploys. Also create /new-season to roll the structure forward to a new season.

## 14. Quality and compliance

- Accessible (keyboard, contrast, alt text, reduced motion), fast on phones, good page titles, descriptions and share-preview images.
- Footer disclaimer: unofficial fan site; not affiliated with Cleveland State University, any other school, EA Sports or the NCAA; dynasty content is fictional.
- Spot-check numbers against the workbook before each milestone (for example the CSU career record, national title years, and a few known season lines).
- A private data-health report lives in the repo's data/ folder, not on a public page.

## 15. Milestones (stop for my approval after each)

- M0 Setup Day walkthrough: GitHub, repo, folders, Drive, tools
- M1 Inventory the workbook, extract logos, present the data-health queue, and resolve fixes with me one at a time
- M2 Build the clean data tables from the Excel file and the build scripts
- M3 Design system: three program themes (I approve palettes), layout shell, nav
- M4 Program, season, game and player pages
- M5 League Almanac, Records Book, rivalry hub, Hall of Fame
- M6 Front page
- M7 Split Decision: bible, 2024 pilot, then season-by-season backfill
- M8 Games
- M9 Road to 2038, Record Watch, phase tracker
- M10 Clips pipeline, print mode, accessibility and QA
- M11 Deploy to GitHub Pages, write the README, and hand-off notes for my first /update-archive
