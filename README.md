# The Valhalla Archive

The official unofficial almanac of a College Football 25 dynasty: the Cleveland State Vikings, the Ohio Bobcats and the Miami (OH) RedHawks.

**Live site: https://captiancernal.github.io/valhalla-archive/**

> Unofficial fan site. Not affiliated with Cleveland State University, any other school, EA Sports or the NCAA. All dynasty content is fictional. Team names and logos belong to their schools and appear here for non-commercial fan use only.

## What's in it
- **Programs:** every season, leaders, honors, titles and postseason for all three programs, plus records, recruiting, draft and transfers for the Vikings.
- **Seasons, games and players:** a page for every season, every Vikings game and every player in the tracker (about 1,400 pages in all).
- **League Almanac:** national champions, playoff brackets, conference champions, AP polls, awards and All-Americans for every year.
- **Records Book, Rivalry Hub (with the Coaches' Cup) and the Hall of Fame.**
- **Split Decision:** two fictional columnists, one optimist and one skeptic, on every Vikings game.
- **Games:** Archive Trivia, Higher or Lower, Playerdle, The Grid and printable Word Searches, all built from the dynasty's data.
- **Road to next season:** offseason phase tracker, Record Watch, departing seniors, projected depth chart and teasers that unlock as data is logged.
- **Highlights:** in-game clips, on their game and player pages.
- **Print view:** a quiet toggle in the footer for clean printouts and PDFs.

## Where things live
- **This repository** holds the website: build scripts, page templates, the cleaned data tables and the columns.
- **The tracker** (the owner's spreadsheet) is the only source of facts. It is never uploaded here and never edited; the build reads a dated copy on the owner's computer.
- **Google Drive** holds what doesn't belong online: dated tracker downloads, raw clips, PDFs and backups.

| Folder | What's in it |
|---|---|
| `data/` | Clean data tables built from the tracker, approved data fixes (`fixes.json`), name spellings (`aliases.json`), site settings |
| `content/split-decision/` | The Split Decision columns, character bible and continuity log |
| `content/clips/` | Compressed highlight clips and their captions (`clips.json`) |
| `scripts/` | Tools that read the tracker, check the data and build the site |
| `site/` | Page templates, styles, scripts, fonts and logos |
| `docs/` | The project plan, the data model and the owner's hand-off guide |
| `.claude/commands/` | The `/update-archive` and `/new-season` commands for Claude Code |

## How it's built and published
Static pages are generated with Python (Jinja2 templates) from the tables in `data/tables/`. Every push to `main` runs the **Build and publish the site** workflow, which validates the data, fact-checks the columns, builds the site, checks every link and publishes to GitHub Pages. If any check fails, nothing is published and the live site stays as it was.

To build it yourself (Python 3.14):

```bash
pip install -r requirements.txt
python -P scripts/validate.py
python -P scripts/build_site.py
python -m http.server 8037 --bind 127.0.0.1 --directory _site
```

Then open http://localhost:8037/.

Updating from a new tracker download is done with Claude Code's `/update-archive` command; see [docs/HANDOFF.md](docs/HANDOFF.md).

## Credits
- Fonts: Inter, Source Serif 4, Barlow Condensed, Zilla Slab and Archivo, all under the SIL Open Font License 1.1 (licenses in `site/assets/fonts/licenses/`).
- Built with Claude Code.
