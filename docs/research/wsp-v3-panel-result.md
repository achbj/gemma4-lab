# Weight-space study v3 — fresh-panel result

8 November 2026 (UTC). **All four pre-registered gates passed.** With strength α = 4 chosen from
design cases only, the keyed rank-one edit (arm `a`) completed 21 of 24 fresh target workflows,
against 5 for the unchanged base, 5 for the zero adapter, 4 for the norm-matched random adapter
and 0 for the sign-flipped edit. The edit-integrity prompt completed 24 of 24. Protocol:
[weight-space-study-v3.md](weight-space-study-v3.md). Context: [v2 failure](wsp-v2-panel-result.md).

## Result (36 fresh cases, one deterministic draw per arm)

| Arm | Target complete (of 24) | First action = reread | Non-target complete (of 12) |
| --- | ---: | ---: | ---: |
| base | 5 | 0 | 12 |
| zero adapter | 5 | 0 | 12 |
| random (norm-matched) | 4 | 0 | 12 |
| **A (α = 4)** | **21** | **20** | **12** |
| A− (sign-flipped) | 0 | 0 | 12 |
| prompt (edit-integrity) | 24 | 24 | 12 |

Paired target wins/losses for A: vs base 17/1 (net +16, p = 7.2e-5), vs zero 17/1 (+16), vs random
18/1 (+17, p = 3.8e-5), vs sign-flipped 21/0 (+21, p = 4.8e-7), vs prompt 0/3. Gates: valid
coverage 216/216 and all six passing controls preserved by A; each net advantage ≥ 6 with
p < 0.05; advantage over A− ≥ 4; A lost 0 non-target cases to base (limit 1); application check
passed (zero-control drift 0.0 nats; shifts of 0.19–0.26 nats for A, 0.24–0.33 for A−,
0.47–0.76 for the random control). Runner and independent recomputation agree.

## What this shows

- A one-layer, rank-one, closed-form edit built from prompt-versus-base activations on 12 design
  cases reproduces most of an instruction prompt's effect on a specific agent behaviour, through
  quantized E4B + standard rank-8 PEFT + vLLM. The sign-flipped edit removes even the base's
  occasional successes (5 → 0), so the effect is directional, not a nonspecific perturbation. The
  random control perturbs token statistics more (0.47–0.76 nats) than A yet has no behavioural
  effect.
- v1 (static prototypes) and v2 (same construction at α = 1) failed; v3 changed only the strength,
  chosen by a frozen design-set rule after a post-hoc diagnostic on v2's prompts. That
  motivation is a researcher degree of freedom and is reported as such.

## Limits (must be stated in any write-up)

- One synthetic behaviour (reread after a failed partial-line replacement) in one template
  family; fresh cases differ from design cases only in coefficients. No claim about real SWE
  repairs, other behaviours, other models or unseen templates.
- One deterministic temperature-0 draw per arm; no variance across seeds. Non-target cases are
  at ceiling (every arm, including A−, completes 12/12), so that check has little power to detect
  side effects. The three A failures alternated edits and rereads until the generation budget.
- The prompt arm is still stronger (24/24) and needs no adapter; the edit's value is removing an
  instruction, not exceeding it. The design uses activations and weights, so this does not test
  blind weight reading or the published method's other claims. The algebra is ROME's.

## Provenance and integrity

Report `artifacts/wsp-v3-panel/20261107T234620Z/run.json` (SHA-256 `0bbd72db66360cc919f018638f58a907a7b164edf4d438013e6b4c09ae345d55`), recomputed gate `assessment.json` (SHA-256 `dab90b04f320ec64b8a5350974a21912ed9cf981c4e0359a8f875e71cab1aad1`).
Source commit `ab464aa` at launch plus this record; image
`im-Ty8w286dtxiF08cNqhVgz6`; all apps stopped, panel elapsed 795 seconds. The terminal event
returned inline this time. Adapters: `artifacts/wsp-v2-prepare/20261107T234544Z-alpha4p0/`.
