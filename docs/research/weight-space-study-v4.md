# Weight-space study v4 — competition-setting robustness

Dated 8 November 2026 (UTC). Frozen before any v4 inference. Supplementary to the v3 verdict, which is unchanged.

**Why.** v3 passed under greedy decoding but failed one of three seeds at temperature 0.7 (empty completions), shared one sampling seed per batch, and never used the competition's setting (temperature 0.2, top_p 0.95, thinking enabled; `submissions/wsp-base-v1/configs/sampling.yaml`). The user approved one more bounded round on 8 November; the cap for it is USD 6.

**Source/rule.** Competition rules and baseline sampling config as recorded in `rules-and-decisions.md` and `baseline.md`. Interpretation: vLLM `chat_template_kwargs.enable_thinking = true`, `max_tokens` 8192 and the harness reasoning parser stand in for "thinking budget 4096"; a separate token budget is **not enforced** (disclosed deviation).

**Change tested.** The same v3 edit (alpha = 4, chosen from design cases in v3; no re-selection, no new alpha) against base, the sign-flipped edit and the instruction prompt. Fresh cases: `configs/wsp-v4-cases.json` (SHA-256 `f8f5d54c45a10b997b31f6fea029f48e8acb7988520eb110343bd3b7779c8f47`), 36 cases disjoint from v1-v3 coefficient pairs (24 target, 6 failing-assertion, 6 passing-control).

**Design.** Two independent batches (`configs/wsp-v4-a.json` seed 201, `configs/wsp-v4-b.json` seed 202), each 4 arms x 36 cases = 144 trajectories, temperature 0.2, thinking on, case timeout 300 s, **per-trajectory seeds** (SHA-256 of batch seed, case id, arm), arm order rotated by case index. Adapter package `artifacts/wsp-v2-prepare/20261108T001803Z-alpha4p0/prepare.json` (the same alpha 4 aliases as v3).

**Gates (per batch, identical to v3 form).** Application check passes; edit completes all passing-control cases; edit beats base by net >= 6 target workflows with one-sided exact sign test p < 0.05; edit beats the sign-flipped edit by net >= 4; edit loses at most one non-target case against base. Rows not reached, timed out or invalid count as failures of the arm (no dropping). **Robust in the competition setting** only if both batches pass; one pass is reported as mixed. Descriptive, not gated: empty-completion counts per arm, rereads on first action, completion tokens.

**Budget.** Two parallel A10G batches, 2 cores/16 GiB, 4,500 s execution, 900 s startup, network blocked, bound USD 1.9847 each (USD 3.97 for both), reserve USD 4.4. Cap for the round USD 6; no third batch without a new decision. If one batch has not finished by 10 November 12:00 UTC, results to date are reported as incomplete.

**Pre-stated limits.** Still one synthetic template family; coefficient-only variation; no real-issue repairs; thinking budget not separately enforced. A pass would not show the edit helps real repairs; a fail is reported as a limit.
