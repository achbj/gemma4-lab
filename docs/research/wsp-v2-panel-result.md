# Weight-space study v2 — primary panel result

8 November 2026 (UTC). **The pre-registered primary gate failed.** The activation-informed keyed
rank-one edit (arm `a`, α = 1, layer 29 `o_proj`) did not change the target behaviour in
deployment: 0/24 first-action rereads and 3/24 completed target workflows, versus 4/24 for the
unchanged base. This is the frozen outcome of [weight-space-study-v2.md](weight-space-study-v2.md)
(SHA-256 `6d7b8fc8…2e0cd`); no gate, threshold or case was changed after seeing results.

## Result

| Arm | Target workflows complete (of 24) | First action = reread | Non-target complete (of 12) |
| --- | ---: | ---: | ---: |
| base | 4 | 0 | 12 |
| base repeat | 4 | 0 | 12 |
| zero adapter | 4 | 0 | 12 |
| random (norm-matched) | 5 | 0 | 12 |
| **A (α = 1, primary)** | **3** | **0** | **12** |
| A− (sign-flipped) | 4 | 0 | 12 |
| v1 static-prototype edit | 4 | 3 | 12 |
| prompt (edit-integrity) | 23 | 24 | 12 |

Gates: valid coverage 288/288 and all non-target controls preserved (pass); A vs base, repeat,
zero, random: net −1, −1, −1, −2 against a required ≥ +6 (fail); A vs A−: net −1 against
required ≥ +4 (fail); non-target losses to base 0 (pass); application check passed, with
log-probability shifts of 0.09–0.27 nats for A, A− and random against zero, zero control drift
0.0 nats. Base and base repeat agreed on every case. The prompt control reached 23/24, so the
headroom was real and the failure is the edit's, not the panel's.

## What this does and does not show

- The edit is *applied* (token distributions move by 0.09–0.27 nats on three unrelated prefixes)
  but does not reproduce the prompt's effect at the decision point. Application is not behaviour.
- A, A−, random and zero are indistinguishable on the target behaviour. There is no evidence of a
  directional effect in either sign at this strength.
- The pre-registered revision (α = 2) applied only to a failure "by margin" with a detected
  effect on the target. It is **not authorized**: A is below base with zero rereads.
- This tests one construction (single layer, rank one, α = 1, one decision-token key) on one
  synthetic behaviour. It does not test the published method or other constructions.

## Provenance and run integrity

- Report: `artifacts/wsp-v2-panel/20261107T231339Z/run.json`, SHA-256
  `8f3d9fae0514f578daac0a458fb195a7c02c1551abc3e7c28709ee33aab564b9`; recomputed gate in the
  sibling `assessment.json` (SHA-256 `a106e669…f100ab`). Source commit `58b0d47`, image
  `im-Ty8w286dtxiF08cNqhVgz6`, NVIDIA A10, server ready in 242 s, 1,293 chat requests.
- The terminal event (summary, server log) was lost: it exceeded Modal's inline result size and
  the blocked-network container could not upload the overflow. All 288 per-case rows and the
  application assessment had already streamed into the report, and the same tested `assess_v2`
  was applied to those rows after the run. The server log is unavailable; Modal's app log
  holds the console only.
- Differences from `ach-bj100` runs: new workspace and rebuilt image, so cross-run comparisons
  with earlier screens are indicative only; base, zero and repeat agree exactly within this run.

## Post-hoc diagnostic (exploratory, not a gate)

Run after the gate failed, on the 24 evaluation target prompts, in Transformers with a dense
simulation of the same construction (`artifacts/wsp-v2-diagnose/20261107T233604Z.json`, SHA-256 `64c22178bbd3cb4f75e8f50081a678275a7726eb3521ccccbd33b6c7da0c3951`). It cannot rescue the v2
outcome; it motivates, at most, a new pre-registered experiment.

- **The trigger fires and the shift generalizes.** The edit's key dot product on evaluation
  decision points averages 0.99 (design value 1.0, range 0.87–1.02); key cosine with the design
  key 0.9995; the evaluation-set teacher-minus-base shift has cosine 0.9992 with the design `d`.
  The cases differ only in coefficients, so this is expected, not evidence of broad transfer.
- **Direction and sign are right; magnitude is far too small.** Teacher-forced
  `log P(read_file) − log P(edit_file)` for the first tool call, base prompt: −0.67 nats at α=0,
  −0.47 at α=1, −0.29 at α=2, +0.15 at α=4, +0.91 at α=8, and −0.85 at α=−1 (monotone in α).
  The edit-integrity prompt reaches +2.65 nats. The fraction of cases preferring the reread is
  0/24 at α=0 and α=1, 1/24 at α=2, 22/24 at α=4 and 24/24 at α=8.
- **So the α=1 rank-one shift of one layer's mean prompt effect recovers about 6% of the
  prompt's margin;** the prompt's effect is spread over many layers and positions. The frozen α=2
  revision would also have failed (margin still negative), consistent with it not being authorized.
- **Not shown:** whether α ≥ 4 yields complete, correct workflows when sampled, or leaves
  non-target behaviour intact. The α values were read off evaluation-case prompts, so any follow-up
  must choose α from design cases only and test on fresh cases.
