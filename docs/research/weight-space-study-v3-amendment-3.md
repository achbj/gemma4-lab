# Weight-space study v3 — amendment 3: completing the sampling-seed run

Dated 8 November 2026 (UTC). [Amendment 1](weight-space-study-v3-amendment-1.md) ran 4 arms × 36 cases ×
seeds 101-103 in one batch (`artifacts/wsp-v3-seeds/20261108T000218Z/run.json`, SHA-256 `58f0122972bf9b5af697f7785a721aceb29b7fbe980375904d2a3029a91ce542`). The batch **exhausted its
1,800-second execution allocation** after 196 of 432 trajectories (about 7.6 seconds each at
temperature 0.7; my estimate of 2.6 seconds came from greedy runs). Seed 101 completed in full.
Seed 102 has 52 of 144 rows and seed 103 none; the rest are recorded as skipped. By amendment 1's
frozen rule, the robustness criterion ("all three seeds pass") is therefore **not met** as run.

**Disclosure:** before deciding to complete the run I saw the partial seed-102 counts (too few
cases to read: edit 3, base 2, prompt 4 completions in the first rows). The decision rests on the
infrastructure cause, not on those numbers.

## What this amendment does

Runs seeds **102 and 103 in full, each in its own single-seed batch** (`configs/wsp-v3-seeds-102.json`,
`configs/wsp-v3-seeds-103.json`): identical arms, cases, adapters, prompts, temperature 0.7,
protocol, per-seed gate and analysis as amendment 1. The 52 partial seed-102 rows from the aborted
batch are reported as aborted and are not used. No other change; no seed is dropped; every
completed seed is reported whether it passes or not. Budget: two A10G batches, bound USD 0.99
each (a 144-trajectory seed needs about 1,100 seconds plus 250 seconds startup, inside 1,800), within
the v3 cap (estimated spend before: ~USD 5.0 of 8).

**Reporting rule:** the paper states that the single-batch run was incomplete and gives all
three seeds' outcomes. Seed 101's result stands as run; "robust across three seeds" may be said only if
seeds 102 and 103 each pass in full.
