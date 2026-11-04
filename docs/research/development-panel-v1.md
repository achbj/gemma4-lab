# Fixed development panel: no demonstrated repair gain

Both conditions solved zero of the two qualified cases. This is a small, selected development comparison with one unseeded run per condition, not a leaderboard estimate or evidence of equivalence.

## Selection and qualification

`configs/development-panel-v1.json` selected two distinct base commits per development repository by a fixed hash ordering of task IDs. Four cases were frozen before control outcomes; none was replaced. The 68 reserved validation issues were not evaluated.

| Fixed case | Unchanged checkout | Reference fix | Eligibility |
| --- | --- | --- | --- |
| `rich_3535` | 1 failed, 7 passed | 8 passed | Qualified |
| `rich_3480` | Test timeout, exit 124 | 109 passed | Qualified after documented amendment |
| `requests_6757` | Collection error | HTTP-fixture/network failures | Excluded |
| `requests_6629` | Test/fixture failures | Test/fixture failures | Excluded |

The first qualification policy accepted only exit 1 and excluded the timeout. Before either GPU condition, the public `rich_3480` statement identified an infinite loop. The policy was amended to allow unchanged exit 1 or 124 only when the reference resolves with exit 0. Task IDs/order, minimum of two, test content, and timeouts were unchanged. The original report, derived report, source-report hash, and classification-code hash are retained:

- Original: `artifacts/panels/development-panel-v1/20261104T193619Z-controls.json`.
- Amended: `artifacts/panels/development-panel-v1/20261104T194633Z-controls.json`.

That infinite loop is a bug in the repository under repair. It is not evidence of a loop caused by Gemma's weights; those are separate questions.

This attrition leaves only Rich cases, so the comparison cannot support cross-repository transfer claims. Environment corrections reproduce [prior validation work](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747248). Hidden-scorer parity remains unverified.

## Matched conditions

Both conditions used approved E4B version 2, one NVIDIA A10G, image `im-bEtC1IFnE2DCntpbAu56LW`, the pinned official wheels, and unchanged serving flags. Agent budgets were one minute, ten counted tool calls, fifty turns, and 60-second commands; verification retained 300 seconds. Only the two generic pagination prompt additions differ. Candidate compilation hashes, sampling/evaluation hashes, fixture identities, and runtime-helper hashes were checked before launch. Reference solutions were removed from GPU inputs; verification tests stayed out of agent workspace files.

Each batch used one model startup and fresh evaluator/context/sandboxes for every case. Results streamed to local files after each case. The baseline app was confirmed stopped before the pagination batch started.

## Results

| Case | Condition | LLM/tool calls | Patch | Outcome |
| --- | --- | --- | --- | --- |
| `rich_3535` | Baseline | 4 / 3 | None | Agent timeout; verification not reached |
| `rich_3535` | Pagination | 11 / 9 | 488 characters; explicitly submitted | 1 failed, 7 passed; unresolved |
| `rich_3480` | Baseline | 9 / 9 | 666 characters; recovered on timeout | Verification still timed out; unresolved |
| `rich_3480` | Pagination | 13 / 10 | None | Agent timeout; verification not reached |

Three of four agent attempts hit the one-minute limit. The pagination candidate completed/submitted the first case but did not fix its failing behavior. It did not improve successful repairs or demonstrate a consistent call-count reduction on this panel. The paired result is zero wins, zero losses, two unresolved ties; the sample is too small to conclude equal capability.

Baseline model readiness/function total were 196.48/631.31 seconds; pagination was 250.23/374.62 seconds. The shorter second batch is largely affected by the first batch's 300-second verification timeout and different startup times; it is not evidence that pagination accelerates agent reasoning.

Raw reports:

- Baseline, runner `8aee809`, [Modal app](https://modal.com/apps/ach-bj100/main/ap-rtb0F5wxanOjYZabN3Ddl6): `artifacts/panels/development-panel-v1/20261104T194859Z-baseline.json`.
- Pagination, runner `051f66e`, [Modal app](https://modal.com/apps/ach-bj100/main/ap-GS250RfWd6hF7yunyShDF5): `artifacts/panels/development-panel-v1/20261104T200028Z-pagination-v1.json`.

## Decision

Do not promote either condition from this result. A useful next diagnostic is a separately recorded, matched increase in task time: most attempts were cut off, and the [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent) permits per-task limits within the overall 12-hour generation budget. More time is a hypothesis, not an established fix; retain the one-minute reference and rerun both conditions at any new budget. Budget/thinking comparisons also have public prior work in the novelty register.

No weight interpretation, edit, adapter, or original research contribution has been demonstrated. Confirm scorer-compatible adaptation before investing in it, and obtain the Ultra switch before weight work. Preserve reserved validation for a frozen candidate and distinguish these public development results from hidden scoring.
