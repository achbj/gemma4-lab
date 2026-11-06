# Gemma 4 prize strategy

Decision brief, 4 November 2026. The user set a compute/API spending ceiling of EUR 100 and selected the `ach-bj100` Modal workspace, reporting USD 30 in existing credit. Modal identity and Kaggle competition access have been verified. See [the working agreement](../../AGENTS.md) for the Ultra checkpoint before interpreting or editing weights, and [the run log](../operations/run-log.md) for execution/budget status.

## Recommended direction

Develop an E4B coding agent and a Paper Track study in parallel, as the user explicitly requested on 5 November. Avoid a broad model sweep. Target the small-model award while collecting a bounded, original and reproducible study for the earlier paper deadline. A paper's claims must follow the evidence; no positive weight effect or novelty is promised.

Treat weight-space programming as a bounded research experiment within this project. Do not make the entire competition attempt depend on it working.

## Measured status, 6 November

The [controlled adapter package](adapter-compatibility.md) now works on both Modal A10 and the official Kaggle image/L4x4 setup, with unchanged weights and fixed numerical/compiled-agent controls. This clears the tested inference deployment prerequisite. The small [development panel](development-panel-v1.md) still shows no repair gain from pagination, a longer task budget, or the feedback-only prompt; it is too small and inspected to establish generalization. All 68 reserved validation issues remain untouched.

The [fixed synthetic diagnostic](behavior-diagnostic-v1.md) completed all 24 trajectories. Each prompt completed seven of nine initially wrong cases and all three passing controls. Both failed the same two prefix-corruption cases, with delayed rereading and unsuccessful edits. Simple assertion failures and irrelevant passing tests were handled correctly in this screen; a general failed-test deficit is not established.

The [fresh-coefficient edit-recovery screen](behavior-diagnostic-v2.md) passed its frozen gate: the focused prompt completed 9/9 initially wrong cases versus baseline's 7/9, with 3/3 passing controls preserved, two prefix wins and zero paired losses. The subsequent [four-issue real-development comparison](development-panel-v2.md) produced 0/4 verified repairs for both baseline-3m and edit-integrity-v1-3m. All four base/reference controls qualified. The candidate remains unpromoted; a synthetic gain has not established repair transfer.

The [first genuine weight construction/test](wsp-screen-v1.md) is now complete after Ultra confirmation. It used inspected numerical weights and a fixed static-prototype rank-one heuristic. Application and identity controls passed; the proposed edit completed 9/12 workflows, versus base/zero/random 10/12 and prompt 12/12. It produced one regression and no workflow wins. Reject this candidate and its real-task promotion. This tests one task-informed hypothesis, not the article's blind task-identification or game-network claims. The [paper draft](paper/draft.md) records the negative result; an original contribution remains unestablished. Paper entry still needs separate confirmation.

The [context check](development-context-v1.md) and [30-call control](development-tool-budget-v1.md) each produced 0/4 verified repairs on the same inspected issues. Neither encountered a context error or crossed the old input boundary. The 30-call arm reached verification on all four, but every trajectory used at most nine calls and failed its tests. Neither change establishes a repair gain. Retain the cheaper 8,192-token/ten-call control and stop cap tuning.

The requested-behavior candidate resolved `rich_2943` with a one-line fix after correctly locating the affected method. An exact public regression replay confirmed the fix. Both arms scored zero on issue-specific checks, and the candidate missed the promotion gate. Preserve the repair and consider localization to the named operation as a separate measurable workflow outcome. One historical draw per arm and different reported GPU devices limit attribution. [Behavior-check report](development-behavior-check-v1.md)

A single weight revision requires a stronger falsifiable account of actual model states and frozen controls by 7 November. Close that branch if this evidence is unavailable by the checkpoint. Freeze evidence and claims on 10 November and target a submitted Writeup on 11 November, ahead of the 12 November 23:59 UTC deadline. Preserve failures, restrict the study to one primary intervention plus at most one revision, and require frozen-candidate reserved evaluation for transfer claims. Any later weight stage requires Ultra confirmation.

## Budget constraint

Use the authorized `ach-bj100` Modal credit for initial remote experiments and available Kaggle quota for official-environment checks. First remote baseline allocation: at most USD 2 estimated usage. Preserve the remaining credit until throughput and compatibility are measured. Proposed additional-spending allocations, not price estimates: EUR 20 for feasibility, EUR 50 for the most useful follow-up runs, and EUR 30 reserved for final verification or a necessary rerun. Total actual additional compute/API charges must remain at or below EUR 100. Keep a spend ledger before launching jobs. Credit balance and quota availability must be verified; do not assume a new grant or reset.

Prefer one model, a small screening panel, and a few paired comparisons. Start with prompts/skills and retrieval, then one focused adapter experiment if deployment is proven. Broad RL, large synthetic-data generation, and full-model training are outside the initial plan. Reuse every measured run for diagnostics and, if justified, the paper.

The working research question is: can a small, targeted adapter correct a recurring agent failure and convert saved execution time into more successfully repaired issues?

## Prize opportunities and dates

- The official prize page lists a $10,000 award for the highest-ranking eligible E2B/E4B submission. It must be among the team's two selected final submissions. These entries remain eligible for the main awards and paper track.
- The paper track lists awards for best paper ($15,000), new resource ($10,000), and new application ($10,000). A reusable diagnostic/evaluation tool could support the resource category, but it needs a distinct contribution and experiments; packaging existing tools alone is not a convincing entry.
- Paper deadline: 12 November 2026, 23:59 UTC.
- Main entry deadline: 25 November 2026, 23:59 UTC.
- Main final deadline: 2 December 2026, 23:59 UTC.

Current small-model standings could not be retrieved in this investigation. This is a strategic preference, not evidence that the category is easy or an estimate of winning probability.

## First 48 hours: establish feasibility

1. Confirm competition entry, data/model access, and available GPU quota. Read the current downloaded harness documentation and validator before choosing an implementation.
2. Reproduce the official starter on at least one public task using the approved checkpoint and serving configuration. Check that the original/gold patch controls behave as expected before trusting local scores.
3. Smoke-test both a plain submission and a supported small-rank adapter. Verify that an adapter is actually applied. A local Transformers result alone does not establish compatibility with scored inference.
4. Build a fixed screening panel of roughly 20–30 public development issues. Reserve separate validation issues before inspecting results; use repository separation where feasible and document the limitations of small samples.
5. Record issue success, patch validity, runtime, generated tokens, repeated tool calls, parse errors, and whether tests were actually run. Separate infrastructure failures from model failures.
6. Inspect failed traces to identify the largest recoverable loss: localization, invalid tools, loops, patch generation, premature stopping, or weak reasoning. Compare current small-model standings once authenticated access is available.

Deliverable: a working baseline, deployment proof for adapters, and a ranked failure analysis. If serving is blocked, resolve that before training.

## Frozen evaluation boundary

`configs/evaluation-split.json`, frozen on 4 November, partitions all 129 public tasks using only instance IDs, repository names, and base commits. Its source SHA-256 identifies the exact task file. Requests `7505` and `7427`, including any shared base commits, are pilot cases because their verification behavior has been inspected. They are excluded from reserved validation.

Requests and Rich form the development pool; HTTPX and FastAPI are reserved for a repository-level transfer check. IDs are unique and shared repository/base-commit groups cannot cross partitions. Choose a bounded screening panel from development before adaptation. Do not inspect reserved problem statements, reference patches, tests, or agent outcomes to design prompts, select edits, or tune settings. Host-side verification data is used only to grade frozen candidates.

Report infrastructure qualification and exclusions, including the failed pilot controls; do not silently replace inconvenient issues or describe this selected pilot as an unbiased success-rate estimate. Keep time/hardware settings matched across comparisons and preserve exact candidate hashes. A budget adjustment becomes a separate experiment, with its own baseline at the same adjusted budget.

On 4 November, a [primary competition discussion](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747248) was retrieved through indexed text. Participants had already documented public-kit dependency/import-shadowing failures. Staff state that test-set repositories differ from all training repositories and that their gold-patch test submission validates fully. These are host statements, not our independent test-set validation. Our public-task environment failures therefore do not establish broken hidden scoring. Generic navigation and repair behavior must transfer beyond memorized public fixes; our reserved public-repository split is only a development proxy for that transfer.

## Experiments, in priority order

| Experiment | Question | Decision criterion |
| --- | --- | --- |
| Baseline vs compact skills and structured workflow | Does better use of the allowed tools improve repair success? | More validated repairs under the same wall-clock budget |
| Basic retrieval vs graph-assisted localization | Does graph context help find the actual edit location? | Localization and repair gains that outweigh added runtime |
| Baseline vs targeted LoRA training | Can verified successful traces correct the observed failure? | Improvement on reserved issues and compatibility with the official scorer |
| Baseline vs LLM-designed low-rank edit | Can a focused weight intervention correct that same failure? | Improvement beyond cheap prompt/sampling controls, without broad regressions |

Use only training/development information to construct updates. Do not expose reserved reference patches or evaluation-only tests to the agent. Check terms and organizer guidance before using proprietary teacher trajectories or model-generated weight edits.

For weight-space work, select one observed failure and a small number of supported target matrices. The linked article's directional column edit suggests a low-rank representation: a shared output direction times a vector selecting/scaling columns can be written as an outer product. This is a mathematical inference; it does not prove that Gemma has the same failure or that the serving stack accepts the relevant module. Derive and verify updates against the actual competition checkpoint.

Cap exploratory weight editing at roughly 10–20% of the experiment budget until it produces reproducible improvement. If the first focused experiment does not outperform ordinary controls on reserved issues, continue with workflow improvements and conventional adapters.

Keep the evaluation panel, budgets, checkpoint, and harness version fixed during comparisons. Rerun promising candidates with matched seeds and use a larger reserved panel before declaring a gain. Report paired wins/losses and uncertainty; a couple of extra solves in a tiny panel is a screening signal.

## Schedule and decisions

- 5–6 November: one context correction, genuine WSP inspection/attempt after Ultra confirmation, paper draft and fresh overlap review.
- By 7 November: first controlled WSP feasibility result and a fixed research direction; at most one documented revision, no new search branch.
- 8–9 November: freeze candidate, held-out/negative controls and required ablation/repeat within budget.
- 10 November: freeze evidence and claims, complete provenance and final novelty review.
- 11 November: review and submit the paper Writeup; verify submitted status. Reserve 12 November as buffer. A rigorous negative/feasibility result needs an original insight; setup work must not be presented as one.
- 13–26 November: improve the best small-model configuration using broader validation and measured time allocation. Avoid a larger-model branch unless free quota, deployment compatibility, and measured results justify it.
- 27 November–1 December: freeze candidates and complete clean end-to-end submission checks. Reserve a final selection for the eligible small-model candidate.
- By 2 December: verify selected final submissions before the deadline.

## Unresolved rules question — draft only, not posted

May we use a commercially available external LLM during development to inspect an approved Gemma checkpoint and design low-rank weight updates, then submit those updates solely as standard PEFT LoRA adapters on the approved base? No external model would run during scoring. Are there restrictions on how adapter weights are produced, or accessibility, disclosure, and redistribution requirements for this process and any teacher-generated traces?

## Sources

- [Official main competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview)
- [Official prizes and small-model eligibility](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview/prizes)
- [Staff update permitting smaller variants](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287)
- [Official paper track and judging criteria](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)
- [Official small-model leaderboard notebook](https://www.kaggle.com/code/ryanholbrook/gemma-4-developer-agent-small-model-leaderboard)
- [LoRA serving discussion, including staff response](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/749191)
- [External-teacher clarification request](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/745961)
- [Weight-space programming article](https://rikiyat.github.io/blog/weight-space-programming/)
