# Site Database: data model

Built by `py -P scripts/build_data.py` from the newest tracker copy in `source/`.
Output: one JSON file per table in `data/tables/`. Every row carries a `program` (CLEV, OHIO, M-OH, or another team's abbreviation) where it applies. IDs are stable across rebuilds (made from season, program and names, never from row order).

Inputs besides the workbook:
- `data/fixes.json`: owner-approved data fixes (applied by id; see each entry's `rule`).
- `data/aliases.json`: canonical player and coach names.
- `data/site-control.json`: current season and offseason phase (the owner sets these during each update; they're not in the tracker).
- `data/reference/teams.json`: abbreviation to school name (reference data; owner can correct).

| Table | One row per | Key fields | Source sheets |
|---|---|---|---|
| `site_control` | (single object) | current_season, current_phase, phases, last_updated, source_file | site-control.json + build |
| `programs` | program (3) | id, school, coach, colors, logo, conference, career W-L (F01), titles | coach sheets, Instructions colors |
| `coaches` | coach-season | program, season, role (HC/OC/DC), name, note | coach sheets, Depth Chart staff rows |
| `seasons` | program-season | W, L, conf W-L, conf rank, AP final rank, six leaders (+class for CLEV), team pass/rush yds, PPG, PPG/offense rank, postseason summary | coach sheets, AP Top 25, Playoff Tree, Conference Champions, Schedule |
| `games` | CLEV game | id, season, week/type, opponent, site, CLEV score, opp score, result, bowl/round name, date (2024-27) | Schedule (CLEV only) + Playoff Tree (F05) |
| `playoffs` | playoff game, all teams | season, round, teams, scores, winner | Playoff Tree |
| `conference_championships` | conference title game | season, conference, teams, scores, champion | Conference Champions (F03) |
| `standings` | season-conference-place | top 4 per conference | Standings (F16) |
| `ap_top25` | season-rank | final AP poll | AP Top 25 |
| `national_championships` | season | champion, runner-up, title-game score | Playoff Tree + Standings |
| `player_seasons` | CLEV player-season-category | passing / rushing / receiving / kicking stat lines | YYYY Stats tabs (F04, F09, F10) |
| `players` | player | id, name, programs, positions, position family, home state, recruit stars/rank/cycle, transfer, ratings by season, peak rating, departure, awards, All-American years, records | everything |
| `recruits` | CLEV recruit | cycle, arrival season, nat rank, position, stars (null = not tracked, F14), state, stage | Recruiting |
| `recruiting_classes` | program-cycle | star counts (CLEV from lists), national class rank (2024-25 only, F13) | Recruiting |
| `transfers` | transfer | cycle, arrival season, player, class (F15), position, from, to | Transfers |
| `departures` | departing player | season, class, position, overall, drafted, round | Graduates |
| `depth_chart` | CLEV season-slot-depth | position slot, depth, player, rating (2024-32), projected flag (next season), departing flag | Depth Chart (F17) |
| `awards` | season-award | award, winner, school | Awards |
| `all_americans` | season-slot | unit, position, player, school | All-Americans |
| `records_official` | record | magnitude, duration, type, value, player, year set | Records sheet (F12) |
| `records_computed` | CLEV best | season and career top-10 lists by stat | built from player_seasons (F12) |
| `teams` | team abbreviation | school name, colors, logo file | reference/teams.json + Instructions + logos |
| `clips`, `columns` | clip / Split Decision column | (filled in M7 and M10) | content/ |

Season conventions:
- A **recruiting or transfer cycle** year is the season it was signed; those players arrive the **next** season.
- A **Graduates** block year is the season the player last played.
- The **Depth Chart** block for (current season + 1) is the projected chart.
