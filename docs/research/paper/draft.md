# From Weight Edits to Verified Repairs

## A controlled feasibility study of quantized Gemma coding agents

Internal draft, 5 November 2026. **Not ready for submission.** Task-directed weight
inspection/edit experiments remain pending. Working title and claims must follow the
results. Final Kaggle Writeup limit: 3,000 words. Author information is not yet finalized.

## Abstract — provisional

Direct weight editing by general-purpose language models raises a practical question:
can such interventions improve completed software repairs in a frozen quantized coding
agent? This study will compare a task-directed intervention with the unchanged model,
simple prompt controls and matched nonspecific interventions, while measuring both
local recovery behavior and independent repair verification. Preliminary engineering
work verifies adapter application through the approved Gemma 4 E4B serving path. A
prompt control improved synthetic recovery but produced no verified repair gain on a
four-issue development panel. The task-directed weight experiment and held-out results
are pending; no weight-space capability, repair improvement or novel mechanism is
claimed in this draft.

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

The planned intervention protocol requires confirmed Ultra before weight interpretation
or edit design, numerical inspection provenance, an explanation and predicted effect
before testing, and one primary intervention with at most one documented revision.
Exact tensors, controls and thresholds will be frozen separately after inspection.
Current behavioral traces are development feedback; a feedback-free claim is unavailable.

All compared study conditions will use the same corrected context/generation settings,
prompts where applicable, task budgets and verification process. Measurements will
include independently verified repairs, paired outcomes, targeted behavior, regressions,
tool/context errors, actual trace usage and compute cost. A candidate must be frozen
before any reserved issue content is inspected.

## Experiments and observed preliminary results

| Experiment | Observed result | Scope |
| --- | --- | --- |
| Zero/random adapter application | Fixed numerical/routing controls passed on Modal and Kaggle | Deployment only |
| Fresh-coefficient recovery screen | Prompt control 9/9 initially wrong cases versus baseline 7/9; both preserved 3/3 passing controls | Synthetic, shared templates |
| Fresh four-issue Rich comparison | 0/4 verified repairs for both prompts | Selected development cases, one draw per condition |
| Task-directed weight interpretation and edit | Pending | No capability result yet |
| Frozen-candidate reserved evaluation | Pending | No generalization claim yet |

In the real-task screen, each condition had three failed verified attempts and one
unverified budget termination. The edited-prompt condition also encountered a context
limit error; its recovered partial patch was still verified and failed. This prevents
a clean attribution to the prompt instructions alone. Raw traces expose navigation,
shared-budget exhaustion, destructive edits and visible-test success without satisfying
new behavior. These observations do not diagnose a weight defect.

The numerical-weight experiment, controls, repeats and reserved results must replace
the pending rows before any substantive WSP conclusion is written.

## Related work and claim boundary

Takehi et al. report direct weight reading/writing across several tasks, including a
Qwen reasoning-loop correction and a Gemma 3 math experiment without established
improvement. ValerioDolci reports Gemma 4 translation edits with controls. The csinva
autoresearch repository tests numerical-weight access against description-only controls.
An author model-card lead also concerns quantized coding-agent loop edits, but requires
full retrieval and attribution review. We cannot claim novelty merely from Gemma,
quantization, low-rank packaging or agent-loop correction.

Any final contribution must state the specific demonstrated insight beyond this work.
The [novelty register](../novelty.md) is rechecked at claim selection and before submission.
Reproduction and expected engineering functionality remain distinct from original work.

## Limitations and conclusion — pending final evidence

Current results are small development screens and deployment validation. A weight
benefit, semantic mechanism and held-out repair transfer remain untested. The final
paper must report null results and resource failures, identify exactly what the editing
model could observe, and avoid extrapolating from one checkpoint or tiny samples.
No conclusion about WSP success or failure is supported at this stage.

## References

1. [Takehi et al. — Sparks of Weight-Space Programming](https://rikiyat.github.io/blog/weight-space-programming/).
2. [ValerioDolci — frontier-weight-edit](https://github.com/ValerioDolci/frontier-weight-edit).
3. [csinva — weight-space-programming-autoresearch](https://github.com/csinva/weight-space-programming-autoresearch).
4. [LoopFix model-card lead — retrieval pending](https://huggingface.co/nitayrabi/Cyber-Tiel-Coder-35B-A3B-LoopFix-GGUF).
5. [Competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent/overview).

Internal evidence: [protocol](../weight-space-study-v1.md),
[adapter validation](../adapter-compatibility.md),
[synthetic screen](../behavior-diagnostic-v2.md),
[real-task screen](../development-panel-v2.md), [run ledger](../../operations/run-log.md).
