---
description: Roll The Valhalla Archive forward to a new season (run once, when the first game of the new season is in the tracker)
---

# /new-season

The dynasty has started a new season. Roll the site's structure forward so the new season's games, stats and columns have a home. Read `CLAUDE.md` first; its hard rules apply (plain English, one question at a time with a recommended default, never invent facts, tracker is read-only, ask before pushing).

**When to run it:** once per season, when the owner has logged the first game(s) of the new season in the tracker. Offseason updates (recruiting, departures, transfers, preseason) are just `/update-archive`. If you're not sure the new season has started, ask.

Below, N is the season that just ended (now `current_season` in `data/site-control.json`), and N+1 is the new one.

## 1. Confirm the new season is in the tracker

1. Make sure the newest tracker copy is in `source/` (see `/update-archive` step 1).
2. Open it read-only and confirm the new season exists: N+1 rows on the Schedule sheet with at least one result, and on the three coach sheets. Report what you found in one or two lines.

## 2. Check that the data builder reads the new season's blocks

The tracker grows by year. For N+1, check each of these and make `scripts/build_data.py` read them if it doesn't already (show the owner what you changed, and keep every existing check passing):
- an `N+1 Stats` tab (read by name; usually works as is)
- a new Excel table on Conference Champions, a new block on CFB Playoff Tree (16 rows per year), a new column on Standings and AP Top 25
- a new block on Recruiting (the N+1 recruiting cycle, for the class arriving in N+2)
- Graduates, Transfers and Depth Chart entries for the new year

Then run `py -P scripts/build_data.py` and `py -P scripts/validate.py`. Treat new data problems exactly like `/update-archive` step 3 (one question at a time).

## 3. Roll the site settings forward

Edit `data/site-control.json`:
- `current_season`: N+1
- `phases`: `["N+1 Season", "Season Recap", "Final Recruiting", "Player Departures and Draft", "Transfer Window", "N+2 Preseason"]` (with real years)
- `current_phase`: `"N+1 Season"`
- `phase_display`: ask the owner; recommend "N+1 Season".

Ask the owner to confirm before saving (one question).

## 4. Split Decision for the new season

1. In `content/split-decision/continuity.md`, add a section for N+1 and carry forward anything that changes with the calendar (for example Mickey's jersey: one new number per season, as the log says).
2. Check `content/split-decision/character-bible.md` for any life-timeline beats due in N+1 and mention them to the owner.
3. Draft columns for the new season's games as in `/update-archive` step 6.

## 5. Check the in-season look (important the first time)

The site was built during an offseason, so a season in progress hasn't been seen with real data yet. After `py -P scripts/build_site.py`, preview and check each of these with the owner:
- the champion banner and front-page masthead (there's no N+1 champion yet; they should keep showing season N's champion until the title game is played)
- the front-page "Road to" section and the Road page (with phase "N+1 Season", Record Watch compares players against records mid-season)
- the N+1 season page with a partial schedule
- program pages, Coaches' Cup and Records Book with a season in progress

Fix anything that reads oddly. Ask one question at a time if something needs the owner's preference. Note in `CLAUDE.md` what you changed, so later seasons go smoothly.

## 6. Finish like an update

Run `/update-archive` steps 7-10: Hall of Fame vote if anyone became eligible, rebuild and run every check (`check_links`, `validate`, `spot_check`), preview, then commit. Ask before pushing.
