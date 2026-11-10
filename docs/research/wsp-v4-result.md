# Weight-space study v4 — result (competition setting)

Protocol: [weight-space-study-v4.md](weight-space-study-v4.md) (SHA-256 `3d8970deffd8407a10107ac992e99ee5c5e9f3a0a25d3e4b8bbbf432a886d956`). Temperature 0.2, top_p 0.95, thinking enabled (verified: every response has reasoning), per-trajectory seeds, 36 fresh cases, edit at alpha 4 as chosen in v3. Reports: batch A (seed 201) `artifacts/wsp-v4/20261108T080127Z-wsp-v4-a/run.json` SHA-256 `c09ee3ae36e05458a93140834dfee0f8a6bc5d62474b85153ca85764cde4b71a`; batch B (seed 202) `artifacts/wsp-v4/20261108T080132Z-wsp-v4-b/run.json` SHA-256 `a1f55807a5580b09e16d1a5d830c10da4acc22ab9c9b3e9c0a94e81bf2bfe203`. Both complete, 144 valid trajectories each (2,424 and 2,558 seconds), apps stopped.

**Verdict by the frozen rule: mixed (A passes, B fails).** Not "robust in the competition setting".

| Target workflows complete, of 24 | base | edit | sign-flipped | prompt |
| --- | ---: | ---: | ---: | ---: |
| A (seed 201) | 3 | 15 | 2 | 10 |
| B (seed 202) | 6 | 10 | 4 | 11 |

- A: edit vs base net +12 (p = 0.0002), vs sign-flipped +13; one non-target loss; all gates pass.
- B: edit vs base net +4 (p = 0.17), vs sign-flipped +6 (p = 0.07); fails the net >= 6 gate.
- Non-target (of 12): edit 11 and 11, base 12 and 11 (one edit loss in A, none net in B).
- First action `read_file` on target cases: base 6 and 5, edit 12 and 10, prompt 18 and 21, sign-flipped 2 and 3. The edit shifts the first action in the intended direction but about half as strongly as the prompt.
- No empty completions or length stops for the edit; the v3 failure mode did not recur at temperature 0.2 with thinking.
- 8-15 of 24 trajectories per arm (the prompt arm included) ended on the 6-request generation budget, which caps completions in this setting; the prompt completing only 10-11 of 24 shows the budget, not only the behaviour, limits the metric.
- Pooled (descriptive only, not pre-registered): edit 25/48, base 9/48, sign-flipped 6/48, prompt 21/48.

Limits: still one synthetic family with coefficient-only variation; thinking budget not separately enforced; the 6-request cap truncates thinking-mode trajectories; no real-repair evidence. Spend: two batches of at most USD 1.98 each, estimated about USD 3.5 actual; study total about USD 11.3 of the USD 14 combined cap.

Correction, 10 November: the spend figures above are allocation-based upper estimates. The Modal billing report shows USD 4.85 of metered compute for all `gemma4-*` apps in November (v2-v4 runs combined); see the ledger entry of 10 November.
