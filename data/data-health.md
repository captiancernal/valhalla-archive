# Data-health report (private: not shown on the site)

Source: `source/2026-10-26 CSU Vikings Tracker.xlsx` (inventoried 2026-10-26).
Every item below waits for the owner's yes/no. Approved fixes go in `data/fixes.json`; name decisions go in `data/aliases.json`.

Status key: OPEN, APPROVED, REJECTED, NOTE (no decision needed)

## What the workbook covers (verified)

| Data | CLEV | OHIO | M-OH |
|---|---|---|---|
| Season record, conf record, conf rank (2024-37) | yes | yes | yes |
| Six team leaders + team pass/rush yards, PPG, PPG rank | yes | yes | yes (last column is "OFF RNK") |
| Game-by-game schedule | yes (all 14 seasons) | only games vs CLEV and some title games | only games vs CLEV and some title games |
| Player stat tables (pass/rush/rec/kick) | yes | no | no |
| Depth chart with ratings | yes (ratings 2024-32 only) | no | no |
| Recruit lists | yes | no | no |
| Recruiting class summary (stars, national rank) | 2024-25 | 2024-25 | 2024-25 |
| Graduates & draft | yes | no | no |
| Transfers | yes (incoming) | 1 entry | no |
| Awards, All-Americans, Standings, AP Top 25, conference title games, playoff brackets | league-wide | league-wide | league-wide |

Correction to the spec: Tim's and Joe's coach sheets have the **same** fields as Josh's (all six leaders and team stats), not fewer.

Logos: 150 team logos + 11 conference marks extracted. Team colors come from the Instructions sheet (CLEV #024731, OHIO #00694E, M-OH #B61E2E). Logo files total ~12 MB, so shrink them before launch.

## Queue

| # | Status | Problem | Proposed fix |
|---|---|---|---|
| 1 | APPROVED (F01) | Career Record cells are stale on all three coach sheets: CLEV shows 41-11, OHIO 46-21, M-OH 51-19. Summing the season rows gives CLEV 180-29, OHIO 175-34, M-OH 174-32. | Ignore the career cells; always compute career record and win % from the season rows. |
| 2 | APPROVED (F02) | 2034 Big 12 title game. Schedule says OHIO vs M-OH 57-42 (M-OH won). Conference Champions says M-OH vs **CLEV** 57-42. Coach sheet says CLEV 15-2, but the Schedule only adds up to 15-1. | Treat it as a CLEV loss to M-OH, 57-42, in the 2034 Big 12 title game (CLEV 15-2). |
| 3 | APPROVED (F03) | 2029 Conference Champions table: Big 12 and MAC labels are swapped (CLEV vs M-OH on the "MAC" row; BUFF vs MASS on the "B12" row). | Swap the two labels for 2029. |
| 4 | APPROVED (F04) | 2032 receiving: Sam Fatafehi 13 catches for 2,219 yards (long 44, 170.7 per catch). Impossible. | Read as 219 yards (16.8 per catch). Or the owner gives the real number. |
| 5 | APPROVED (F05) | Schedule rows for games CLEV wasn't in disagree with other sheets (2027 title game shows M-OH beating BAMA 0-0; Standings, AP and the bracket say BAMA won). | Owner: the Playoff Tree decides playoff scores and champions. Schedule is used only for CLEV games. |
| 5a | APPROVED (F05) | Two CLEV playoff scores differ between Schedule and Playoff Tree: 2036 first round vs LSU (Schedule 37-27, Tree 37-3); 2037 national title vs OHIO (Schedule 56-35, Tree 56-39). | Under F05 the Tree wins: 37-3 and 56-39. Owner to confirm. |
| 5b | NOTE | 2035 national title score is written "73*" for M-OH in the bracket. | Ask the owner what the asterisk means (overtime?). Until then, show the score without a note. |
| 5c | NOTE | All 15 bracket champions (2023-2037) match the Standings sheet. Every other CLEV playoff score matches the Schedule. | None. |
| 6 | APPROVED (F06) | Final scores are usually winner-first, but 2031 title game reads "34-35" (CLEV's score first, CLEV lost). | Store every game as CLEV score / opponent score using the W/L result. |
| 7 | APPROVED (F07) | Result column says W/L in early years and a team name ("CLEV", "M-OH") from 2034 on. | Convert to W/L from CLEV's point of view. |
| 8 | APPROVED (F08) | Empty placeholder games (2024-26 "B12-CH" and "NC" rows with N/A and 0-0). | Drop them. |
| 9 | APPROVED (F09) | Stats tab titles are wrong in places (2026 tab says 2025; 2027 kicking says 2025; 2029 says 2027; 2035 says "20235"; 2037 says 2036; 2029-37 passing title blank). | Take the season from the tab name; ignore the titles. |
| 10 | APPROVED (F10) | Error cells: #DIV/0! (empty future seasons on coach sheets; yards-per-catch for 0-catch players), #REF! (future year headers on Schedule). | Treat as blank. Recompute averages where the inputs exist. |
| 11 | APPROVED (F11) | Numbers stored as text ("3,817", "1,085") and records as text ("(5-4)"). | Convert to numbers; parse conference records. |
| 12 | APPROVED (F12) | Records sheet is short and out of date: 21 records, newest from 2029. Example: Baraka Nwangwu's 2,536 rush yards in 2029 beat the listed 2,329 season record. | Show the tracker's records as entered, and add a separate "Computed from the stats" school list (CLEV only). |
| 13 | OPEN | Recruiting class summaries for 2029, 2030 and 2031 are exact copies of the 2025 numbers for all three programs; 2026-28 say "did not track". | Show class summaries only for 2024 and 2025. For CLEV, compute star counts from the recruit list every year. |
| 14 | OPEN | 2026 recruit list has no star ratings filled in. | Show stars as "not tracked" for 2026. |
| 15 | OPEN | 2025 Transfers "Class" column holds numbers (1, 50, 74, 80, 91, 158), not classes. | Treat them as transfer-portal rankings. Or the owner says what they are. |
| 16 | OPEN | Standings 2034: ECU appears in both the AAC (#4) and the MAC (#2). | Owner to confirm the MAC #2 team. |
| 17 | OPEN | Depth Chart: no ratings after 2032; the 2038+ columns hold leftover copies of 2024 names. | Use ratings 2024-32 only; ignore every column after 2037. |
| 18 | OPEN | Class labels are inconsistent: "SR (RS)", "SR(RS)", "Dave Shelley SO (RS)" (no dash), "SR (SR)", "Dorian Pringle - ROLB" (a position where the class should be). | Normalize to FR / SO / JR / SR with a separate redshirt flag; ask about the two odd ones. |
| 19 | OPEN | Position labels vary: RB/HB, OG/LG/RG, OT/LT/RT, LE/RE vs EDGE, LOLB/ROLB/MLB vs LB, FS/SS vs S, "WR/ATH". | Keep the exact position for depth charts; use a family (QB, RB, WR, TE, OL, DL, LB, DB, K, P) for filters and games. |
| 20 | OPEN | Name variants: about 50 groups (list in `data/source-meta/name-variant-groups.json`). Examples: Kenny Tongues / Kenny Tonges / Keenan Tonges; Emmett / Emmit / Emmitt Mosley V; Damian / Damien Ferrario. | One canonical spelling per player in `aliases.json`. Owner picks. |
| 21 | OPEN | Coach names vary: Josh / Joshua Dolan, Tim / Timmy Slocombe, Joe / Joseph Snyderwine. | Owner picks the display name for each. |
| 22 | NOTE | Columns sit in slightly different places on each coach sheet (OHIO's conference record sits under the "Conf Rank" header). | Parser handles it; no data change. |
| 23 | NOTE | 2027 Walter Camp is a custom award ("Most Outstanding Player determined by JD"), plus the "Lynel Billups-Williams Rule". | Show as footnotes on the awards pages. |
| 24 | NOTE | Trophy photos on the Awards sheet carry an auction-house watermark. | Don't publish them; design our own award marks. |
