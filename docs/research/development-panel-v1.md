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

## Decision after the one-minute comparison

Do not promote either condition from this result. A useful next diagnostic is a separately recorded, matched increase in task time: most attempts were cut off, and the [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent) permits per-task limits within the overall 12-hour generation budget. More time is a hypothesis, not an established fix; retain the one-minute reference and rerun both conditions at any new budget. Budget/thinking comparisons also have public prior work in the novelty register.

No weight interpretation, edit, adapter, or original research contribution has been demonstrated. Confirm scorer-compatible adaptation before investing in it, and obtain the Ultra switch before weight work. Preserve reserved validation for a frozen candidate and distinguish these public development results from hidden scoring.

## Matched three-minute diagnostic, 4 November

`baseline-3m` and `pagination-v1-3m` copy their respective candidates with exactly one setting changed: `max_time_minutes: 1` becomes `3`. Prompts, sampling, ten counted tool calls, fifty turns, command/verification timeouts, checkpoint, A10G hardware, serving flags, official wheels, and runtime image are preserved. Original candidates and reports remain intact. This is a small diagnostic with one draw per condition; changed trajectories and stochastic variation limit causal attribution.

Both candidates passed official CPU compilation. Fresh controls on all four original cases again qualified exactly the same two Rich cases; Requests exclusions, task order, and qualification policy are unchanged. Control report: `artifacts/panels/development-panel-v1/20261104T202406Z-controls.json`. Candidate evaluation/sampling hashes matched those controls. No reserved validation issue was evaluated.

| Case | Three-minute condition | LLM / counted tool calls | Submission | Verification | Case seconds, including verification |
| --- | --- | --- | --- | --- | --- |
| `rich_3535` | Baseline | 7 / 5 | 473-character patch | 3 failed, 5 passed | 92.11 |
| `rich_3480` | Baseline | 13 / 10 | 437-character patch | Timeout, exit 124 | 380.90 |
| `rich_3535` | Pagination | 11 / 9 | 459-character patch | 3 failed, 5 passed | 57.33 |
| `rich_3480` | Pagination | 16 / 10 | Empty patch submitted | Timeout, exit 124 | 444.52 |

Both conditions again solved **0/2**. No three-minute attempt reported an agent/session error, versus session timeouts in three of the four earlier attempts. This does not mean every tool succeeded: budget errors and an unavailable analyzer tool appear in the traces despite a null top-level agent error. Actual repairs remain the outcome; an explicit submission or pipeline completion is insufficient.

Observed failures, without weight-level attribution:

- Both `rich_3535` patches removed the callable regex `.match` binding. The agents received failing targeted-test output, then claimed success and submitted. The baseline explicitly treated failures introduced by its change as pre-existing breakage. The starter prompt's permission to ignore unrelated failures is a plausible contributor, not a demonstrated cause.
- The second baseline used all ten counted calls before its targeted test. The harness rejected that test command with `BudgetExceeded`; an unverified patch was submitted and the independent verification still hung.
- The second pagination attempt called `run_command` from the read-only analyzer, where it is unavailable. Later, its source edit was rejected by the tool-call budget. It then submitted `patch_size=0`, and verification of the unchanged checkout timed out. Do not count this as a nonempty patch or infer that more time alone would allow an edit.

Baseline model readiness/function total were 196.42/673.46 seconds; pagination was 205.05/710.57 seconds. Baseline waited for A10G capacity but scheduled within the 15-minute cancellation window. Each app was confirmed stopped before the next allocation; no jobs or deployments remained at closure.

- Baseline, runner `9946d9f`, [Modal app](https://modal.com/apps/ach-bj100/main/ap-kCiHlguSlyaGWxJesLJShh): `artifacts/panels/development-panel-v1/20261104T203042Z-baseline-3m.json`.
- Pagination, runner `ebb35ff`, [Modal app](https://modal.com/apps/ach-bj100/main/ap-a3Sujk7lOzieocGIOuzEbj): `artifacts/panels/development-panel-v1/20261104T204852Z-pagination-v1-3m.json`.

## Decision after the three-minute comparison

Do not promote either candidate or keep increasing limits without a defined control. More task time did not produce a repair in these runs. The next useful control is a generic prompt/workflow change that requires acting on relevant failing-test output, reserves calls for editing and verification, respects each subagent's declared tools, and checks for a nonempty patch. Test those changes separately under matched budgets before attributing failures to weights. More cases and repeated measurements will be needed to assess transfer and variance.

The longer-budget comparison and observed workflow failures are development findings, not a novel method. No weight work has occurred. Scorer-compatible adapter validation and the user's confirmed Ultra switch remain prerequisites for a weight intervention; keep the reserved validation partition untouched until a candidate is frozen.

## Feedback-only development screen, 4 November

`feedback-v1-3m` copies `baseline-3m` and changes only the root prompt's targeted-test feedback policy: read exit codes, correct failures related to the task/edit, require evidence before dismissing a failure as pre-existing, and describe unresolved verification honestly. No task-specific code/path/example was added. The analyzer, navigation, tools, sampling, time/call budgets, official wheels, checkpoint, A10G hardware, and runtime image remain unchanged.

This is an exploratory screen against the saved three-minute baseline (0/2), with no fresh baseline draw. Existing CPU controls are reused only after source/fixture/image/evaluation/sampling identity checks; the same two Rich cases and both Requests exclusions are retained. Compiler, reference-report hashes, and preflight checks are preserved in `artifacts/runtime-validation/feedback-v1-preflight.json`. None of the 68 reserved validation cases was evaluated.

| Case | LLM / counted tool calls | Submitted patch | Visible targeted tests | Independent verification | Case seconds |
| --- | --- | --- | --- | --- | --- |
| `rich_3535` | 10 / 8 | 756 characters | 7 passed | Import error, exit 2 | 68.63 |
| `rich_3480` | 11 / 9 | 470 characters | Collection errors before and after attempted correction | Syntax error, exit 2 | 99.01 |

Result: **0/2 repairs**, with no session or call-budget termination. Both submissions were nonempty; neither was correct.

- In `rich_3535`, the agent removed a regex helper and replaced its fast-path use with a direct width comparison. The visible tests passed, but verification imports the removed helper and failed. This is a patch regression, not a new environment exclusion. There was no failing-test feedback for the agent to respond to in this trajectory, so it does not test the intended response-to-failure mechanism.
- In `rich_3480`, a replacement matched an incomplete source-line prefix and left trailing text, creating a syntax error. After a failing test, the agent attempted two further edits and reran the targeted test. Those replacements repeated the prefix mistake and made the line worse. The retest still failed; the agent nevertheless submitted and claimed a fix. A corrective-edit/retest sequence is observed, but repair success and honest interpretation of the final failure were not demonstrated. Its causal relationship to the prompt is unresolved in this single historical-control screen.

Report: `artifacts/panels/development-panel-v1/20261104T211036Z-feedback-v1-3m.json`, runner `1f2f3b2`, [Modal app](https://modal.com/apps/ach-bj100/main/ap-saXf1R8NVLDS2KIlRvSuM7). Model readiness/function total: 249.12/422.19 seconds. The app and local CLI completed; final workspace inspection found no active project app or queued request.

## Current decision

Do not promote the feedback candidate or claim an improvement from attempted corrections. Keep this simple prompt control as a recorded negative repair result. The fixed panel is too small and already inspected to establish generalization; any later candidate needs fresh development evidence and a frozen validation decision.

The subsequent [controlled adapter checks](adapter-compatibility.md) passed on Modal and the official Kaggle image/L4x4 setup. This clears the tested inference deployment prerequisite. Next build focused behavioral diagnostics and fresh development evidence before selecting a weight intervention. Stop for the user's confirmed Ultra switch before constructing/applying new adapter weights or designing a weight intervention, as required by the working agreement. No weight-level cause or novel method follows from these traces.
