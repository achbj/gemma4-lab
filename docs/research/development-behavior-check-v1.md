# Requested-behavior verification on the Rich development panel

The candidate produced **one independently verified repair in four cases**, versus
zero in the preserved ten-call control. It cleared the stale hash after removing
metadata in `rich_2943`. Both arms scored zero on issue-specific checks. The candidate
missed the preregistered promotion gate, which required a verified repair with a
passing issue-specific check on the submitted revision.

The comparison used the same four inspected cases, grader controls, checkpoint,
image, serving command and budgets. Only the root verification and submission
instructions changed. The ten-call control and candidate report NVIDIA A10 and
NVIDIA A10G respectively under the same requested Modal GPU setting. The device
difference, historical control and one sampled draw per arm limit causal and timing
comparisons.

| Issue | Ten-call control | Verification candidate | Issue-specific score |
| --- | --- | --- | ---: |
| `rich_3942` | Verified failure | Submitted an invalid color and failed test collection | 0 |
| `rich_3518` | Unverified tool cap | Exhausted ten calls before editing | 0 |
| `rich_2943` | Verified failure | Cleared the stale cached hash and passed independent verification | 0 |
| `rich_3676` | Unverified tool cap | Hit the three-minute session limit without a patch | 0 |

The successful trace located `Style.clear_meta_and_links`, replaced the copy of
`self._hash` with `None`, passed all 26 stock style tests and submitted the one-line
source change. It used five charged calls. The stock tests cover hash type and metadata
removal separately. Their assertions do not exercise the stale hash after metadata
removal, which leaves this case at score 0 under the frozen rubric.

A separate local replay used the public issue and exact original and submitted Git
blobs. It hashes a style with metadata, clears metadata and checks the result against
a fresh equivalent style. The original source fails the hash assertion and the
submitted source passes it. This replay validates the repair directly. It was
constructed after the run and has no effect on the agent's workflow score.

The 47 recorded calls used 382,452 input and 23,167 output tokens. Maximum observed
input was 16,048, maximum output was 3,661 and total charged tools were 35. There was
one agent wall time termination and one tool cap termination. No context error or
token-limit nudge was observed. Native trace finish reasons remain unavailable.

The [run ledger](../operations/run-log.md) records allocation and shutdown. The full
report is `artifacts/panels/development-context-v1/20261105T234726Z-behavior-check-v1-8k.json`,
SHA-256 `ea7ac9b07172e18fa2ab5f874a66ee59744d5d9c3ef303315420385724b7983f`.
The trace audit and exact public probe are preserved as
`artifacts/runtime-validation/behavior-check-v1-audit.json` and
`artifacts/runtime-validation/behavior-check-v1-public-replay.json`.

Keep this patch and trace as a verified development result. The observed repair
supports evaluating localization and minimal fixes as separate workflow outcomes.
The requested-behavior check mechanism remains unestablished, and the four inspected
cases provide no held-out or novelty evidence.
