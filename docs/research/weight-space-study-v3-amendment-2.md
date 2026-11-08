# Weight-space study v3 — amendment 2: gradient-trained prompt-distillation baseline

Dated 8 November 2026 (UTC), written after the [v3 pass](wsp-v3-panel-result.md) and before any
training step. Requested to answer the obvious reviewer question: how does the training-free
closed-form edit compare with a conventional gradient-trained LoRA distilled from the same prompt?
Supplementary and comparative; it cannot change the v3 verdict. Parent:
[weight-space-study-v3.md](weight-space-study-v3.md).

## Baseline (frozen)

- **Matched capacity and site:** a rank-8, scale-1 LoRA on the same module as the edit
  (layer 29 `self_attn.o_proj`, input 4096, output 2560), simulated as an additive hook on the
  frozen quantized model during training, exported as standard PEFT bf16 factors.
- **Data (design cases only):** the 12 v2 prefix design cases and the 12 non-target design cases.
  Student context = wsp-base-v1 prompt. Targets: the edit-integrity prompt's greedy 48-token
  continuation for the 12 prefix cases (the teacher), and the base prompt's own greedy
  continuation for the 12 non-target cases (preservation). Loss: cross-entropy on target tokens.
- **Optimization:** AdamW, learning rate 2e-3, no weight decay, gradient clip 1.0, A initialised
  Kaiming-uniform with seed 20261108 and B = 0; each step uses 3 prefix and 3 non-target cases in a
  fixed cyclic order; at most 120 steps.
- **Stopping rule (mirrors the α rule):** every 20 steps, greedy 48-token first tool call on the 24
  design cases with the LoRA active; stop at the first checkpoint with `read_file` first in ≥ 11
  of 12 prefix cases and an unchanged first tool-call name in all 12 non-target cases. If none by
  step 120, the baseline is reported as **failed to train** and no panel is run. No
  learning-rate, rank, module or step-count changes after seeing results.

## Comparison panel (frozen)

The 36 v3 fresh cases, temperature 0, one deterministic draw (as v3). Arms: base, A (α = 4),
A− (sign-flipped), **distill** (the trained LoRA), prompt: 5 × 36 = 180 trajectories, one A10G batch.
Reported only: target completions, first-action rereads, non-target completions, paired
wins/losses of A versus distill. **Interpretation rule:** the edit is called comparable if A and
distill differ by at most 3 completed target workflows; otherwise the larger one is called better.
The v3 gates are applied to distill for information but are not a pass criterion.

## Limits

One training run, one draw, same synthetic behaviour and template family; the baseline's
hyperparameters were set once without tuning, so it may understate what tuned training achieves.
Design cases are few (24) and near-identical, which favours the closed-form edit's data
efficiency claim only if distill underperforms. Budget: training bound USD 0.77, panel bound
USD 0.99, CPU packaging USD 0.10; study cap USD 8 (estimated spend before this: ~USD 4.1).
