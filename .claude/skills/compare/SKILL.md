---
name: compare
description: Re-run DanPom, then diff ActionNetwork data against the previous run to find new sharp activity
disable-model-invocation: true
allowed-tools: Bash(/home/dconde/miniconda3/envs/danpom/bin/python*), Read, Grep, Glob
argument-hint: [YYYYMMDD]
---

# Compare Runs

Re-run the model to pull fresh data, then diff against the previous run's output to highlight what changed.

## Step 1: Re-run the model

```bash
/home/dconde/miniconda3/envs/danpom/bin/python /home/dconde/PycharmProjects/DanPom/RunDanPom.py
```

Verify the output files were created. If Action Network fails, note it — comparison can't proceed without fresh AN data.

## Step 2: Diff against previous run

Read the fresh `ActionNetwork_YYYYMMDD.csv` from `/home/dconde/Documents/DanPom/`. Compare against the data from the previous `/picks` or `/run` analysis (which should be in the conversation context from the earlier run).

If no previous run context exists, say so and just produce a standard `/picks` analysis instead.

## Key changes to highlight

For each game, flag any of these changes between runs:

| Signal | What matters |
|--------|-------------|
| `Steam_Moves` | Any increase (especially 0->1 or 1->2+) |
| `Money_Diff` | Crossing the >=+20 threshold, or swinging by 5+ points |
| `Sharp_on_*` | Any flag flipping from False to True |
| `Big_Bets_Flagged` | Any flag flipping from False to True |
| `Power_Edge` | Newly appearing or increasing significantly |
| Ticket/Money %  | Shifts of 5+ percentage points on any side |

## Output

- **New signals**: Games that now have sharp activity they didn't before
- **Strengthening signals**: Games where existing steam/money signals intensified
- **Fading signals**: Games where earlier signals weakened (rare but possible)
- **No change**: Brief note that remaining games are unchanged

Keep it concise — the user cares about what's NEW, not a rehash of the full slate.
