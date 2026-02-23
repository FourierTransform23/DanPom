# DanPom — Claude Instructions

## Project Overview
College basketball betting model. Runs daily during the NCAAB season. Combines KenPom efficiency ratings, Bart Torvik projections, and Action Network sharp money data to identify betting edges.

## Running the Model
```bash
/home/dconde/miniconda3/envs/danpom/bin/python /home/dconde/PycharmProjects/DanPom/RunDanPom.py
```
All dates are dynamic via `datetime.now()` — no date arguments needed.

## Skills (Slash Commands)
- `/run` — Execute RunDanPom.py and then analyze the output (runs `/picks` automatically after)
- `/picks` — Read today's DanPom + ActionNetwork CSVs and produce a structured betting analysis. Accepts optional `YYYYMMDD` date argument.
- `/compare` — Re-run DanPom.py to pull fresh data, then diff ActionNetwork output against the previous run in the conversation to highlight new sharp activity (steam moves, money shifts, new flags)

## Output Files
Located in `/home/dconde/Documents/DanPom/`:
- `DanPom_YYYYMMDD.csv` — filtered games with model edge (positive AdjEM teams only)
- `DanPom_all_YYYYMMDD.csv` — all games sorted by absolute model vs. line difference
- `ActionNetwork_YYYYMMDD.csv` — sharp money data, separate file (team names don't align with ESPN/KenPom)

## Key Rules
- **Never add or reorder columns** in the DanPom CSV files without confirming the Google Sheets template is updated first. User pastes output directly into a pre-canned template daily.
- **Action Network is always a separate file** — team name mismatches make merging unreliable. User cross-references it manually.
- **Do not auto-commit.** Ask before any git operations.
- `TOURNEY_GM = False` during regular season. Set to `True` only for neutral-site tournament games (removes the 3.5 home court coefficient).

## Model Logic
- `Model_Spread` sign convention: **positive = home team favored**, negative = away team favored
- `Spread` uses the same sign convention (parsed from the odds string)
- `Abs. Diff` = `|Model_Spread - Spread|` — larger = bigger model edge
- `Crossover = YES` means one team has positive AdjEM and the other negative (above-average vs. below-average matchup)
- Filtered file only includes games where the model-favored team has **positive AdjEM** (quality filter)

## Action Network Authentication
- Requires a cached JWT token in `action_network_token.txt` (project root). Valid ~1 year.
- Programmatic login fails due to captcha. To refresh the token:
  1. Log out/in at actionnetwork.com
  2. Export HAR file to `/home/dconde/Downloads/www.actionnetwork.com.har`
  3. Extract token from the `loginnew` POST response body
- Account: conde.daniel23@gmail.com

## Sharp Money Thresholds
- `Money_Diff` (money % minus ticket %) **≥ +20** is the sharp money threshold
- `Steam_Moves` ≥ 2 on a side is a meaningful steam signal
- `Sharp_on_*` flags from Action Network indicate AN's own sharp detection algorithm triggered

## Betting Strategy & Signal Priority
The model spread is basic and not optimized for true edge — **do not use it as the primary signal for selecting plays.** It serves as a reference only.

**Priority order for identifying best bets:**
1. **Action Network signals** — sharp steam moves, big handle money percentages, power rating edge, and `Sharp_on_*` flags. These reflect what pros and syndicates are actually doing with real money.
2. **Bart Torvik** — use as a secondary reference to sanity-check a side.
3. **Model spread (KenPom)** — use as a tertiary reference only, not a deciding factor.

**Important scope note:** The model spread applies to **spread picks only**, not game totals. For totals, rely entirely on Action Network signals (steam moves, over/under money %, `Sharp_on_Over/Under`).

## Multi-Run Workflow
The scripts are expected to run **multiple times per day**. Each run may show updated Action Network data — new steam moves, shifting money percentages, or newly triggered sharp flags. When comparing runs, pay attention to changes in:
- `Steam_Moves` counts increasing
- `Money_Diff` crossing the ≥20 threshold
- New `Sharp_on_*` flags appearing

These changes between runs are meaningful signals that sharps are loading up on a side.

## Which DanPom File to Use
- **Weekdays (Mon–Fri):** Use `DanPom_all_YYYYMMDD.csv` — shows all games.
- **Saturday:** Use `DanPom_YYYYMMDD.csv` (filtered, no `_all`) — Saturday slates are too large; the filtered file narrows to games with a qualifying model edge.
- The user will always specify if it's Saturday.

## Advisor Agent Context
The output of this analysis is fed as input to a downstream advisor agent that recommends bets for the day. When producing analysis, structure it clearly so the advisor agent can consume it — highlight top AN signals, note any conflicts between sources, and flag games worth revisiting on the next run.
