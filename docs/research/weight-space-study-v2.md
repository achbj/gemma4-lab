# Weight-space study v2 — pre-registration

Drafted 8 November 2026 (UTC), **before** any v2 case, activation or adapter exists.
It supersedes the revision limit and the 7 November stop date in the
[v1 protocol](weight-space-study-v1.md) by explicit user decision on 7–8 November: the first
edit failed, a defensible second construction is now available, and a larger panel is
affordable. Paper deadline 12 November 23:59 UTC (internal submit 11 November). The main
competition (entry 25 November, final 2 December) is **independent** of this study.

## What changed from v1, and why

v1's edit used static token embeddings as a stand-in for hidden states and failed its gate
(9/12 vs 10/12 base; prompt 12/12). The 7 November feasibility runs show we can read real
hidden states and attention-output inputs from the approved checkpoint with a plain forward
pass (`artifacts/activation-feasibility-v1/`; the first run's control failure was a missing
BOS token, fixed in the second). v2 therefore builds the edit from observed activations and
drops the blind-designer arm I considered: it would need a program-writing designer and a
mechanical resolver we cannot validate in three days. **No weights-visible-versus-hidden
claim will be made.** The numerical-access question stays open and is stated as a limitation.

## One question

Can a closed-form rank-one edit, built from activations that distinguish a prompted from an
unprompted agent at one decision point, reproduce that prompt's effect when deployed as a
standard rank-8 PEFT adapter on the quantized E4B, beyond zero, random, sign-flipped and
repeat-draw controls?

## Prior work this builds on (not claimed as ours)

ROME and MEMIT (closed-form rank-one/low-rank key-value edits), activation steering and
representation engineering (difference-of-means directions), refusal-direction weight
orthogonalization, context distillation, and the weight-space programming article plus the
overlapping repositories in [novelty.md](novelty.md). The algebra below **is** ROME's update
with activation-derived keys and values. Any contribution is limited to what the controls
below demonstrate in this deployment setting: transfer through quantized base + PEFT +
vLLM, and agent-loop workflow outcomes. All citations are rechecked before submission.

## Target behaviour and data

- **Target**: after a failed partial-line replacement leaves a syntax error, reread current
  source and replace the whole line (the `prefix_corruption` family). Earlier screens: base
  completed 1/3 in each of three 3-case screens; the edit-integrity prompt completed 3/3 and
  9/9 overall in v2. Headroom exists, and the prompt is the intended "teacher".
- **Design set (never evaluated)**: 12 `prefix_corruption` + 6 `failing_assertion` + 6
  `passing_control` cases. **Evaluation panel**: 24 `prefix_corruption` (target) + 6
  `failing_assertion` + 6 `passing_control` (non-target, regression check) = 36 cases.
  Coefficients come from one seeded generator, disjoint within the panel and from every
  coefficient in `behavior-diagnostic-v1/v2` and `wsp-screen-v1`; the generator, seed and
  full list are committed and hashed before any capture. Same six-action, 60-second,
  1,536-token, temperature-0 protocol as `wsp-screen-v1`.
- Reserved issues stay untouched. Real-task repairs are out of scope until the gate below passes.

## Construction (frozen before capture)

1. Replay each design-set case's seeded history to the first assistant turn after the error
   observation, once under the base prompt and once under the edit-integrity prompt, in
   Transformers with BOS and the official chat template. Record, at the last token of each,
   the input `k` (2,048-dim) and output `o` of `self_attn.o_proj` in every layer 12–38.
2. Per layer: `d = mean(o_prompt) − mean(o_base)`, `k* = mean(k_base)` over prefix design
   cases. **Layer rule (one, no behavioural tuning)**: pick `L*` maximizing
   `‖d‖ / ‖mean(o_base)‖` over layers 12–38.
3. Background covariance `C` of `k` at `L*` over all tokens of the 12 non-target design
   cases (+ ridge `1e-3·tr(C)/2048·I`).
4. `ΔW = α · d (C⁻¹k*)ᵀ / (k*ᵀ C⁻¹ k*)`, so `ΔW k* = α d`. Primary `α = 1`.
5. Encode as rank-1 inside rank-8/alpha-8 PEFT on `L*`'s `o_proj` (same route as the v1
   adapter; seven components zero). No gradient step anywhere.

**Arms** (all use the base prompt unless noted): base; base-repeat (noise floor); zero adapter;
random adapter (seeded, delta norm matched to `ΔW`); **A** (primary, `α = 1`); **A−**
(sign-flipped `d`, same norm); static-prototype v1 edit (`wsp_read`, re-run on the new
panel); prompt (edit-integrity, no adapter). Condition order rotates by case. 8 arms × 36
cases = 288 trajectories.

## Controls and gates (decided now)

Application, in vLLM before the panel: fixed 3-prefix log-probability shift of A, A− and
random vs zero ≥ 0.001 nats with repeated-base drift ≤ 0.05 nats (reused thresholds), and
a vLLM-versus-Transformers top-1 log-probability comparison on those prefixes (diagnostic
only; reported, not a gate).

**Primary success** requires all of:
1. All 288 trajectories valid and every non-target passing control preserved by A.
2. On the 24 target cases, A beats each of base, base-repeat, zero and random with ≥ 6 net
   paired workflow wins and one-sided exact sign-test p < 0.05 for each.
3. A's net advantage over A− is ≥ 4 target cases (directional specificity).
4. A has ≤ 1 paired loss to base on the 12 non-target cases.

Prompt and v1 edit are reported against A but are not gates. If the base/base-repeat
disagree on more than 3 cases, no effect smaller than that noise is interpreted.

**One revision, pre-specified**: if A shows a detected application effect but fails gate 2
only by margin, rerun once with `α = 2` at the same `L*` (new ledger entry, same panel, same
controls with norms rescaled). If that fails or application is undetectable, **close the
weight branch** and report the negative result with all arms. No layer, rank or module
sweep.

## What follows each outcome

- **Pass**: report as a deployment-constrained replication of keyed rank-one editing for
  agent workflow, not as a new editing method; run the real-task development panel once
  (budget below) before any repair claim. No main-track promotion unless it beats
  `wsp-base-v1` on held-out issues, which is unlikely before 25 November.
- **Fail**: paper reports the prompt-to-weights gap honestly: the activation-informed edit
  fails to reproduce a prompt that works, with full controls. Combined with v1's static
  failure this characterizes what does and does not transfer; novelty remains modest.
- Either way the main submission stays the best measured prompt/workflow candidate.

## Budget, rules, schedule (UTC)

- Workspace `onepiecification` only. Planned estimated compute: capture ≈ USD 0.30, vLLM
  application + parity ≈ USD 0.60, main panel ≈ USD 1.50, optional `α = 2` rerun ≈ USD 1.50,
  optional real-task pair ≈ USD 2.80. Study cap **USD 8**, inside the EUR 100 ceiling; each
  job gets its own current-rate ledger entry first. Workspace credit is unverified.
- Rules: main/paper §2.6 allow external development tools; edit design by Claude (this
  session, `xhigh`) is recorded, no paid API, submitted artifacts are standard PEFT only.
  Information available to the designer: architecture, tensor shapes, activations on the
  design set, prior traces. Not feedback-free discovery.
- 8 Nov: freeze this document, generate and hash cases. 9 Nov: capture, build adapters,
  application controls, main panel. 10 Nov: optional `α = 2`, freeze evidence, final novelty
  recheck. 11 Nov: submit Writeup, verify status. 12 Nov: buffer. Paper Track entry still
  needs your manual confirmation.
