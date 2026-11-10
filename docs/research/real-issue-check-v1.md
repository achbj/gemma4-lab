# Real-issue check v1: the edited adapter on competition repair tasks (frozen 10 November 2026)

Frozen before any run. This is the first time the closed-form edit is run inside the official repair harness on real issues. Studies v2-v4 measured it only on synthetic tool sessions.

## Question

Does attaching the α = 4 edit to the competition agent break real repair attempts, and does its target behaviour (reread after a failed edit) appear in real trajectories?

The check **cannot show a repair benefit**: three issues and one sampled trajectory per arm. No significance test is applied and no improvement will be claimed from it.

## Rule and source

The [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent) permits PEFT LoRA directories referenced by agents; the [staff update](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287) permits E4B. Adapter serving through the official compiler, resolver and registry was verified in [adapter-compatibility.md](adapter-compatibility.md). This is a development measurement on Modal, not a leaderboard submission.

## Arms

| Arm | Candidate | Difference |
| --- | --- | --- |
| base | `submissions/wsp-base-v1` | none (control) |
| edit | `submissions/wsp-edit-v1` | one line, `adapter: wsp2_a`, on the root agent, plus the adapter directory |

- Adapter: `wsp2_a` from `artifacts/wsp-v2-prepare/20261108T001803Z-alpha4p0/` (the package used in v3 and v4). `adapter_model.safetensors` SHA-256 `9b58fa48656644de01ceb4a634ef16ec97a2871629e477749d52395b4b33d650`; `adapter_config.json` SHA-256 `2aa05babf33ec3c9a667d5e085ab74cc9921a6a8de529a83751c86a8131eb703`. Weight files are git-ignored; restore the directory by copying it from that package.
- The sub-agent (`code_analyzer`) keeps the base model in both arms. It has no edit tool, so the edit's target situation cannot arise there.
- Prompts, tools, sampling (temperature 0.2, top-p 0.95, 8,192 output tokens, thinking budget 4,096) and evaluation limits (10 tool calls, 3 minutes, 50 turns) are byte-identical between arms.
- The base arm is served without LoRA enabled, as in every earlier real-issue run. The edit arm enables LoRA for the single adapter. The zero adapter matched the base exactly in the compatibility probe, so the serving flag itself is not expected to change outputs.

## Cases

Panel `configs/development-line-anchored-v1.json`, unchanged: `rich_4077`, `rich_3486`, `rich_3772`, `rich_3521`, frozen from metadata on 6 November. Three qualified then (`rich_3486` excluded). The same exclusion rule applies; no replacement.

- These are development issues. No reserved validation issue is used.
- They are not fresh: `wsp-base-v1` and one prompt candidate ran on them on 6 November (base 1 of 3 resolved). The edit was built from synthetic design cases only and no real-issue outcome informed it.
- The CPU grader controls are rerun, because the harness helper changes to pass the adapter manifest and the runner requires matching identities.

## Order of work

1. CPU compile of `wsp-edit-v1` (and `wsp-base-v1` if no matching report exists).
2. CPU grader controls for the panel.
3. GPU base arm; confirm the app stopped.
4. GPU edit arm; confirm the app stopped.

## Recorded outcomes

For each arm and issue: resolved or not, test exit code, tool calls, model calls, whether a patch was produced, and any error.

From the traces, counted the same way in both arms:

- failed `edit_file` calls (tool result reports an error or no match);
- of those, how many are followed by `read_file` as the next tool call (the edit's target behaviour);
- model responses with no content and no tool call (the failure seen at temperature 0.7 in v3).

Before the edit arm's first case, the server must show that `wsp2_a` changes next-token log-probabilities on three fixed synthetic prefixes by more than 0.001 nats and ten times the base repeat drift. If not, the arm stops and is reported as not applied.

## Reading the result

- **Operational harm** is reported if the edit arm has a server or adapter error, an empty-response abort, or an issue that ends without a valid test exit where the base arm had one.
- Resolved counts are reported as counts. A difference of one issue in either direction is within what one sampled trajectory per issue can produce and is described that way.
- The 6 November base run is cited as an earlier draw of the same control, not pooled.
- Whatever the outcome, the adapter is not promoted to a competition candidate on this evidence.

## Budget

Approved by the user on 10 November: up to USD 2 from the USD 4.9 credit in `onepiecification`.

- Two A10G jobs with `configs/real-issue-check-a10g.toml`: 2 cores, 16 GiB, 1,620-second execution, 900-second startup, one container, network blocked, scale-down 2 seconds. Bound USD 0.9266 each, USD 1.853 together. The 6 November runs of this panel took 714 and 828 seconds.
- CPU compile and controls: worst case about USD 0.12 (four controls at the 900-second limit); expected under USD 0.03.
- Total bound USD 1.98. No repeat, no second seed and no further job without a new approval.
- Cancel a job that is still unscheduled after 15 minutes.
