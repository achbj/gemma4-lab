# Real-issue check v1: result (10 November 2026)

Protocol: [real-issue-check-v1.md](real-issue-check-v1.md), frozen before the runs. Three qualified Rich development issues, official harness, competition settings, one sampled trajectory per issue per arm.

**Outcome: no repair in either arm, and the edit arm triggers the protocol's operational-harm flag.** The adapter is not a competition candidate. With three issues and one draw this is a breakage check, not a measurement of repair rate.

## Results

| Issue | base (10 Nov) | edit (10 Nov) | base, earlier draw (6 Nov) |
| --- | --- | --- | --- |
| `rich_4077` | not resolved; tests ran, exit 1; 51 s | not resolved; **session timeout, no patch, exit -1**; 183 s | resolved; 45 s |
| `rich_3772` | not resolved; verification timeout (124); 419 s | not resolved; verification timeout (124); 411 s | not resolved; 124; 408 s |
| `rich_3521` | not resolved; exit 1; 124 s | not resolved; exit 1; **session timeout**, patch kept; 187 s | not resolved; exit 1; 64 s |
| **Resolved** | **0 of 3** | **0 of 3** | 1 of 3 |

| Trace count (root and sub-agent calls) | base (10 Nov) | edit | base (6 Nov) |
| --- | --- | --- | --- |
| Tool calls | 29 | 37 | 26 |
| `read_file` calls | 10 | 16 | 10 |
| Edits the editor rejected | 1 | 4 | 1 |
| Rejected edit followed by `read_file` | 1 | 3 | 1 |
| Empty model responses | 0 | 0 | 0 |
| Trajectories ending on the 3-minute session limit | 0 | 2 | 0 |

## Checks

- **Applied.** Before the first case the served `wsp2_a` shifted next-token log-probabilities on the three fixed prefixes by 0.254, 0.257 and 0.187 nats, with zero base repeat drift (threshold 0.001). Every root-agent step in the edit traces names model `wsp2_a`; base traces name the base checkpoint.
- **Controls.** CPU grader controls were rerun on 10 November; the same three issues qualified and `rich_3486` stayed excluded.
- **Operational harm rule.** The edit arm had no server or adapter error and no empty response. On `rich_4077` it ended without a valid test exit (session timeout, no patch) where the base arm had one. The frozen rule counts that as operational harm.

## Reading

- The repair counts (0, 0 and an earlier 1) are within what one sampled trajectory per issue produces. The base control itself went from 1 of 3 to 0 of 3 between draws.
- The edit arm read more and used more calls and time. Two of its three trajectories hit the session limit; neither base draw hit it. That is the same direction as the synthetic studies (more rereading) but here it cost budget without producing a repair. One draw cannot separate this from sampling variation.
- The edit's target situation is rare in these traces. Base met one rejected edit per draw and reread after it both times, so on these issues there was little for the edit to fix.
- The base arm ran without LoRA serving enabled and the edit arm with it. The zero adapter matched the base exactly in the compatibility probe, so this is not expected to matter, but it was not re-tested here.
- The issues were not fresh for the base agent (see protocol). The edit was built from synthetic cases only.

## Provenance

- Base: `artifacts/panels/development-line-anchored-v1/20261110T135254Z-wsp-base-v1.json`, SHA-256 `ec690e769fe9009a7159bae60b06d8996ba239d8bee93ccd4f648bc418f15a99`, runner commit `d4668ec`, app `ap-B68WYzA6iWx0BGt1kdyh7t`, 874 s.
- Edit: `artifacts/panels/development-line-anchored-v1/20261110T140821Z-wsp-edit-v1.json`, SHA-256 `e544c9388d02220868a07008ea3a203915aa71152e833c970ed59a7bd881f8a4`, commit `2c9c900` (adds only the offline trace summary), app `ap-kwMLU0y7kp8zfURXccbYLg`, 1,029 s.
- Controls: `artifacts/panels/development-line-anchored-v1/20261110T134631Z-controls.json`.
- Counts come from `gemma4_lab.trace_summary.summarize_trace` over the saved traces.
- Cost: USD 0.70 metered on the day of the run per `modal billing report` (GPU jobs 0.689, CPU controls 0.012, compile 0.001), against a bound of USD 1.98. Both apps stopped; nothing left running.
