# Weight-space study v3 — amendment 1: sampling-seed robustness

Dated 8 November 2026 (UTC), written **after** the [v3 panel passed](wsp-v3-panel-result.md) and
**before** any sampled trajectory exists. Requested by the user as the first extension. It is
supplementary: it cannot change the v3 verdict, add arms to the gate, or authorize any change
of α, layer, rank or construction. Parent protocol: [weight-space-study-v3.md](weight-space-study-v3.md).

## Question

Does the v3 effect survive stochastic decoding, or was it an artifact of one deterministic
temperature-0 draw?

## Design (frozen)

- Same 36 v3 evaluation cases, the same packaged adapters at α = 4
  (`artifacts/wsp-v2-prepare/20261107T234544Z-alpha4p0/`), same prompts, tools, six-action,
  60-second, 1,536-token protocol.
- Temperature **0.7**, top-p 0.95, per-request sampling seeds **101, 102, 103**.
- Arms: base, A (α = 4), A− (sign-flipped), prompt (edit-integrity). Zero and random are not
  re-run: at temperature 0 base and zero agreed exactly and random was inert; stated as a limit.
- 4 arms × 36 cases × 3 seeds = 432 trajectories, one A10G batch.

## Analysis (frozen)

For **each seed separately**, apply the v3 gate form on the arms present: valid coverage;
A completes all six passing controls; A beats base on the 24 target cases with ≥ 6 net paired
wins and one-sided exact sign-test p < 0.05; A beats A− by ≥ 4 target cases; A loses ≤ 1
non-target case to base (application result reused from the v3 run). **The effect is called robust
if all three seeds pass.** Also reported, not gating: target completions and first-action
rereads per arm per seed, and A versus prompt. A seed that fails is reported as failed;
no seed is dropped, replaced or re-run.

## Limits

The cases are the v3 cases (already evaluated once), so this tests decoding variance, not case
sampling; seeds are not independent samples of the task distribution. Non-target cases remain
near ceiling. No claim extends beyond the one synthetic behaviour. Budget: one A10G batch, bound
USD 0.99, inside the v3 cap.
