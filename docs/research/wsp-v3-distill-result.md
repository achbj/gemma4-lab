# Weight-space study v3 — amendment 2 result: gradient-trained distillation baseline

8 November 2026 (UTC). Protocol: [amendment 2](weight-space-study-v3-amendment-2.md), frozen before
training. A rank-8 LoRA on the same module (layer 29 `o_proj`) trained by gradient descent on the 24
design cases reached the frozen design-set rule at step 40 (12/12 prefix cases reread, 12/12
non-target first actions unchanged; loss ≈ 1e-4) and was then run once on the 36 fresh v3 cases.

| Arm | Target complete (of 24) | First action = reread | Non-target (of 12) |
| --- | ---: | ---: | ---: |
| base | 4 | 0 | 12 |
| sign-flipped edit | 0 | 0 | 12 |
| **closed-form edit (α = 4)** | **23** | 22 | 12 |
| **gradient distillation LoRA** | **24** | 24 | 12 |
| prompt | 24 | 24 | 12 |

Under the frozen interpretation rule (comparable if within 3 completed target workflows) the
closed-form edit is **comparable** to the gradient-trained LoRA (23 vs 24; paired 0 wins, 1 loss).
Both beat base by large margins; the distilled LoRA matches the prompt exactly.

## What this means

- The conventional baseline is at least as good as the training-free edit on this task, so the
  edit's merit is not accuracy. Its defensible advantages are that it needs no optimizer, no
  data beyond 12 prompted/unprompted replays plus background statistics, and runs in seconds of
  CPU after one forward pass; it also leaves no training-set overfitting question beyond those
  12 cases. These are efficiency and simplicity claims, not performance claims.
- The baseline used fixed, untuned hyperparameters and converged in 40 steps (about 5 minutes),
  so this comparison cannot support a claim that the edit is cheaper in wall-clock terms.
- **Run-to-run variation:** in this run the edit completed 23/24 and base 4/24; in the earlier v3
  panel (same adapters, same cases, same settings, different arm composition and server batching)
  the edit completed 21/24 and base 5/24. Temperature-0 vLLM serving is not bit-reproducible
  across runs, so single-draw counts carry about ±2 workflow noise. Both runs satisfy the gates.

Provenance: report `artifacts/wsp-v3-distill-panel/20261108T001834Z/run.json` (SHA-256 `20103071ca9fca70616de5aef99f36ca0e9ffe77725e6fd2bbcf3df06c19cd3c`), recomputed `assessment.json`; training report
`artifacts/wsp-v3-distill/20261108T001735Z/train.json` (adapter SHA-256 `4bd667ef…edec`);
package `artifacts/wsp-v2-prepare/20261108T001803Z-alpha4p0/`. 180 trajectories, all valid.
