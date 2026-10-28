# Your guide to running The Valhalla Archive

Everything you need to keep the site up to date, in plain English. You never have to touch code: Claude does the work, and you answer questions and say yes before anything goes live.

**Your live site:** https://captiancernal.github.io/valhalla-archive/

## How it fits together

1. **Your tracker** (the Google Sheet) is the single source of truth. You keep playing and logging there like always. The site never changes it.
2. **This project folder** (`Documents\valhalla-archive`) turns a downloaded copy of the tracker into the website.
3. **GitHub** stores the project online and publishes the site. Every time you approve an update, it rebuilds and publishes the site, usually in about two minutes.
4. **Google Drive** ("The Valhalla Archive" folder) keeps your dated tracker downloads, raw clips, PDFs and backups.

## Your first update, step by step

Do this whenever you've logged new things in the tracker (games, recruits, departures, anything).

1. **Download the tracker.** In Google Sheets: File > Download > Microsoft Excel (.xlsx).
2. **Put the file in the project.** Move it into `Documents\valhalla-archive\source\`. Don't worry about the name; Claude will give it a dated name. Also drop a copy in Drive > The Valhalla Archive > 01 Original Tracker.
3. **Open the project in Claude.** In the Claude app, open the Code tab with the `valhalla-archive` folder.
4. **Type `/update-archive`** and press Enter.
5. **Answer Claude's questions, one at a time.** Each one comes with a recommended answer. Expect these:
   - any new data problems it spots (for example, a number that disagrees between two sheets);
   - captions for any new highlight clips;
   - whether to approve the new Split Decision columns;
   - Hall of Fame votes for newly eligible players;
   - which offseason phase you're in now.
6. **Look at the preview.** Claude opens the updated site on your computer (http://localhost:8037/) and tells you which pages changed.
7. **Say yes to publish.** Nothing goes online until you do. A couple of minutes later the live site has the update.

If you have no new clips or nothing changed in some area, Claude just skips that part.

## Adding highlight clips

1. Record or export the clip from the game.
2. Drop the video file into `Documents\valhalla-archive\content\clips\incoming\`.
3. Run `/update-archive` (or just tell Claude "I added a clip"). Claude asks you for the season, the opponent and what happened, compresses the video and adds it to the Highlights page, the game page and the player cards you name.
4. Afterwards, move your original from `content\clips\originals\` to Drive > 02 Clips Source.

Clips share a 500 MB budget (about 13 minutes of 1080p highlights). Claude warns you at 75%. Short clips of big plays work best.

## When a new season starts

When you've logged the first game of a new season, type **`/new-season`** instead. Claude moves the site to the new season, checks that the tracker's new tabs and blocks are being read, and then finishes like a normal update.

The first time you do this, it'll take a little longer. The site was built during an offseason, so Claude will check the "season in progress" pages with you using your real data and tidy anything that reads oddly.

## Print view and PDFs

At the bottom of any page there's a small **Print view** button. It turns the page into a clean, printable sheet, with a **Save as PDF** button at the top. Season recaps, the Records Book and player cards get a "Print Edition" heading. Save PDFs you want to keep in Drive > 03 Print Exports.

## If something goes wrong

- **The live site never breaks from a bad update.** Before publishing, GitHub re-checks the data, the columns and every link. If anything fails, nothing is published and the old version stays up. Claude reads the error and explains it.
- **You can always ask Claude in plain words**, for example "the 2036 season page looks wrong" or "undo the last update". Claude will explain the options and ask before doing anything that can't be undone.
- **Everything is saved in GitHub's history**, so any earlier version of the site can be brought back.

## Backups

- GitHub is a full backup of the project (except your tracker copies, which stay private).
- Your tracker downloads go in Drive > 01 Original Tracker.
- Now and then (for example after each season), you can zip the `Documents\valhalla-archive` folder into Drive > 04 Backups. This also covers the tracker copies in `source\`.
- There's also a one-time backup from before your email was hidden: `Documents\valhalla-archive-backup-2026-10-28.bundle`. It contains your Gmail address, so keep it on your computer only. You can delete it once the site is live and you're happy.

## Things only you can do

- Download the tracker and copy files into Drive (Claude can't reach your Google Sheet).
- Say yes before anything is published.
- Change settings on your GitHub account.

## Still open

- **Corrected tracker copy:** you asked for a corrected copy of the tracker with every approved fix applied, plus a "Valhalla Changes" sheet listing each change, so you can copy the edits into your live sheet. That's the final task after launch.
- **2038 depth chart:** a few names appear twice (Quincy Reddick twice at center, Johnnie Floyd twice at CB3). If those are typos, fix them in the tracker and they'll clear up on your next update.

## Quick reference

| You want to... | Do this |
|---|---|
| Update the site from the tracker | Download the .xlsx into `source\`, then `/update-archive` |
| Start a new season | `/new-season` |
| Add a highlight clip | Drop it in `content\clips\incoming\`, then `/update-archive` |
| Change the offseason phase | `/update-archive` asks you every time |
| Print or save a PDF | "Print view" in any page's footer |
| See the site before publishing | Claude opens http://localhost:8037/ during every update |
