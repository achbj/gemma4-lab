# Novelty register

Last checked: 4 November 2026. Status: exploratory; no novel result has been demonstrated. A search cannot establish that an idea is absent from all prior work or guarantee that nobody publishes before our submission.

## Verified overlapping work

| Primary source | What is already covered | Consequence for our claims |
| --- | --- | --- |
| [Takehi et al., Sparks of Weight-Space Programming](https://rikiyat.github.io/blog/weight-space-programming/) (2 November 2026) | Frontier-model reasoning over weights and direct edits, including a Qwen looping correction; also a Gemma experiment without an established improvement. | We cannot claim to invent LLM-directed weight editing or assume that it transfers to Gemma coding agents. |
| [ValerioDolci/frontier-weight-edit](https://github.com/ValerioDolci/frontier-weight-edit), README blob `08ecf4d1a88a3cd6af851dc7d7fd3f3fced353ab` | Reports Gemma 4 12B translation edits, prompt/ablation/LoRA comparisons, held-out controls, and a separate Qwen edit surviving Q4_K_M quantization. These are author-reported experiments, not independently validated here. | Neither using Gemma, comparing with LoRA, nor demonstrating some quantization survival is sufficient novelty by itself. |
| [Program-as-Weights](https://arxiv.org/abs/2607.02512) (2 July 2026) | A trained compiler produces parameter-efficient programs for a frozen interpreter. | Generating adapters from a natural-language specification is established adjacent work; distinguish its trained compiler from direct editing. |
| [csinva/weight-space-programming-autoresearch](https://github.com/csinva/weight-space-programming-autoresearch) | Public autonomous weight-programming experiments were surfaced by search. Detailed audit remains pending. | A generic editing harness or autoresearch loop must not be presented as a new contribution without comparison. |
| [Public grader/environment discussion](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747248) and its linked grader-rebuild notebook | Participants already report missing dependencies, package shadowing, and false positives on Requests, including `requests_7427`. This primary discussion was retrieved through indexed text on 4 November; the linked rebuild has not been audited here. | Our rediscovery and import-path correction are development validation, not an original resource contribution. |

We still need a focused review of model editing and activation-steering literature before freezing any mechanism-level claim. Existing low-rank factorization is a deployment format, not our research novelty.

## Pilot status on 4 November

The [baseline and pagination comparison](baseline.md#matched-pilot-prompt-control-no-repair-gain) produced zero successful repairs in both conditions on one selected issue. Generic pagination instructions reached an edit but introduced regressions. This is setup/development evidence, not a novel method, a successful intervention, or a weight-level finding. No weight analysis or edit has been performed. Broader matched controls and a fresh related-work review are required before choosing a paper claim; the Ultra checkpoint remains mandatory before weight work.

Public [time/budget/thinking experiments](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/747696) also surfaced on 4 November. Detailed audit is pending; a generic task-budget or reasoning-budget comparison must not be described as novel without it.

The subsequent [fixed development panel](development-panel-v1.md) retained two qualified Rich cases and excluded two Requests cases after host-side controls. Both candidates solved 0/2. No repair gain, cross-repository transfer, or weight-level contribution follows from that result; the repository's infinite-loop task is not a model-weight diagnosis.

The matched three-minute follow-up on 4 November again produced 0/2 repairs for each condition, despite removing session timeouts in these draws. Traces expose dismissed failing tests, exhausted tool-call budgets, and an analyzer's unavailable-tool call. These are behavioral development observations, not a novel method or a causal weight explanation. Generic prompt/workflow controls and scorer-compatible adapter validation must precede any weight-intervention claim; no original paper contribution is established.

The feedback-only prompt screen on 4 November also solved 0/2 against that historical baseline. One case passed its visible tests but failed independent verification; the other attempted corrections/retesting but still submitted a syntax error. This single development screen does not establish a causal mechanism, repair gain, or novelty. The pinned adapter interface was audited without tensor work; runtime compatibility remains unverified.

The subsequent [controlled adapter probe](adapter-compatibility.md) established application through the pinned Modal compiler/resolver/serving path for one rank-8 E4B projection. Zero/base controls matched in the measured lists, all three active effects passed the fixed threshold, and both compiled-agent routes responded. This verifies documented LoRA functionality for the tested configuration; it is an engineering prerequisite, not a novel method, repair improvement, or causal circuit result.

On 5 November, the identical package also passed on the official Kaggle image with L4x4/tensor parallelism 4, with all source/checkpoint/wheel hashes and fixed controls retained. This clears the tested inference deployment prerequisite. Full SWE judging and useful repair gains remain unmeasured; the environment check adds no novelty claim. Recheck prior work when selecting a distinct behavioral/weight-intervention claim and again before submission.

Also on 5 November, the [paired synthetic diagnostic](behavior-diagnostic-v1.md) found identical correctness/workflow counts for the baseline and feedback-only prompts: seven of nine initially wrong cases and all three passing controls per condition. Both failed the same two prefix-corruption cases. This is a small, inspected development diagnostic using native editing and a restricted arithmetic checker; it is not a new method/resource claim, a competition repair gain, or weight-level evidence. Generic rereading and full-line replacement instructions are simple controls to test before selecting any intervention. This experiment update is not a new prior-work search; the claim-selection and pre-submission reviews remain required.

The subsequent [fresh-coefficient screen](behavior-diagnostic-v2.md) produced two paired workflow wins and zero losses for the reread/full-line prompt, preserving all passing controls. It passes its prespecified synthetic gate but establishes no SWE repair transfer. The two jointly changed instructions are ordinary prompt/workflow controls, not a novel method. Fresh real-development controls and matched inference are required before promotion. No new prior-work search or weight analysis occurred in this phase; claim-selection and final reviews remain pending.

The following [four-issue development comparison](development-panel-v2.md) produced 0/4 verified repairs for both prompts, with all base/reference controls qualified. It exposed tool-budget/navigation failures, false confidence from visible tests, and a context/output allocation error. These are engineering/development observations, without established repair transfer, a causal weight explanation, or an original method/resource claim. The synthetic prompt remains unpromoted. A new prior-work review is still required when selecting any paper claim and immediately before submission; no such claim was selected in this phase.

An additional author-post lead surfaced on 4 November: [Scaffolding helps the smallest Gemma 4 agent, not the larger ones](https://medium.com/@toeda/scaffolding-helps-the-smallest-gemma-4-agent-not-the-larger-ones-63da369962b0). Full review is pending; no results from that post are relied on here. Include it in the next claim-time review rather than treating generic E4B scaffolding or prompt controls as novel.

## Candidate research question

Do targeted weight interventions improve multi-turn software-repair success under a fixed inference-time budget, and do any behavioral gains transfer across repositories through the competition's quantized-base-plus-adapter serving path?

This is a question to test, not a novelty or performance claim. Possible useful findings include a repeatable gain, a measured failure to transfer, or evidence that fewer loops/invalid tools fail to improve completed repairs. A negative result needs a meaningful, well-supported insight to be competitive.

## Evidence required to support a contribution

1. An observed recurring agent failure and a clearly specified intervention, developed without viewing reserved reference patches or evaluation-only tests.
2. Comparisons against the unchanged agent, simple prompt/decoding/workflow fixes, and conventional LoRA where affordable and applicable. Match resource budgets and report development cost as well as inference cost.
3. Held-out issue and repository results, paired outcomes and uncertainty, multiple runs where stochastic variance matters, and regressions on unaffected tasks.
4. Evidence that the deployed adapter has the intended effect in the actual serving path. Proxy improvements, such as fewer repeated commands, cannot substitute for verified repairs.
5. A precise statement of what is new relative to the sources above. Do not use a “first” claim without a much broader supporting review.

## Recheck and claim decisions

- Recheck at experiment selection, before writing the main paper claim, and immediately before submission. Search both the method and its practical equivalents: LLM-directed model editing, generated adapters, agent loop/tool-call repair, quantized model editing, and coding-agent interventions.
- Search original papers, author repositories, and competition discussions; record the date and directly overlapping results. Social/news summaries are leads, not evidence for technical claims.
- If new work covers the proposed contribution, cite it and narrow the claim or change the paper's emphasis. Do not manufacture a novelty distinction based on a model name alone.
- Keep our submission itself original and unpublished as required. Cite prior methods and reproduce their baselines honestly. Public prior work does not automatically disqualify our own distinct empirical contribution.
- Paper deadline remains 12 November 2026 at 23:59 UTC, subject to host updates. No paper draft or original result exists yet.
