# A Training-Free Rank-One Prompt Distillation for a Quantized Gemma 4 Coding Agent: Controlled Evidence and Its Limits

Draft of 8 November 2026 (UTC), updated with the v4 competition-setting result. Kaggle Writeup limit: 3,000 words. Author information not yet
finalized. Pre-submission checks still open are listed at the end.

## Abstract

Small coding agents often fail at one step of the repair loop. We ask whether a closed-form,
rank-one weight edit can carry one such behaviour, rereading source after a failed partial-line
edit, into the competition's quantized Gemma 4 E4B through its standard PEFT-adapter path. The edit
uses the output shift between a prompted and an unprompted agent at one decision token, whitened by
background key statistics, and is installed as one rank-1 component of a rank-8 adapter on one
attention output projection. Under frozen protocols, a static-prototype edit and the same
activation-derived edit at strength 1 both failed. With strength chosen from design cases only, the
edit completed 21 and 23 of 24 target workflows in two greedy-decoding runs on fresh cases, versus 4-5
for the unchanged model and zero or norm-matched random adapters, and 0 for its sign-flipped copy; the
instruction prompt and a gradient-trained rank-8 LoRA each completed 24. Under temperature-0.7
sampling the result is not robust: one seed passed and one failed because the edit made the model emit
empty completions, and one was incomplete. In the competition's own setting (temperature 0.2, thinking
enabled) with independent per-trajectory seeds on 36 new cases, one batch passed (edit 15 of 24 versus
3 for base) and one did not (10 versus 6), so the effect is real in direction but not reliable;
the instruction prompt completed only 10-11. The method is prior work in model editing; the contribution is
a controlled deployment study with failures preserved. It covers one synthetic behaviour, not real repairs.

## 1. Introduction

System-prompt instructions cost context and are brittle for small models. Weight-space programming
proposes that a general-purpose model can read and rewrite weights directly [1]. We test a narrower,
checkable question under real deployment limits: the approved quantized E4B v2 checkpoint, the harness's
standard PEFT adapters, and vLLM serving. A design that only moves token statistics is not enough. We
require a change in a specific agent behaviour that survives that path, against controls that rule out
nonspecific perturbation, and we pre-register every gate.

## 2. Related work and claim boundary

The algebra is established. ROME [2] applies closed-form rank-one key-value edits. Steer2Edit [3]
(Sun, Yan, Wang, Weng) is a training-free framework that turns steering vectors into component-level
rank-1 weight edits. Mazzawi et al. [4] turn a prompt's influence into token-independent "thought
vectors and matrices" for reusable weight updates. Yin et al. [5] compile an activation-steering
direction into a persistent closed-form weight edit under a null-space constraint, for backdoor
injection. Gradient-trained prompt distillation into a LoRA is the standard alternative. [1] and
public follow-ups report LLM-directed weight edits. We claim no new editing method. Our contributions
are empirical: (i) a design-set-selected, covariance-whitened rank-one edit from prompt-versus-base
activations, deployed as a standard adapter on a quantized E4B; (ii) controls including a sign-flipped
and a norm-matched random edit and a gradient-trained baseline; (iii) a preserved record of failures,
including a decoding-regime failure that greedy evaluation hid. References [3-5] were checked at
abstract level only. We do not test blind weight reading or [1]'s other claims.

## 3. Method

**Behaviour.** After an edit leaves a syntax error, the base agent repeats a stale replacement; a
prompt saying "reread, then replace the whole line" makes it call `read_file` first. At the decision
token, 12 of 12 design cases reread under that prompt and 0 of 12 under the base prompt. Cases are
seeded synthetic tool sessions (an arithmetic `adjust` function) checked by a restricted interpreter and
the official editor; a workflow is complete only if the final source is correct, was tested after the
last edit, and was submitted.

**Construction.** On 12 design cases we replay each history under both prompts and record, at the last
token, the input `k` and output `o` of `self_attn.o_proj` in layers 12-38. With `d` the mean
prompted-minus-base output and `k*` the mean base input, the layer maximizing `||d|| / ||mean o_base||`
is used (layer 29, input width 4096). A ridge-regularized covariance `C` of that input over all tokens of
12 non-target design cases whitens the key: `dW = alpha d (C^-1 k*)^T / (k*^T C^-1 k*)`, so `dW k* = alpha d`.
It is one rank-1 component of a rank-8, alpha-8 bf16 adapter; the realized shift error is 0.17%.
Strength alpha is the smallest value in {2, 3, 4, 6, 8} for which greedy decoding on design cases rereads
in at least 11 of 12 target cases and leaves the first tool call unchanged in all 12 non-target cases
(alpha = 4). No evaluation case enters design or selection.

**Controls and baseline.** Base; zero adapter (same A, B = 0); seeded random adapter with matched factor
norms; sign-flipped edit; the prompt; a base repeat (v2). The gradient baseline is a rank-8 LoRA on the
same module trained on the same 24 design cases (teacher: the prompted agent's continuation; preservation
targets on non-target cases), stopped at the first checkpoint meeting the same design-set rule (step 40).
Application in vLLM was verified separately: active adapters shift first-token log-probabilities by
0.09-0.76 nats on three fixed prefixes with zero control drift.

**Protocols.** Each experiment was frozen, with cases, gates and budget hashed in a ledger before any
inference. Evaluation cases are seeded, disjoint from every earlier coefficient pair, and never used for design.

## 4. Results

**Failures first.** A static-prototype edit built from token embeddings completed 9 of 12 workflows
versus 10 for base and 12 for the prompt. The activation-derived edit at alpha = 1 (36 cases, 8 arms,
288 trajectories) completed 3 of 24 target workflows versus 4 for base, with no rereads, although it was
applied. A post-hoc diagnostic on those evaluation prompts showed the key fires (dot product 0.99) and the
log-probability margin grows monotonically with alpha, but alpha = 1 recovers about 6% of the prompt's
margin. That diagnostic motivated the alpha grid and is a disclosed researcher degree of freedom.

**Greedy decoding, fresh cases (alpha = 4).** Target workflows complete, of 24 (non-target, of 12, were
12 in every arm):

| Arm | Run 1 | Run 2 |
| --- | ---: | ---: |
| base | 5 | 4 |
| zero adapter | 5 | – |
| random, norm-matched | 4 | – |
| **edit** | **21** | **23** |
| sign-flipped edit | 0 | 0 |
| gradient-trained LoRA | – | 24 |
| prompt | 24 | 24 |

Run 1 (216 trajectories) passed all four pre-registered gates: the edit beat base, zero and random by net
+16, +16, +17 target workflows (one-sided exact sign tests, p < 1e-4), beat the sign-flipped edit by +21
and lost no non-target case. Run 2 (180 trajectories, a different arm mix) repeated the pattern. The same
adapters and settings gave 21 and 23, so greedy single-draw counts carry about +-2 serving noise. The
sign-flipped edit removed even the base's occasional successes, and the random edit disturbed token
statistics more than the real one without effect, so the gain is directional. Under the frozen
comparability rule (within 3 workflows) the edit is comparable to the gradient-trained LoRA (23 vs 24),
which trained in about five minutes; the edit's value is that it needs no optimizer, not accuracy.

**Sampling, temperature 0.7 (three seeds).** Seed 101: edit 24, base 18, sign-flipped 6, prompt 24 (pass).
Seed 103: edit 4, base 24, sign-flipped 0, prompt 24 (fail); in 20 of 24 target cases the edit's first
sampled completion was empty, one token and a stop. Seed 102 was incomplete (cancelled at 63 of 144 rows).
Robustness is therefore not established. Because every request in a batch shared one sampling seed and the
target contexts differ only in coefficients, each seed is close to one draw per arm; base rereads were 9
of 24 under seed 101 and 24 of 24 under seed 103. Within-seed counts are not independent samples.

**Competition setting, temperature 0.2 with thinking (v4).** To test the setting the main entry
runs in, we froze a further protocol: 36 new cases, temperature 0.2, top_p 0.95, thinking enabled,
independent per-trajectory sampling seeds, two batches (seeds 201, 202), the same alpha = 4 edit with
no re-tuning. Target workflows complete, of 24:

| Arm | Batch A | Batch B |
| --- | ---: | ---: |
| base | 3 | 6 |
| edit | 15 | 10 |
| sign-flipped edit | 2 | 4 |
| prompt | 10 | 11 |

Batch A passed every gate (edit beat base by net +12, p = 0.0002, and the sign-flipped edit by +13; one
non-target loss). Batch B failed the net-+6 gate (edit beat base by +4, p = 0.17). By the frozen rule
the outcome is mixed. The first action was `read_file` in 12 and 10 of 24 edit trajectories, against 6 and
5 for base and 18 and 21 for the prompt: the edit moves behaviour in the intended direction at roughly half
the prompt's strength. The empty-completion failure did not recur. Between 8 and 15 of 24 trajectories in
every arm, the prompt included, ended on the six-request budget, which caps completions in thinking mode.
Pooled counts (edit 25 of 48, base 9, sign-flipped 6, prompt 21) are descriptive only.

## 5. Limitations

One synthetic behaviour in one template family; fresh cases differ from design cases only in coefficients.
No real-repair claim: the edit has not been run on real issues, and earlier real-task screens of prompt
changes showed no repair gain. The competition's baseline agent samples at temperature 0.2 with a thinking
budget; v4 tested that setting, but the 4,096-token thinking budget was approximated by enabling thinking
with an 8,192-token output limit and was not separately enforced, and a six-request cap truncates
many thinking-mode trajectories in every arm. Non-target cases are at
ceiling (every arm, including the harmful sign-flipped edit, completes 12 of 12), so side-effect detection
is weak. Greedy single draws vary by about +-2 workflows. The gradient baseline used untuned
hyperparameters. We did not ablate numerical weight access, so we cannot say whether seeing weights helped
design. The edit uses activations from forward passes and was designed by an LLM assistant that knew prior traces.

## 6. Reproducibility

Protocols, case generators, adapter builders, ledger and hashed reports are in the repository. Runs used
Modal A10G with the competition's pinned wheels and `gemma-4-e4b-it-qat-w4a16-ct` v2, for about USD 11 in
total. Incidents are recorded: a lost terminal event in the first panel (gate recomputed from streamed rows
with unit-tested code), a batch cut by its execution limit, a report-path collision that forced a seed
rerun, and a cancelled batch.

## References

1. Takehi et al. Sparks of Weight-Space Programming, 2 Nov 2026. rikiyat.github.io/blog/weight-space-programming
2. Meng et al. Locating and Editing Factual Associations in GPT (ROME). arXiv 2202.05262.
3. Sun, Yan, Wang, Weng. Steer2Edit: From Activation Steering to Component-Level Editing. arXiv 2602.09870.
4. Mazzawi, Dherin, Munn, Goldwaser, Wunder, Gonzalvo. Transmuting prompts into weights. arXiv 2510.08734.
5. Yin et al. Compiling Activation Steering into Weights via Null-Space Constraints for Stealthy Backdoors. ACL 2026, pp. 26228-26245.
6. Competition overview: kaggle.com/competitions/gemma-4-developer-agent

## Open before submission

Read the full texts of [3-5]; confirm authors and affiliations; the user submits the Writeup on Kaggle
(draft Writeups are ineligible); decide whether to link public code.
