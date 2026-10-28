---
description: Update The Valhalla Archive from a fresh download of the tracker (validate, review, build, preview, then publish with the owner's OK)
---

# /update-archive

You are updating The Valhalla Archive from a new copy of the owner's tracker. Read `CLAUDE.md` first; its hard rules apply to every step. The short version:

- The owner is new to this. Plain English, one step at a time, **one question at a time**, always with a recommended default (use the AskUserQuestion tool).
- **Never invent** stats, scores, records or names. Facts come only from the tracker.
- The tracker is **read-only**. Never edit or write back to any `.xlsx` the owner gives you.
- **Never change data silently.** Every new data problem is one question to the owner.
- **Ask before pushing.** Publishing is the last step and needs a clear yes.

Keep the task list current as you go. If any step fails, stop, explain it simply and ask what to do; don't route around it.

## 1. Get the new tracker copy

1. Download the live Google Sheet: `py -P scripts/pull_tracker.py pull`. It saves `source/YYYY-MM-DD-HHMM CSU Vikings Tracker.xlsx` (read-only sign-in; it never writes to the sheet).
   - `DOWNLOADED`: carry on with the new file.
   - `UNCHANGED`: the sheet hasn't changed since the last download. Tell the owner and ask whether there's something else to update (clips, phase, Hall of Fame) or whether to stop. Recommend stopping if they expected new games.
   - The browser may open for a Google sign-in (the saved sign-in lapses about once a week while the Google app stays in "Testing"). The owner signs in themselves; never type a password for them.
   - Exit code 2 (setup missing) or any error: explain it and use `py -P scripts/pull_tracker.py status`. As a fallback, the owner can still download the sheet by hand (File > Download > Microsoft Excel); copy that file into `source/` with the same `YYYY-MM-DD-HHMM` naming. Never move or rename the owner's original.
2. If the owner instead gave you a file somewhere else (Downloads, an attachment), copy it into `source/` with that naming.
3. The downloaded copy stays in `source/` (git-ignored). The owner's occasional folder zip into Drive > 04 Backups covers it; no manual Drive copy is needed each time.

## 2. Build the data and find what's new

1. Keep the old tables for comparison: copy `data/tables/` to a scratch folder outside the repo.
2. Run `py -P scripts/build_data.py`. Read `data/build-report.md`.
3. Run `py -P scripts/validate.py`. Any failure is either a pipeline bug (fix it) or a new data problem (go to step 3).
4. Compare old vs new tables to list what changed: new games and scores, new seasons, new stat lines, awards, All-Americans, recruits, departures, transfers, depth chart, records, standings.

## 3. Walk through new data problems, one at a time

For each new problem (a cell that disagrees with another sheet, a misspelled name, a total that doesn't add up, a missing value):
- Explain it in plain English with the exact sheet and cell, what it says, and what the other source says.
- Ask one question with a recommended fix. Options usually: apply the fix / leave as entered / "I'll give you the right number".
- Record approved fixes in `data/fixes.json` (next free F-number, `approved` date, sheet/cell/old/new) **and** add matching code in `build_data.py` (search `FIXES[`), plus a check in `validate.py`. Name spellings go in `data/aliases.json`.
- Never batch similar items unless the owner says so.
- Rebuild and re-validate after each approved fix. Then run `py -P scripts/spot_check.py`: 0 unexplained differences required. If an approved fix explains a new difference, add it to `EXPLAINED` in that script.

## 4. Summarize what's new (plain English)

A short list the owner can scan, for example: "4 new Vikings games (3-1), Pashos passed 7,000 yards, 2 new All-Americans, the 2038 recruiting class has 12 commits so far." Facts only from the data.

## 5. Process new highlight clips

1. Run `py -P scripts/clips.py status`. If nothing is waiting in `content/clips/incoming/`, say so and move on.
2. For each new video, ask the owner (one clip at a time): season, opponent and what happened (in their words), and optionally which players are in it. Never write the caption yourself.
3. Run `py -P scripts/clips.py add "<file>" --season N --opponent ABBR --what "..." [--player "Name"]...`. Report the size and the budget line. If the budget warning appears, tell the owner before adding more.
4. Remind them to move the originals from `content/clips/originals/` to Drive > 02 Clips Source.

## 6. Draft Split Decision columns for new Vikings games

1. Read `content/split-decision/character-bible.md` and `content/split-decision/continuity.md` in full.
2. Write one column per new CLEV game into `content/split-decision/columns/<season>/<game-id>.md`, following the bible and the continuity rules (no per-game player stats; season totals only in a season's final column; every "N-N" must be a real score or record).
3. Run `py -P scripts/columns.py check <season>`: 0 errors required. Fact-check each column against the data yourself as well (streaks, head-to-head counts, records at that point).
4. Show the owner the new headlines and ask for approval (one question: approve all / show me one first). Update `continuity.md` with anything new you used.

## 7. Hall of Fame vote

Run `py -P scripts/hof_review.py`. For each newly eligible player, show the career summary and ask **one player at a time**: induct or not? Record with `py -P scripts/hof_review.py decide "<name>" yes|no`. Eligibility alone inducts no one.

## 8. Season and phase

Ask the owner which phase the dynasty is in now, offering the phases in `data/site-control.json` with the likely next one as the recommendation. Update `current_phase` (and `phase_display` if they want a different headline). Locked teaser cards on the front page and the Road page open by themselves when their data exists; tell the owner which ones opened.

If the tracker now has games for a season after `current_season`, the dynasty has moved into a new season: stop and suggest running `/new-season` first.

## 9. Rebuild and preview

1. `py -P scripts/build_site.py`, then `py -P scripts/check_links.py` (0 broken), `py -P scripts/validate.py` (all pass), `py -P scripts/spot_check.py` (0 unexplained).
2. Start the local preview (the "site" entry in `.claude/launch.json`, http://localhost:8037/) and open the pages that changed: the front page, the newest season page, any new player cards, the Road page.
3. Tell the owner what to look at, with links. Wait for their OK. Make any changes they ask for, then rebuild.

## 10. Commit and publish (only after a clear yes)

1. Commit with a clear message (for example "Update through 2038 week 4: 4 games, 4 columns, 2 clips"). The repo's git config already uses the private GitHub address; never commit with any other email.
2. Ask: "Ready to publish? This pushes to GitHub and the live site updates in about two minutes." Recommended answer: publish.
3. On yes: `git push origin main`. Then watch the "Build and publish the site" run (`gh run watch` or `gh run list --limit 1`). If it fails, read the log (`gh run view --log-failed`), explain, fix, and ask again before re-pushing.
4. When it's green, give the owner the live link: https://captiancernal.github.io/valhalla-archive/
5. Remind them (one line) of anything left for them: Drive copies of the tracker and clip originals.
