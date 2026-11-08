# A Training-Free Rank-One Prompt Distillation for a Quantized Gemma 4 Coding Agent

## Controlled evidence, including two failures, from a frozen-protocol study

Draft of 8 November 2026. Final Kaggle Writeup limit: 3,000 words. **Pending items are marked
[PENDING]; nothing marked so is established.** Author information not yet finalized.

## Abstract

Small coding agents often fail at a specific step of the repair loop. We ask whether a
closed-form, rank-one weight edit can carry one such behaviour, rereading source after a failed
partial-line edit, into a quantized Gemma 4 E4B served through the competition's standard
PEFT-adapter path. The edit uses the output shift between a prompted and an unprompted agent at
one decision token, whitened by background key statistics, and is installed as a rank-1 component
of a rank-8 adapter on one attention output projection. Two earlier constructions failed under
frozen gates (a static-prototype edit and the same activation-derived edit at strength 1). With
the strength selected from design cases only and a fresh 36-case panel, the edit completed 21 of
24 target workflows versus 5 for the unchanged model, 5 for a zero adapter, 4 for a norm-matched
random adapter and 0 for its sign-flipped copy; the instruction prompt completed 24. [PENDING:
sampling-seed robustness and a gradient-trained distillation baseline.] The construction is prior
work in steering and model editing; our contribution is a controlled deployment study with its
failures preserved. It covers one synthetic behaviour, not real repairs.

## 1. Introduction

Instructions in a system prompt cost context and are fragile for small models. Weight-space
programming proposes that a general-purpose model can read and rewrite weights directly [1]. We
study a narrower, testable question under real deployment limits: the approved E4B v2 quantized
checkpoint, the harness's standard PEFT adapters, and vLLM serving. A design that only changes
token statistics is not enough; we require a change in a specific agent behaviour that survives
that path, against controls that rule out nonspecific perturbation.

## 2. Related work and claim boundary

The algebra is established. ROME [2] applies closed-form rank-one key-value updates. Steer2Edit [3]
converts mean-difference steering vectors into closed-form rank-one component edits;
Mazzawi et al. [4] argue that a prompt's effect on a block equals ROME-like rank-one updates; Yin
et al. [5] compile steering directions into closed-form, null-space-constrained edits; gradient
prompt-distillation into LoRA is a standard alternative. The weight-space-programming article [1]
and two public follow-ups report LLM-directed weight edits. We claim no new editing method. Our
contributions are empirical: (i) a design-set-selected, whitened rank-one edit from
prompt-versus-base activations deployed as a standard adapter on a quantized E4B; (ii) controls
including a sign-flipped and a norm-matched random edit; (iii) a record of what failed first.
Related-work search was rechecked on 8 November 2026 from search summaries; full texts of [3-5]
must be read before submission. We do not test blind weight reading or the article's other claims.

## 3. Method

**Behaviour.** After an edit leaves a syntax error, the base agent repeats a stale replacement; a
prompt instructing "reread, then replace the whole line" makes it call `read_file` first. In
replays at the decision token, 12 of 12 design cases reread under that prompt and 0 of 12 under the
base prompt. Cases are seeded synthetic tool sessions (an arithmetic `adjust` function) scored by a
restricted checker and the official editor; a workflow is complete only if the final source is
correct, was checked after the last edit, and was submitted.

**Construction.** On 12 design cases we replay each history under both prompts and record, at the
last token, the input `k` and output `o` of `self_attn.o_proj` in layers 12-38. With `d` the mean
prompted-minus-base output and `k*` the mean base input, the layer maximizing
`‖d‖/‖mean o_base‖` is chosen (layer 29, input width 4096). A ridge-regularized covariance `C` of
that layer's input over all tokens of 12 non-target design cases whitens the key:
`ΔW = α d (C⁻¹k*)ᵀ / (k*ᵀC⁻¹k*)`, so `ΔW k* = α d`. It is stored as one rank-1 component in a
rank-8, alpha-8 PEFT adapter, bf16. Realized shift error after rounding is 0.17%.

**Controls.** Base; a zero adapter (same A, B = 0); a seeded random adapter with matched factor
norms; the sign-flipped edit; the prompt; base repeat. Application was verified separately in vLLM:
all active adapters move first-token log-probabilities by 0.09-0.76 nats on three fixed prefixes
with zero control drift, so an unapplied adapter is excluded.

**Protocols.** Each experiment was frozen, with gates, thresholds, cases and budget, and hashed in a
ledger before any inference. Evaluation cases are seeded, disjoint from every earlier coefficient
pair, and never used for design.

## 4. Results

**Failure 1 (v1).** A static-prototype edit built from token embeddings completed 9 of 12
workflows versus 10 for base and 12 for the prompt; rejected.

**Failure 2 (v2).** The activation-derived edit at α = 1 on 36 panel cases (288 trajectories, 8
arms) completed 3 of 24 target workflows versus 4 for base, with zero rereads; the gate failed
although the adapter was applied. A post-hoc diagnostic showed the key fires on evaluation prompts
(dot product 0.99) and the effect is monotone in α but α = 1 recovers about 6% of the prompt's
log-probability margin. This diagnostic used evaluation prompts and is reported as exploratory.

**Pass (v3).** A second protocol changed only α, chosen by a frozen rule on design cases (smallest
α in {2, 3, 4, 6, 8} with ≥ 11/12 design prefix cases rereading and 12/12 non-target first actions
unchanged): α = 4. On 36 fresh cases (216 trajectories, temperature 0):

| Arm | Target complete (of 24) | First action = reread | Non-target (of 12) |
| --- | ---: | ---: | ---: |
| base | 5 | 0 | 12 |
| zero adapter | 5 | 0 | 12 |
| random, norm-matched | 4 | 0 | 12 |
| **edit (α = 4)** | **21** | **20** | **12** |
| sign-flipped edit | 0 | 0 | 12 |
| prompt | 24 | 24 | 12 |

The edit beat base, zero and random by net +16, +16, +17 target workflows (one-sided exact sign
tests p < 1e-4) and the sign-flipped edit by +21; it lost no non-target case. The sign-flipped
edit removed even the base's occasional successes, and the random edit perturbed token statistics
more than the real one without effect, so the gain is directional and specific.

**Robustness [PENDING].** [Sampling at temperature 0.7 over seeds 101-103: per-seed gates.]

**Distillation baseline [PENDING].** [A rank-8 LoRA at the same module trained by gradient descent on
the same design cases: target completions versus the edit.]

## 5. Limitations

One synthetic behaviour in one template family; fresh cases differ from design cases only in
coefficients. No real-repair claim: the edit has not been tested on real SWE issues, and earlier
real-task screens of prompt changes showed no repair gain. Non-target cases are at ceiling (every
arm, including the harmful sign-flipped edit, completes 12 of 12), so side-effect detection is weak.
The prompt still outperforms the edit, so its value is removing an instruction, not exceeding one.
The strength range was motivated by a post-hoc diagnostic on earlier evaluation prompts, a researcher
degree of freedom; selection itself used design cases only and testing used fresh cases. Single
checkpoint, single draw per arm at temperature 0 in the primary result. Numerical access to weights
was not ablated, so we cannot say whether seeing weights helped the design. The edit uses
activations from forward passes and was designed by an LLM assistant with knowledge of prior traces.

## 6. Reproducibility

All protocols, case generators, adapter builders, ledgers and hashed reports are in the repository;
runs used Modal A10G with the competition's pinned wheels and the approved
`gemma-4-e4b-it-qat-w4a16-ct` v2 checkpoint, spending about USD 5-6 in total. The first run's
final summary event was lost to a size limit and its gate recomputed from streamed rows with the
unit-tested code; this is noted in the record.

## References

1. Takehi et al. Sparks of Weight-Space Programming, 2 Nov 2026. rikiyat.github.io/blog/weight-space-programming
2. Meng et al. Locating and Editing Factual Associations in GPT (ROME). arXiv 2202.05262.
3. Steer2Edit: From Activation Steering to Component-Level Editing. arXiv 2602.09870.
4. Mazzawi et al. Transmuting prompts into weights. arXiv 2510.08734.
5. Yin et al. ACL 2026, arXiv-listed paper on compiling steering directions into weight edits (aclanthology.org/2026.acl-long.1206).
6. Competition overview: kaggle.com/competitions/gemma-4-developer-agent
