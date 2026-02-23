---
name: run
description: Execute RunDanPom.py and then analyze today's output
disable-model-invocation: true
allowed-tools: Bash(/home/dconde/miniconda3/envs/danpom/bin/python*), Read, Grep, Glob
---

# Run DanPom Model

Execute the DanPom model and produce today's betting analysis.

## Steps

1. Run the model:
   ```bash
   /home/dconde/miniconda3/envs/danpom/bin/python /home/dconde/PycharmProjects/DanPom/RunDanPom.py
   ```
2. Verify output files were created in `/home/dconde/Documents/DanPom/`:
   - `DanPom_YYYYMMDD.csv`
   - `DanPom_all_YYYYMMDD.csv`
   - `ActionNetwork_YYYYMMDD.csv`
3. Report any errors. If Action Network fails (token expired, etc.), note it and continue with the DanPom files.
4. After successful run, invoke the `/picks` workflow: read today's files and produce the full betting analysis.
