# Context correction on the fixed Rich development panel

The 8,192-token candidate completed all four attempts and produced **0/4 verified
repairs**. No context error recurred. Successful inputs peaked at 15,751 tokens, so
this run did not test admission above the old 16,384-token input boundary. The
complete no-truncation criterion remains unestablished because finish reasons are
absent from the pinned trace format.

Only `max_output_tokens` changed, from 16,384 to 8,192 in the shared root/analyzer
sampling file. The approved E4B checkpoint, runtime, edit-integrity prompts, tools,
three-minute/ten-tool/fifty-turn allowances and independent 300-second verification
were retained. All four fixed, already-inspected v2 development cases passed matching
unchanged/reference grader controls. All reserved issues remain untouched. This is an
operational recurrence check, not a matched prompt experiment or a replay of the
historical failing request.

| Issue | Result | Charged tools | Maximum input tokens |
| --- | --- | ---: | ---: |
| `rich_3942` | Source patch verified, exit 1; no context error | 3 | 10,429 |
| `rich_3518` | Tool budget exhausted, no patch or verification | 10 | 15,056 |
| `rich_2943` | Source patch verified, exit 1 | 10 | 15,451 |
| `rich_3676` | Tool budget exhausted, no patch or verification | 10 | 15,751 |

Both patches changed only Rich source files. The two unverified cases spent the tool
allowance on navigation, reads, searches and delegation before any edit. Native
`SUCCESS` is attempt status; it does not supersede `resolved` or the verification
exit code. The new run has two verified failures and two unverified stops. All four
remain in the repair denominator.

The 47 recorded inference calls used 377,809 input and 12,738 output tokens;
maximum completed output was 1,521. No token-limit continuation nudge was observed.
ATIF drops per-response finish reasons, so these observations cannot certify no
truncation. The earlier 16,384-output candidate also scored 0/4 and had one context
error. Different sampled trajectories and no requests above the old input boundary
preclude attributing the missing error or any repair gain to the new setting.

The audit verified candidate, compiler, settings, fixture, source, image and coverage
identities and source-only diffs. Report:
`artifacts/panels/development-context-v1/20261105T194405Z-edit-integrity-v1-8k.json`,
SHA-256 `2140bdc68d057cee7bd1d7844a7fa540a39172b3cd0f755e07d9bfc6522640a5`.
Audit: `artifacts/runtime-validation/context-v1-audit.json`. One A10 job reached
readiness in 205.771 seconds and finished in 444.342 seconds; all apps stopped.
See the [ledger](../operations/run-log.md) for rules, controls and spend.

Retain the shared 8,192 setting in the next control. The immediate testable bottleneck
is the ten-tool cap: the official harness README §7.1 explicitly allows changing
`evaluation.max_tool_calls`, and ten is a sample setting. One planned 30-call arm,
with the same three-minute limit and all other settings fixed, tests whether more
tool calls translate into verified repairs. It requires a separate allocation and
matching controls. Neither budget tuning nor this context check is a novelty claim.
