# Paired synthetic behavioral diagnostic

`configs/behavior-diagnostic-v1.json` freezes twelve synthetic continuation cases and
the two preserved system prompts. The protocol and allocation were committed before
inference in [the run ledger](run-log.md). This measures behavior after seeded tool
feedback; it does not measure competition repair accuracy.

Run from the repository with its orchestration environment:

```sh
MODAL_PROFILE=onepiecification .venv/bin/modal run infrastructure/modal/behavior_diagnostic.py
```

For the separately frozen fresh-case edit-recovery screen, select its configuration
before the Modal module is imported (resource decorators are evaluated at import):

```sh
MODAL_PROFILE=onepiecification GEMMA4_DIAGNOSTIC_CONFIG=configs/behavior-diagnostic-v2.json \
  .venv/bin/modal run infrastructure/modal/behavior_diagnostic.py
```

The selector accepts JSON files directly under `configs/`, and requires the diagnostic
name to match the filename. Version 1 remains the default. Version 2 retains its
generation/checker settings and adds a fixed screening gate; changing coefficients
does not create an independent task distribution or establish competition gains.

The command starts one ephemeral A10G container using the existing official-wheel
image and approved E4B cache. It creates no deployment or adapter. Only synthetic
case data and the two prompts are sent to the function. Network access is blocked;
the model server is local to the remote container. There are no automatic retries.
Monitor the invocation to completion; cancel a still-unscheduled app after fifteen
minutes with `MODAL_PROFILE=onepiecification .venv/bin/modal app stop APP_ID`.

All twelve seed states must pass their preconditions using the official resilient
editor before model serving starts. Each condition receives the same seeded history.
Condition order alternates across cases. The native assistant message, including
reasoning and structured calls, is retained, with one JSON tool response per call.
Plaintext or truncated calls are never reconstructed into executable actions.

`run_command` implements only the two documented fixture checks. Generated Python
is parsed and interpreted as bounded integer arithmetic; it is never executed.
Target tests check three inputs. The separate source metric checks seven fixed
inputs, including four not exposed in the test file; this is a finite behavioral
oracle, not a proof for all integers. Unsupported syntax is recorded separately.
Only `task.py` is editable, and no general shell is exposed.

Each trajectory has six tool actions (including submission), six generation requests,
sixty seconds total, and thirty seconds per request. Generation is greedy with a
fixed seed and at most 1,536 output tokens. The overall function retains the existing
1,800-second execution limit and leaves shutdown time before starting another case.
Skipped/error rows remain in the output. Interpret a paired comparison only after
complete coverage and successful protocol/API checks.

Outputs are atomically saved after each event in ignored
`artifacts/<diagnostic name>/<UTC timestamp>/run.json`. Reports include input
hashes, source commit, runtime identity, raw requests/responses, tool actions, final
source, and separate correctness/workflow/budget/error fields. A completed workflow
requires a nonempty explicit submission and a successful target check after the last
edit. Report the nine initially wrong cases separately from the three already-correct
controls; always show all four families. Inspect traces before interpreting counts.

Refresh workspace rates and check for active project apps before execution; record
the result, billing snapshot, and shutdown afterward. The allocated USD 1.20 reserve
is an estimate including overhead, not a provider-enforced spending cap. Any new
weight analysis or intervention requires the separate Ultra checkpoint.
