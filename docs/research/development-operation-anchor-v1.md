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

## Line-anchored root navigation correction

`line-anchored-root-v1-8k` isolates a single-factor correction to Section 1 of
`prompts/system.md` against the saved `operation-anchor-root-only-v1-8k` control;
all five companion files are byte-identical. The updated instructions require a
line-numbered `grep -rnF` or `grep -rnE` search on the first navigation call (covering
both named definitions and setting/attribute anchors), explain that `read_file`
enforces a 150-line window starting at `start_line` so raising `end_line` with
`start_line=1` still returns lines 1–150, specify `start_line=L, end_line=L+120`
for definitions and `start_line=L-15, end_line=L+105` for in-body matches, and
require tracing every branch in the target block before editing.

The candidate reached **3/3 exact source targets** (versus **1/3** in the root-only
control), **3/3 early targets** by navigation attempt 3 before the first mutation
attempt (versus **0/3** in the control and all prior arms), and **1/3 verified
repairs** (`rich_3905`, verifier exit 0) with zero paired repair losses and zero
context or infrastructure terminations. Because the verified repair on `rich_3905`
now follows early target exposure on navigation attempt 3 (completing in 6 tool
calls and passing `pytest tests/test_progress.py` before submission), the candidate
passes the prespecified early-localization gate on this inspected panel.

| Case | Saved root-only control | Line-anchored root (`line-anchored-root-v1-8k`) |
| --- | --- | --- |
| `rich_3905` | Exact body on attempt 8 (`10` tool calls), verified fix | Exact body on attempt 3 (`6` tool calls, lines `1061–1180`), verified fix |
| `rich_3777` | Partial source (`Live`), verifier exit 1 | Exact body on attempt 3 (`7` tool calls, lines `700–800`), edited `Console.is_interactive`, verifier exit 1 |
| `rich_4006` | Read lines `150–190`, edited `_cell_len`, verifier exit 124 | Exact body on attempt 3 (`6` tool calls, lines `161–250`), edited `split_graphemes`, verifier exit 124 |

In `rich_3905`, the agent ran `grep -rn "class Progress" rich/progress.py` on call 2,
read lines `1061–1180` on call 3, guarded `Progress.stop` with `not self.disable`,
ran `pytest tests/test_progress.py` (39 passed), and submitted its patch in 6 tool
calls. The local replay `artifacts/runtime-validation/line-anchored-root-v1-public-progress-replay.json`
confirms the exact original (`421e14119d96c277759b956e1f2680ca09290863`) and submitted
(`756b749d265646d2c214fd8b575145f52ed9b404`) git blobs and expected disabled/enabled
outputs. In `rich_3777`, `grep -rnE 'TTY|interactive' rich/` on call 1 located line 734
of `rich/console.py`, and call 3 read lines `700–800`; the edit modified
`Console.is_interactive` directly, but read `os.environ.get("TTY_INTERACTIVE", "1")`
and only handled `"0"`, failing `test_tty_interactive` when `_environ={"TTY_INTERACTIVE": "1"}`
was passed on a non-TTY `BytesIO`. In `rich_4006`, `grep -rnF 'def split_graphemes' rich/`
on call 1 and `read_file` (`161–250`) on call 3 exposed the full `split_graphemes`
loop; the agent patched `split_graphemes` rather than `_cell_len`, adding an `else: index += 1`
fallback to the width check (`tests/test_cells.py` passed), while the early `continue`
inside `if (character := text[index]) in SPECIAL:` for a leading `\ufe0f` remained
unpatched and timed out in verification (exit 124).

Charged tool calls fell from 22 to 19 (`6 + 7 + 6`, with zero tool-cap stops) and
LLM calls from 29 to 25 (`8 + 9 + 8`), with 200,586 input and 8,907 output tokens
(versus 247,462 and 9,416 in the root-only control) and zero delegated analyzer
actions. The saved report is
`artifacts/panels/development-operation-anchor-v1/20261106T122330Z-line-anchored-root-v1-8k.json`
(reported GPU label `NVIDIA A10` versus `NVIDIA A10G` in the control), and the paired
audit is `artifacts/runtime-validation/line-anchored-root-v1-audit.json`. Because this
correction was designed from inspected traces on this three-case panel, fresh
uninspected development transfer is required before any broad generalization claim.
[Run ledger](../operations/run-log.md)
