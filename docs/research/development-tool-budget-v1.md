# Tool-budget control on the fixed Rich development panel

Raising the shared tool cap from 10 to 30 produced **0/4 verified repairs**, the
same as the preserved [ten-call control](development-context-v1.md). All four new
attempts made source patches and failed verification. No attempt used more than nine
charged calls, so the extra calls were not exercised. The candidate failed its repair
gate; do not advance it or sweep larger caps.

The official harness README §7.1 permits `evaluation.max_tool_calls`. This single
change preserves both prompts, 8,192 output tokens, thinking/sampling, three minutes,
50 turns, 60-second commands, 300-second verification, E4B version 2 and the pinned
runtime. All four already-inspected cases passed freshly matching CPU controls;
the order, source/fixture identities and reference-solution separation were retained.

| Issue | 10-call control | 30-call candidate | New charged calls |
| --- | --- | --- | ---: |
| `rich_3942` | Verified failure | Verified failure | 5 |
| `rich_3518` | Unverified budget stop | Verified failure | 7 |
| `rich_2943` | Verified failure | Verified failure | 9 |
| `rich_3676` | Unverified budget stop | Verified failure | 7 |

Each new patch touched one source file, with no test changes. Both previously stopped
issues reached verification using fewer calls than the original cap allowed. Those
different trajectories do not demonstrate a benefit from the extra allowance. This
is one sampled draw per condition on a tiny inspected panel: no repair wins/losses,
no strong causal conclusion about the cap, and no claim that tool budgets never matter.

There were no observed context or infrastructure terminations. The 38 recorded calls
used 326,799 input and 16,231 output tokens (343,030 total), with maxima of 14,770 and
2,831 respectively. No successful request crossed the old 16,384-input boundary and
no token-limit nudge was observed. Native trace finish reasons remain unavailable.
Charged tool counts are 33 versus 28 across the four cases; traced attempts can include
unbudgeted or rejected calls and are kept separately.

The audit matched exact case coverage, checkpoint manifest, serving command, image,
compiler/candidate hashes, budgets and verifier controls. GPU report:
`artifacts/panels/development-tool-budget-v1/20261105T232825Z-edit-integrity-v1-8k-t30.json`,
SHA-256 `680e7c31698db72e1631fc9ba4ad9986762cbc929a396c0ea84e3b993b811b7b`.
Audit: `artifacts/runtime-validation/tool-budget-v1-audit.json`. One A10 job was ready
in 199.617 seconds and finished in 486.506 seconds. All apps stopped. The
[ledger](../operations/run-log.md) records the bounded allocation and credit snapshot.

Keep the cheaper ten-call/8,192 configuration as the control. Next test a single
allowed workflow change targeting correctness on the requested behavior before
submission. More editing or passing unrelated visible tests is not a promotion metric.
No reserved case, adapter, or original-paper claim follows from this budget control.
