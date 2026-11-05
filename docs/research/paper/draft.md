# From Weight Edits to Verified Repairs

## A controlled feasibility study of quantized Gemma coding agents

Internal draft, 5 November 2026. **Not ready for submission.** The first task-directed
weight edit failed its behavioral gate. An original contribution and held-out evidence
remain unestablished. Final Kaggle Writeup limit: 3,000 words. Author information is
not yet finalized.

## Abstract — provisional

Direct weight editing by general-purpose language models raises a practical question:
can such interventions improve completed software repairs in a frozen quantized coding
agent? We tested one static-prototype rank-one intervention against the unchanged model,
zero and norm-matched random edits, and a prompt control on 12 inspected synthetic
recovery cases. Numerical controls confirmed application, but the proposed edit completed
9/12 workflows versus 10/12 for base/random and 12/12 for the prompt. All passing
controls were retained. An earlier four-issue development panel found no verified repair
gain from the prompt. The proposed weight edit failed its prerequisite gate and was not
advanced to real repairs. These small feasibility results establish neither a general
weight-space capability conclusion nor a novel mechanism.

## Introduction

Software-repair agents must navigate repositories, edit source, test relevant behavior
and submit a valid patch within limited resources. Improved behavior in a small
continuation task may not improve end-to-end repairs. Quantized deployment adds a
further requirement: an intervention must actually be applied through the scored
serving route without changing the approved base model.

Weight-space programming offers a possible development method: a general-purpose
model reasons about numerical parameters and writes a deliberate intervention without
gradient training. Published examples differ in scale, information access and feedback.
We do not assume that success on small game networks transfers to a pretrained Gemma
coding agent. Our research question is whether a specific intervention produces a
controlled, useful effect that survives deployment and transfers to verified repairs.

## Methods — completed and planned work

Completed engineering uses the approved E4B version-2 quantized checkpoint, official
compiler/ADK/tool wheels and standard PEFT packaging. A zero/random diagnostic adapter
pair was checked on Modal A10 and the official Kaggle image with L4x4. This demonstrates
the tested routing and numerical application, not semantic understanding of weights.

Public development tasks are separated from 68 reserved issues by repository/base
commit metadata. Model inputs exclude reference solutions and verification-only tests.
Each real-task fixture must distinguish the unchanged checkout from its reference
patch before agent outcomes are interpreted. Runtime adaptations and all exclusions
are recorded; local development evaluation is not claimed to be full hidden-scorer parity.

The editor inspected numerical projection statistics, learned gains and derived label
prototypes after checking all eight base-file hashes. The fixed construction uses the
final attention output projection and its shared layer-23 value source. It maps learned
embeddings for error/ok through the source value path, orthogonalizes the error prototype
against ok, and adds a rank-one output change toward a gain-adjusted read_file/edit_file
embedding difference. The delta norm is fixed at 1% of the decoded output matrix norm,
represented in rank-8/alpha-8 PEFT. A zero edit and one seeded random edit with matched
stored factor/delta norms control application and nonspecific perturbation.

These static token prototypes approximate deep-layer inputs; no actual hidden-state
detector or causal defect was established. Construction used no gradients or full-model
forward passes, but did include four linear value projections of label prototypes.
The editor knew architecture, labels and prior behavioral development traces, so this is
task-informed editing rather than blind weight reading or feedback-free discovery.
The proposal, controls, thresholds and budget were recorded before inference. One primary
intervention and at most one documented revision bound the search; no revision is selected.

The synthetic screen used the same 1,536-token/six-action/60-second protocol for all
five conditions, rotating their order by case. This differs from the full-agent study's
shared 8,192-token context correction, which has passed compilation but not real-task
admission/repair evaluation. A candidate must be frozen before reserved content is inspected.

## Experiments and observed preliminary results

| Experiment | Observed result | Scope |
| --- | --- | --- |
| Zero/random adapter application | Fixed numerical/routing controls passed on Modal and Kaggle | Deployment only |
| Fresh-coefficient recovery screen | Prompt control 9/9 initially wrong cases versus baseline 7/9; both preserved 3/3 passing controls | Synthetic, shared templates |
| Fresh four-issue Rich comparison | 0/4 verified repairs for both prompts | Selected development cases, one draw per condition |
| Task-directed static-prototype weight edit | Base/zero/random 10/12, proposed edit 9/12, prompt 12/12; all 60 trajectories valid | Failed specific synthetic hypothesis; no real-repair promotion |
| Frozen-candidate reserved evaluation | Pending | No generalization claim yet |

In the real-task screen, each condition had three failed verified attempts and one
unverified budget termination. The edited-prompt condition also encountered a context
limit error; its recovered partial patch was still verified and failed. This prevents
a clean attribution to the prompt instructions alone. Raw traces expose navigation,
shared-budget exhaustion, destructive edits and visible-test success without satisfying
new behavior. These observations do not diagnose a weight defect.

The weight screen had exact base/zero action/source/workflow agreement, zero measured
token-control drift and detected effects from both active edits. All three compiled
adapter routes responded. Despite application success, the proposed edit produced zero
paired workflow wins, one loss and zero first-action source rereads on the three prefix
cases. Its regression alternated failed replacements and rereads without fixing the
observed corrupted line. The prompt completed all three. Application is therefore
insufficient evidence for this construction's intended behavioral effect. This single
heuristic does not test the published blind task-identification or game-network claims.

## Related work and claim boundary

Takehi et al. report direct weight reading/writing across several tasks, including a
Qwen reasoning-loop correction and a Gemma 3 math experiment without established
improvement. ValerioDolci reports Gemma 4 translation edits with controls. The csinva
autoresearch repository tests numerical-weight access against description-only controls.
An author model-card lead also concerns quantized coding-agent loop edits, but requires
full retrieval and attribution review. We cannot claim novelty merely from Gemma,
quantization, low-rank packaging or agent-loop correction. Rank-one model rewriting is
also established prior work, including ROME; our prototype heuristic is not ROME.

Any final contribution must state the specific demonstrated insight beyond this work.
The [novelty register](../novelty.md) is rechecked at claim selection and before submission.
Reproduction and expected engineering functionality remain distinct from original work.

## Limitations and conclusion — pending final evidence

Current results concern small inspected templates, one checkpoint, one edit strength,
one random direction and one deterministic draw. The proposed weight benefit failed
its synthetic test; semantic selectivity and held-out repair transfer remain unestablished.
No numerical-access ablation isolates whether inspecting weights improved edit design.
A negative feasibility result alone does not establish an original prize-worthy insight.
The final paper needs a defensible contribution, appropriate confirmation and final
prior-work review. No general conclusion about WSP success or failure follows here.

## References

1. [Takehi et al. — Sparks of Weight-Space Programming](https://rikiyat.github.io/blog/weight-space-programming/).
2. [ValerioDolci — frontier-weight-edit](https://github.com/ValerioDolci/frontier-weight-edit).
3. [csinva — weight-space-programming-autoresearch](https://github.com/csinva/weight-space-programming-autoresearch).
4. [LoopFix model-card lead — retrieval pending](https://huggingface.co/nitayrabi/Cyber-Tiel-Coder-35B-A3B-LoopFix-GGUF).
5. [Competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview).
6. [Meng et al. — Locating and Editing Factual Associations in GPT (ROME)](https://arxiv.org/abs/2202.05262).

Internal evidence: [protocol](../weight-space-study-v1.md),
[adapter validation](../adapter-compatibility.md),
[synthetic screen](../behavior-diagnostic-v2.md),
[real-task screen](../development-panel-v2.md), [first designed weight edit](../wsp-screen-v1.md),
[run ledger](../../operations/run-log.md).
