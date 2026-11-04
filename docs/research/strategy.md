# Gemma 4 prize strategy

Decision brief, 4 November 2026. The user set a compute/API spending ceiling of EUR 100 and selected the `ach-bj100` Modal workspace, reporting USD 30 in existing credit. Modal identity and Kaggle competition access have been verified. See [the working agreement](../../AGENTS.md) for the Ultra checkpoint before interpreting or editing weights, and [the run log](../operations/run-log.md) for execution/budget status.

## Recommended direction

Build an E4B coding agent, switching to E2B if serving compatibility or measured throughput warrants it. Avoid a broad model sweep on this budget. Target the small-model award first. Use the same experiments and reusable evaluation tools for a paper-track submission if the evidence is strong enough before its deadline.

Treat weight-space programming as a bounded research experiment within this project. Do not make the entire competition attempt depend on it working.

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

- 4–5 November: baseline, adapter deployment checks, failure analysis.
- 6–9 November: compare the simplest fixes; run one bounded weight-editing experiment if a suitable failure exists.
- 10 November: decide whether there is a distinct, supported paper contribution. If yes, freeze the paper experiments and document data provenance, costs, controls, and limitations.
- 11–12 November: finish and submit the paper/resource entry. A draft is insufficient. If evidence is weak, prioritize the main entry instead of inventing a result.
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
