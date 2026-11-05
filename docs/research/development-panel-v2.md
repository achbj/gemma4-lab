# Fresh Rich development comparison, 5 November 2026

Baseline-3m and edit-integrity-v1-3m each produced **0/4 independently verified
repairs** on the same four qualified development issues. The synthetic edit-recovery
gain did not produce a repair gain in this screen. The candidate remains unpromoted;
runtime/context and navigation constraints need simpler controls before weight work.

## Selection and qualification

`configs/development-panel-v2.json` selected four Rich tasks using SHA-256 ordering
of instance IDs and distinct base commits, excluding all v1 base-commit groups.
Selection used metadata before inspecting task content or outcomes. Rich-only selection
followed the Requests reference-control failures in v1; this is selected single-repository
development data, not a representative or cross-repository validation sample.

All four unchanged checkouts failed with exit 1; all four reference patches resolved
with exit 0. No exclusions or replacements occurred. CPU control times were 13.74,
9.32, 8.89 and 11.09 seconds. Candidate compilation and all fixture/task/runtime,
evaluation/sampling and compiler hashes passed. The [run ledger](../operations/run-log.md)
records the separate CPU and matched-GPU allocations. The dedicated CPU entrypoint
declares no GPU function; all 53 regression checks and Ruff lint/format passed.

## Matched results

Both candidates used unchanged E4B v2, the same official-wheel image and ADK/tool path,
temperature 0.2/top-p 0.95, 16,384 output-token allowance, thinking budget 4,096, three
minutes per task, ten shared tool calls, fifty turns and 60-second commands. Verification
had its independent 300-second bound. Baseline ran first, candidate second. There was
one draw per task/condition, with no outcome-driven edits, retries or replacements.

| Issue | Baseline-3m | Edit-integrity-v1-3m |
| --- | --- | --- |
| `rich_3942` | Submitted destructive module replacement; verification failed | Context-window termination; recovered patch verified and failed |
| `rich_3518` | Empty submission; verification failed | Budget stop without modifications; no verification |
| `rich_2943` | Budget stop without modifications; no verification | Patch verified and failed |
| `rich_3676` | Visible tests passed; independent verification failed | Patch verified and failed |

Both batches covered all four selected cases, with zero paired repair wins/losses.
Each condition had three failed verified attempts and one unverified budget termination.
All eight rows remain in the attempted-case denominator; missing verification is not
a test failure or an infrastructure exclusion. Visible passing tests did not establish
the requested behavior. Trace and patch inspection is needed alongside repair counts.

The baseline repeatedly failed replacements and overwrote most of `rich/markdown.py`
on the first issue, then its targeted test was rejected by the shared tool-call budget.
Other cases spent the shared tool budget on navigation or omitted required behavior
despite visible passing tests.

The candidate's first issue hit `ContextWindowExceededError`: the server allowed 32,768
tokens while the request reserved 16,384 output tokens and had at least 16,385 input
tokens. The native evaluator recovered its partial patch and still verified it, yielding
exit 1. Record both the context/resource termination and failed recovered patch. This
does not support a clean causal conclusion about the recovery instructions alone.

## Provenance and decision

- Unchanged runtime image: `im-bEtC1IFnE2DCntpbAu56LW`; no adapter or weight changes.
  Both batches used runner commit `c81e1e1` and NVIDIA A10. Baseline readiness/total:
  198.10/484.70 seconds; candidate: 194.09/573.25 seconds.
- Controls: `artifacts/panels/development-panel-v2/20261105T085310Z-controls.json`,
  SHA-256 `69e67146f641a0bdc714dc8cd2ee79b5c7d6c4e6f8f4941d1791c9ed60ae6c61`.
- Baseline [app](https://modal.com/apps/ach-bj100/main/ap-2loo8fu2dbcBrMsL5zBTVc):
  `artifacts/panels/development-panel-v2/20261105T085834Z-baseline-3m.json`, SHA-256
  `b098e2f71217b0f71593c8c0c3b42e60736f49607ae65b44183f52479b4d9e8e`.
- Candidate [app](https://modal.com/apps/ach-bj100/main/ap-d0ljucpGZploTbjNiMgJc2):
  `artifacts/panels/development-panel-v2/20261105T090822Z-edit-integrity-v1-3m.json`, SHA-256
  `96fe5341f136a08529b7a3d3efbd9d7a7ebed1ace35ea334f4beb87e6294fcba`.
- Independent preflight/baseline/comparison audits:
  `artifacts/runtime-validation/development-panel-v2-{preflight,baseline-audit,comparison}.json`.

This tiny, now-inspected development panel cannot estimate hidden accuracy, establish
generalization, rank global optima or support a novelty claim. Reference solutions were
stripped from inference payloads; verification-only tests stayed outside agent workspace
files. All 68 reserved validation issues remain untouched. No external paid model API,
new weight interpretation or intervention occurred.

Raw traces record 51 baseline LLM calls (420,479 prompt/17,354 output tokens) and 52
candidate calls (435,394/22,784); official token summaries report zero. Preserve the
traces. The largest completed outputs were 2,970 and 4,249 tokens, respectively.

Next preregister an isolated shared output allowance of 8,192 tokens in both conditions,
retaining the server context and other settings. This leaves more input headroom and
exceeds the observed completed outputs; a 4,096 cap would truncate an observed response.
It does not guarantee every later history fits. Then measure a simpler navigation/
delegation control under matched budgets. Keep each experiment explicit and preserve
these failed runs. A reliable real-task baseline and the best measured cheap controls
must precede weight-intervention claims; new weight work still requires Ultra confirmation.
