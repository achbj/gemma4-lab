# Source localization on the Rich development panel

The symbol-first prompt reproduced the one-line `rich_2943` hash-cache repair.
It resolved **1/4** cases against **0/4** in the saved ten-call control and reached
two exact source targets against one. Early coverage reached **1/3** on issues
with specified behavior. The frozen gate required two early targets and a verified
repair linked to one of them.

| Case | Control source score | Symbol-first source score | Verified outcome |
| --- | ---: | ---: | --- |
| `rich_3942` | 2 | 2 | Failed collection after a style edit |
| `rich_3518` | 1 | 1 | Tool cap before an edit |
| `rich_2943` | 0 | 2, second lookup | Identical one-line hash repair, verifier exit 0 |
| `rich_3676` | 1 | 1 | Edited the installation hook and failed verification |

The table trace exposed an incorrect premise in the candidate. The stock graph and
embedding index contain `rich.table.Table.add_row`. The pinned `swegemma` 0.2.11
implementation removes the resolved query node when ranking its neighbors. The
exact `Table.add_row` lookup returned `rich.progress.TextColumn` in this run.
Earlier broad file reads repeatedly returned only lines 1–150. The target branch
starts at line 452. A direct source lookup can supply a line number for a narrow
read, which makes it the appropriate correction for named definitions.

The comparison used one sampled draw per arm, the same NVIDIA A10 label and exact
source, runtime and checkpoint identities. The candidate used 35 charged tool calls
and 46 traced model calls. The 370,740 input and 13,109 output tokens are retained
with the full report. Source scores use successful observations before the first
edit attempt.

The report is `artifacts/panels/development-context-v1/20261106T003016Z-symbol-localization-v1-8k.json`,
SHA-256 `f453f4e7db74933faeb007f544f479ca304fa16fa9786a93afd66982308b630e`.
`artifacts/runtime-validation/localization-v1-audit.json` records the scoring and
retrieval implementation location. [Run ledger](../operations/run-log.md)

## Direct source lookup correction

The corrected candidate uses literal definition search and a narrow source read.
The local feasibility probe found all three supplied symbols in the original public
snapshots. Each 60-line read contains its target body and fits the documented caps.
The agent still has to select the relevant symbol from the issue.

The corrected run reproduced **1/4 verified repairs**, **2/4 exact targets**, and
**1/3 early targets**. Its `rich_2943` patch is byte-identical to both earlier
verified repairs, and the exact body appeared in the first search for `meta`.
The source looked up in the table case was the `Table` class and `add_column`.
The final pre-edit read stopped at line 300, before the `add_row` branch at
452–457. The agent exhausted its calls on unsuccessful edits and the empty
submission failed verification. The Markdown and traceback patches also failed.

The two localization runs report the same NVIDIA A10 label as the fixed control.
The direct candidate used 29 charged tools and 39 traced model calls, with
325,505 input and 14,084 output tokens. All four cases ran without an observed
context or infrastructure termination. The early-coverage requirement remained
unmet, so the candidate stays at the inspected development stage.

The corrected run report is
`artifacts/panels/development-context-v1/20261106T004243Z-direct-localization-v1-8k.json`,
SHA-256 `edc000ed136db01d65beb5448c3f86d143068fc87cb5b947b8210ec3119e73c2`.
The independent trace scores and the original-stock probe are retained under
`artifacts/runtime-validation/direct-localization-v1-audit.json` and
`artifacts/runtime-validation/direct-localization-v1-source-probe.json`.
