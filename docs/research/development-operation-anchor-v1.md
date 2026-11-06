# Operation anchoring on fresh Rich development cases

The candidate keeps the operation and requested behavior from the issue in view
from lookup through the first edit. The direct lookup control provides the same
source search and file tools. Only the root localization instructions differ.
Both arms use the pinned E4B runtime and the same three-minute, ten-call, 8,192
output token settings. The control runs first on the qualified panel.

The panel was committed from issue IDs and base commits before reading the selected
issues. It excludes all previously inspected fixture and panel groups. The target
bodies below come from the four selected public descriptions and original source.
The host grader qualifies the snapshots separately.

| Case | Public behavior | Frozen source body |
| --- | --- | --- |
| `rich_3905` | A disabled `Progress` should finish without an extra blank line | `rich/progress.py` 1175–1177, the stop and print branch in `Progress.stop` |
| `rich_3777` | `TTY_INTERACTIVE=0` disables animation while preserving terminal style handling | `rich/console.py` 734–738, the interactive default and explicit override in `Console.__init__` |
| `rich_4006` | `split_graphemes` terminates on the reported loop case | `rich/cells.py` 181–209, the special codepoint and zero-width branches that govern index progress |
| `rich_3130` | Markdown table cells preserve text segments with inline styles and links | `rich/markdown.py` 336–341, the assignment in `TableDataElement.on_text` |

Score observations before the first source mutation attempt or terminal stop. A score
of 2 requires the full target body in a successful tool observation available to the
editing agent. A score of 1 means a relevant file or partial implementation. Score 0
means the trace shows no relevant location. The returned code determines the score.
Early coverage requires score 2 by the third navigation attempt, counting failed
lookups and delegated navigation. Record whether the first edit addresses the
requested operation or a helper with a source connection demonstrated in the trace.
Keep verifier outcomes and agent stops separate from these scores.

Advance only with complete paired coverage, at least one verified repair win on an
early-target gain, zero paired repair losses, and zero new context or infrastructure
terminations. The frozen panel retains every qualification exclusion. Results use
one sampled trajectory per arm per qualified issue. [Run ledger](../operations/run-log.md)

## Paired result

Both arms resolved **0/3** qualified cases. Exact source coverage rose from **1/3**
to **2/3**, with **0/3 early targets** in each arm. The candidate missed the
advancement gate. `rich_3130` was excluded from both arms because its CPU reference
failed verification. The remaining unchanged/reference exits were 1/0, 1/0 and 124/0.

| Qualified case | Direct lookup | Operation anchor | Verified repairs |
| --- | --- | --- | --- |
| `rich_3905` | Exact body on attempt 10 | Exact body returned by analyzer after attempt 10 | 0 → 0 |
| `rich_3777` | Partial source, edit in console options | Partial source, edit in progress consumer | 0 → 0 |
| `rich_4006` | Partial source, stopped at tool cap | Exact body on attempt 4, partial loop fix | 0 → 0 |

The progress case exhausted both tool budgets before a successful edit. In the
candidate trace the analyzer returned the exact `Progress.stop` body at step 15,
after the ten navigation attempts. Both submitted empty patches. The interactivity
traces show relevant files, but neither exposes the frozen assignment before editing.

The candidate found the grapheme loop and patched the ordinary zero-width branch.
All 56 visible `test_cells.py` tests passed. The independent verifier timed out with
exit 124. A bounded local replay of the exact stock and submitted Git blobs shows why.
The patch makes a leading combining mark (`U+0301`) terminate and leaves a leading
variation selector (`U+FE0F`) in the stall path. Printable input returns the same span
in both versions. The two-second subprocess limits and complete replay are recorded
in `artifacts/runtime-validation/operation-anchor-v1-public-loop-replay.json`.

The control used 30 charged tools and 39 model calls, with 328,899 input and 12,191
output tokens. The candidate used 27 charged tools and 38 model calls, with 316,346
input and 12,510 output tokens. Both arms used the same checkpoint, serving command,
image, settings and ordered cases. The reported GPU labels were NVIDIA A10 and A10G
respectively. The device labels, fixed arm order and single sample limit inference
about timing and causal effects.

The control and candidate reports are under
`artifacts/panels/development-operation-anchor-v1/` with names
`20261106T072156Z-direct-localization-v1-8k.json` and
`20261106T073015Z-operation-anchor-v1-8k.json`. The paired identity and trace audit is
`artifacts/runtime-validation/operation-anchor-v1-audit.json`. [Run ledger](../operations/run-log.md)

## Analyzer availability ablation

Removing the analyzer registration gave **1/3 verified repairs** against **0/3** in
the saved operation-anchor run. Exact source coverage fell from 2/3 to 1/3. Early
coverage stayed at 0/3, so the repair came too late to pass the frozen advancement
gate. Only `agent.yaml` differed. The historical control and candidate used the
same three qualified issues, image, checkpoint, settings and reported A10G device
label. The single sample per arm limits attribution.

| Case | Saved control | Root agent |
| --- | --- | --- |
| `rich_3905` | Exact body on attempt 10, empty patch | Exact body on attempt 8, verified fix |
| `rich_3777` | Partial source, exit 1 | Partial source, edit in `Live`, exit 1 |
| `rich_4006` | Exact body on attempt 4, exit 124 | Read through line 190, partial source and exit 124 |

The root agent guarded `Progress.stop` with `self.disable` and submitted its patch.
Its pytest request hit the ten-call cap. The independent verifier passed the patch.
A local replay of the exact original and submitted blobs shows the disabled output
changes from a newline to empty output, with identical enabled output. The probe is
`artifacts/runtime-validation/root-only-v1-public-progress-replay.json`.

The candidate trace contains zero analyzer calls. The control delegated once and
the analyzer made eight tool attempts. Charged tools fell from 27 to 22 and model
calls from 38 to 29. Candidate input and output totals were 247,462 and 9,416 tokens.
All three cases reached a recorded outcome and the Markdown qualification exclusion
was preserved. The saved report is
`artifacts/panels/development-operation-anchor-v1/20261106T075107Z-operation-anchor-root-only-v1-8k.json`.
`artifacts/runtime-validation/root-only-v1-audit.json` records paired identities,
trace scores and the replay digest. [Run ledger](../operations/run-log.md)
