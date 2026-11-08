# Weight-space study v3 — sampling-seed result (amendments 1 and 3)

8 November 2026 (UTC). **Robustness is not established.** Per the frozen rule ("robust only if all three
seeds pass in full"), the outcome is: seed 101 pass, seed 102 incomplete, seed 103 fail.

| Seed (temp 0.7) | Rows | Base | Edit α=4 | Sign-flipped | Prompt | Edit rereads | Gate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 101 | 144/144 (first batch) | 18 | 24 | 6 | 24 | 24/24 | pass |
| 102 | 63/144 (batch cancelled by Modal) | – | – | – | – | – | **incomplete** |
| 103 | 144/144 (rerun) | 24 | 4 | 0 | 24 | 4/24 | **fail** |

(target completions of 24; non-target 12/12 in every arm that completed).

## Findings

1. **Stop-token side effect.** On seed 103 the edit arm's first sampled completion was empty (one
   token, finish reason `stop`, no tool call) in 20 of 24 target cases. Greedy decoding, which
   the design-set rule and the main panel used, cannot reveal this. At temperature 0.7 the α = 4
   edit puts enough probability on an immediate stop to matter.
2. **Shared-seed design flaw (mine).** All requests in a batch carry one sampling seed and the target
   contexts differ only in coefficients, so each seed is nearly one draw per arm: base rereads 9/24
   under seed 101 and 24/24 under seed 103. Counts within a seed are not independent samples;
   the net-win and sign-test figures for seed 101 should not be read as statistics.
3. **Base is stronger under sampling** (18/24 on seed 101, 24/24 on seed 103 vs 4–5/24 greedy), so
   the edit's measured advantage depends strongly on the decoding regime.
4. **Untested regime.** The competition baseline config uses temperature 0.2 with a thinking budget;
   this study used temperature 0 or 0.7 without thinking.

## Provenance

Seed 101: `artifacts/wsp-v3-seeds/20261108T000218Z/run.json` (SHA-256 `58f0122972bf9b5af697f7785a721aceb29b7fbe980375904d2a3029a91ce542`; the batch hit its 1,800-second execution limit at 196 of
432 rows). Seed 102: `artifacts/wsp-v3-seeds/20261108T003338Z/run.json` (SHA-256 `dd0603e81524296ae5190d05f24837b45cca4307309f4044dad6bf6ff8ab1987`; cancelled by Modal at 63 rows, no terminal event;
a report-path collision with the seed-103 batch occurred earlier in the same file, see the ledger).
Seed 103: `artifacts/wsp-v3-seeds/20261108T004228Z/run.json` (SHA-256 `f0686ed112e015ae610903a23b122d394adf4b6687136d79d882690b2dac2c57`). Amendments: [1](weight-space-study-v3-amendment-1.md),
[3](weight-space-study-v3-amendment-3.md). The study compute cap (USD 8) is essentially spent; seed 102
is not re-run.
