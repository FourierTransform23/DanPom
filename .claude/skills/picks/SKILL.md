---
name: picks
description: Analyze today's DanPom and ActionNetwork output to recommend bets
disable-model-invocation: true
argument-hint: [YYYYMMDD]
---

# Daily Picks Analysis

Read today's DanPom and ActionNetwork CSVs and produce a structured betting analysis. If a date argument is provided, use that date; otherwise use today's date.

## Which DanPom file to read
- **Weekdays (Mon-Fri):** `DanPom_all_YYYYMMDD.csv`
- **Saturday:** `DanPom_YYYYMMDD.csv` (filtered — Saturday slates are too large). User will specify if it's Saturday.

Always read `ActionNetwork_YYYYMMDD.csv` regardless of day.

Files are in `/home/dconde/Documents/DanPom/`.

## Signal Priority (most to least important)

1. **Action Network signals** — This is the primary source. Prioritize:
   - `Steam_Moves` (2+ on a side is meaningful)
   - `Money_Diff` (money % minus ticket % — threshold is >=+20 for sharp)
   - `Sharp_on_*` flags
   - `Power_Edge` values
   - `Big_Bets_Flagged`
2. **Bart Torvik** — secondary reference to sanity-check direction and projected score
3. **Model Spread** — tertiary reference only, not a deciding factor. Applies to spreads only, NOT totals.

## Output Structure

Produce a clear, structured analysis with these sections:

### Top Plays (strongest AN signals)
Games where multiple AN indicators align (steam + money diff + sharp flags). Grade each play.

### Total Plays (Over/Under)
Games with steam moves or sharp flags on Over or Under. The model spread has NO bearing on totals — rely entirely on AN data.

### Conflicts / Mixed Signals
Games where AN signals point one way but model/BT point the other. Note the conflict and advise caution.

### Watch List for Next Run
Games where signals are building but not yet at threshold — e.g., Money_Diff approaching +20, or 1 steam move that could become 2+. These are the ones to re-check when the model is run again later in the day.

This output will be consumed by a downstream advisor agent that recommends final bets.
