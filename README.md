# DanPom - College Basketball Betting Model

A Python-based college basketball betting model that combines multiple data sources to identify value plays against the Vegas spread.

## Setup

### Prerequisites

1. **Python 3.8+**
2. **KenPom API Access** - Subscribe at [kenpom.com/api](https://kenpom.com/api)
3. **Action Network PRO** (optional) - Subscribe at [actionnetwork.com/pro](https://www.actionnetwork.com/pro)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DanPom.git
cd DanPom
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure credentials:
```bash
cp config.example.py config.py
```

Edit `config.py` and add your credentials:
- `KENPOM_API_KEY` - Your KenPom API key (required)
- `ACTION_NETWORK_EMAIL` - Your Action Network PRO email (optional, for sharp money data)
- `ACTION_NETWORK_PASSWORD` - Your Action Network PRO password (optional)
- `TOURNEY_GM` - Set to `True` for tournament games (removes home court advantage)

4. Run the model:
```bash
python3 RunDanPom.py
```

### First-Time Action Network Setup

Action Network requires manual JWT token extraction due to captcha protection:

1. Open [actionnetwork.com](https://www.actionnetwork.com) in your browser
2. Open DevTools → Network tab
3. Log out, then log back in
4. Navigate to the NCAAB sharp report page
5. Export HAR file to `/home/dconde/Downloads/www.actionnetwork.com.har`
6. The token will be automatically extracted and cached in `action_network_token.txt`
7. Token is valid for ~1 year

See the "Action Network Authentication" section below for more details.

## Overview

DanPom analyzes college basketball games by:
- Calculating model spreads using KenPom efficiency metrics
- Comparing model spreads to Vegas lines to find edges
- Cross-referencing with Bart Torvik T-Rank projections
- Pulling raw bet/money percentages and sharp money signals from Action Network PRO

## Data Sources

1. **ESPN** - Game schedules and betting odds
2. **KenPom** - Adjusted efficiency metrics via API (AdjEM, AdjOE, AdjDE, Tempo)
3. **Bart Torvik** - Independent T-Rank projections and lines
4. **Action Network PRO** - Raw bet/money percentages + sharp money signals

## Quick Start

```bash
python3 RunDanPom.py
```

Generates three output files in `/home/dconde/Documents/DanPom/`:
- `DanPom_YYYYMMDD.csv` - Filtered games with model edge (used in Google Sheets)
- `DanPom_all_YYYYMMDD.csv` - All games analyzed
- `ActionNetwork_YYYYMMDD.csv` - Full Action Network sharp/money data (reviewed separately)

## Configuration

All configuration is managed in `config.py`:
- `TOURNEY_GM` - Set to `True` for tournament games (removes the 3.5 home court adjustment)
- `KENPOM_API_KEY` - Your KenPom API key
- `ACTION_NETWORK_EMAIL` / `ACTION_NETWORK_PASSWORD` - Action Network PRO credentials (optional)

## Output Files

### DanPom_YYYYMMDD.csv / DanPom_all_YYYYMMDD.csv
These feed directly into the Google Sheets template. Column format is fixed — do not add columns here without updating the template.

| Column | Description |
|--------|-------------|
| Away Team / Home Team | Team names from ESPN (mapped via Ken Pom ESPN Mapping.csv) |
| Time / TV | Game info from ESPN |
| Odds | Raw odds string from ESPN |
| AdjEM_Away / AdjEM_Home | KenPom adjusted efficiency margin |
| Model_Spread | Calculated spread: `((AdjEM_Home - AdjEM_Away) * (Tempo_Home + Tempo_Away) / 200) + 3.5` |
| Spread | Vegas spread parsed from ESPN odds |
| Abs. Diff | `abs(Model_Spread - Spread)` — the model edge, sorted high to low |
| Crossover | YES if one team has positive AdjEM and the other negative |
| Bart Tovik | Bart Torvik's T-Rank line |
| AdjOE / AdjDE | Adjusted offensive and defensive efficiency |

The filtered file uses this mask:
- `(Model_Spread > Spread AND AdjEM_Home > 0)` — home team has edge and model likes them more
- OR `(Model_Spread < Spread AND AdjEM_Away > 0)` — away team has edge and model likes them more

### ActionNetwork_YYYYMMDD.csv
Reviewed separately from the main model output. Contains raw betting percentages for every game plus Action Network's PRO flagged signals.

**Spread percentages (all games):**
| Column | Description |
|--------|-------------|
| Spread_Tickets_Away / Home | % of bets placed on each side |
| Spread_Money_Away / Home | % of money on each side |
| Money_Diff_Away / Home | `Money% - Tickets%` — the sharp indicator. ≥+20 is significant per strategy doc |

**Totals percentages (all games):**
| Column | Description |
|--------|-------------|
| Total_Line | The O/U number |
| Total_Tickets_Over / Under | % of bets on Over/Under |
| Total_Money_Over / Under | % of money on Over/Under |
| Total_Money_Diff_Over | `Money% - Tickets%` for the Over — positive = sharp money on Over |

**PRO flagged signals (only games Action Network actively flags):**
| Column | Description |
|--------|-------------|
| Sharp_on_Away / Home | True if AN detected sharp money on that side |
| Steam_Moves_Away / Home | Number of steam moves (coordinated sharp betting) |
| Big_Bets_Flagged_Away / Home | True if AN flagged a big bet alert |
| Power_Edge_Away / Home | AN's own power rating disagreement with the line (in points) |
| Sharp_on_Over / Under | Sharp money detected on the total |
| Steam_Moves_Over / Under | Steam moves on the total |

## Model Formula

```
Model_Spread = ((AdjEM_Home - AdjEM_Away) * (AdjTempo_Home + AdjTempo_Away) / 200) + 3.5
```
The `3.5` is the home court advantage adjustment. Set `TOURNEY_GM = True` to remove it for neutral-site tournament games.

## Files

| File | Purpose |
|------|---------|
| `RunDanPom.py` | Main script — runs the daily report |
| `GetESPNSchedule.py` | Scrapes ESPN schedule and odds |
| `KenPomAPI.py` | Fetches KenPom ratings via API, cached for 6 hours |
| `GetBartTovik.py` | Scrapes Bart Torvik schedule (JS-rendered, uses requests-html) |
| `GetActionNetworkClean.py` | Fetches Action Network data with JWT auth |
| `ParseOdds.py` | Parses ESPN odds string using fuzzy matching to assign away/home |
| `CalcModelSpread.py` | Model spread calculation |
| `Ken Pom ESPN Mapping.csv` | Team name overrides to align ESPN names with KenPom names |
| `action_network_token.txt` | Cached JWT token for Action Network (do not commit) |

## Error Handling

Action Network failures are non-fatal — the main DanPom output always generates:
- If AN auth fails or the API errors, the script logs a warning and continues
- `ActionNetwork_YYYYMMDD.csv` simply won't be written that day
- The Google Sheets workflow is unaffected

## Action Network Authentication

Login requires a captcha so programmatic login doesn't work. The JWT token is extracted manually from a HAR file:

1. Open Action Network in browser, open DevTools Network tab
2. Log out, then log back in
3. Navigate to the NCAAB sharp report page
4. Export HAR file to `/home/dconde/Downloads/www.actionnetwork.com.har`
5. Run the token extraction script (or ask Claude to do it):
   ```python
   # Finds the loginnew POST response and saves the JWT to action_network_token.txt
   ```
6. Token is valid for ~1 year — refresh when you start getting auth errors

The API endpoint used is:
```
GET https://api.actionnetwork.com/web/v2/scoreboard/proreport/ncaab
    ?bookIds=15,30,1006,1548,974,939,1005,972,1902,1903,2194
    &date=YYYYMMDD&division=D1&periods=event&tournament=0
```
Book 15 is DraftKings and is used as the consensus source for bet/money percentages.

## Known Limitations

- **Team name mismatches**: ESPN, KenPom, and Bart Torvik use different team names. `Ken Pom ESPN Mapping.csv` handles most but not all. Action Network names are NOT merged into the main DataFrame for this reason — it's a separate file until a name mapping is built.
- **Action Network token expiry**: Must be refreshed manually via HAR export (~yearly).
- **Bart Torvik JS rendering**: Uses `requests-html` which spins up Chromium. Slow but reliable.

## Betting Strategy Reference

See `/home/dconde/Documents/DanPom/claude-info/betting_strategy_summary.md` for the full framework:
- Signal hierarchy (HIGH / MEDIUM / SMALL confidence)
- Sharp money thresholds (≥20% money/tickets differential)
- Bankroll management (max 2 units per game)
- Red flag avoidance system
