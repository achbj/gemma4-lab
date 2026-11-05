# Fresh-coefficient edit-recovery screen, 5 November 2026

The edit-integrity prompt passes its prespecified synthetic screening gate. It
corrected and completed 9/9 initially wrong cases versus baseline's 7/9, with 3/3
passing controls preserved in both conditions. This qualifies the prompt for fresh
real-development evaluation; no competition repair improvement is established.

The candidate adds two root instructions to baseline-3m: reread current source after
edit/syntax failure, and replace complete lines/blocks using documented arguments.
Five companion files remain byte-identical. Review clarified `old_string` wording
before inference; no prompt or case changed after outcomes.

`configs/behavior-diagnostic-v2.json` froze twelve unique coefficient pairs disjoint
from v1, retaining three cases per family, the same context/checker, greedy settings,
six-action budget and alternating condition order. Both conditions get identical
seed histories. The [run ledger](../operations/run-log.md) records rules, controls,
cost allocation and the decision gate before execution.

| Family | Baseline: correct source / complete workflow | Edit-integrity: correct source / complete workflow |
| --- | --- | --- |
| Prefix corruption | 1/3 / 1/3 | 3/3 / 3/3 |
| Failed assertion | 3/3 / 3/3 | 3/3 / 3/3 |
| Passing control | 3/3 / 3/3 | 3/3 / 3/3 |
| Irrelevant passing check | 3/3 / 3/3 | 3/3 / 3/3 |

Exactly two paired prefix workflow wins, zero losses, 3/3 candidate passing controls,
zero premature submissions, and all 24 valid trajectories meet the frozen gate.
Source correctness and workflow outcomes agree here; the source oracle checks seven
fixed integers and workflow additionally requires a nonempty explicit submission
with a successful target check after the final edit.

Each candidate prefix trajectory read current source, replaced the complete corrupted
line with exact matching, passed a fresh targeted check, then submitted on action four.
Baseline used six actions on each prefix, with two unresolved syntax errors. Passing
controls submitted on action one in both conditions. Total post-seed actions fell
from 42 to 36. Baseline received five command, two edit and eight argument errors;
the candidate received three command failures from the wrong-source smoke fixtures
and no edit/argument errors. No API/wrapper protocol failures, truncations, timeouts
or skipped cases occurred. Parsed argument errors do not identify a generation versus
parser cause.

Provenance: stopped [Modal app](https://modal.com/apps/ach-bj100/main/ap-ecmTDffj4zR6vBdaxAmKS2),
source `e030fae`, unchanged image `im-bEtC1IFnE2DCntpbAu56LW`, no adapter, approved E4B v2.
Readiness/complete function took 256.07/290.60 seconds. Raw report:
`artifacts/behavior-diagnostic-v2/20261105T083728Z/run.json`, SHA-256
`0a534a2cd514d93848f0e617e8af5715f9ddd5478fda7e6da74bfa8dc4104f94`.
Independent native-editor replay, histories, hashes, settings, coverage, metrics and
gate checks passed in `artifacts/runtime-validation/behavior-diagnostic-v2-consistency.json`.

Limits: one deterministic draw per condition/case, shared inspected templates, restricted
arithmetic and commands, synthetic seeded histories, and two prompt bullets changed
together. Fresh coefficients provide limited independence. This does not establish
which bullet causes the gain, ADK/SWE repair transfer, novelty, or a need for weight
editing. The four-issue development follow-up was selected from metadata before
inspecting task contents/outcomes. It requires separate unchanged/reference controls
and candidate compilation before matched inference. All 68 reserved validation issues
remain untouched.
