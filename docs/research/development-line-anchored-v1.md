# Fresh Rich development transfer for line-anchored root navigation

This paired fresh-development comparison tests whether the accumulated declarative
workflow and tool-surface package in `line-anchored-root-v1-8k` transfers to
uninspected Rich issues against the context-corrected official starter baseline
(`wsp-base-v1`). Both arms use the pinned E4B v2 runtime image, checkpoint, and
identical three-minute, ten-call, fifty-turn, 8,192-output-token settings
(`eval_config.yaml` and `configs/sampling.yaml` are byte-identical across arms).
Only `agent.yaml` (removing `code_analyzer` registration so the root retains the
full ten-call budget) and `prompts/system.md` (line-anchored `grep -rnF` /
`grep -rnE` first-call lookup, explicit `start_line` windows for the 150-line
`read_file` cap, and `edit-integrity` full-line replacement/reread rules) differ.
The `wsp-base-v1` control runs first on the qualified panel, followed by
`line-anchored-root-v1-8k`.

`configs/development-line-anchored-v1.json` was frozen from issue IDs and base
commits in `configs/evaluation-split.json` before reading any of the four selected
issues. It excludes every repository/base-commit group from all 14 prior fixture
and panel tasks. The target source bodies below are frozen from the four public
problem statements and original stock source snapshots prior to inference; the
dedicated CPU-only grader qualifies snapshots separately.

| Case | Public problem statement | Frozen source body |
| --- | --- | --- |
| `rich_4077` | `proxy isatty` (`FileProxy` delegation of `isatty`) | `rich/file_proxy.py` 25–57, the `FileProxy` delegation methods (`__getattr__` through `fileno`) |
| `rich_3486` | `report fine grained error locations` (PEP 657 in `rich.traceback`) | `rich/traceback.py` 443–466 (frame extraction in `Traceback.extract`) or 693–708 (`Syntax` highlight construction in `_render_stack`) |
| `rich_3772` | `Fix traceback recursion` | `rich/traceback.py` 461–475 (`ExceptionGroup` recursion in `Traceback.extract`) or 564–582 (`__cause__` / `__context__` loop in `Traceback.extract`) |
| `rich_3521` | `Segment.split_cells fix` | `rich/segment.py` 132–182, the cell-position loop in `Segment._split_cells` and wrapper `Segment.split_cells` |

Score source observations available to the editing agent before its first source
mutation attempt or terminal stop:

- **Score 2:** Full frozen target body returned in a successful `read_file`
  observation available to the editing agent.
- **Score 1:** Target file observed or partial target implementation returned.
- **Score 0:** No observation of the target file before editing or stopping.
- **Early target:** Score 2 achieved within the first three navigation tool
  attempts (counting delegated `code_analyzer` tool calls, failed searches, and
  file reads in trace order).

Promote `line-anchored-root-v1-8k` as the frozen development-validated E4B agent
candidate only with complete paired coverage across all qualified cases (at least
two qualified cases required, preserving any qualification exclusions), at least
one paired verified-repair win (`candidate > control`), zero paired verified-repair
losses, at least one paired gain in early target coverage, at least one verified
repair on an early-target case, and zero new context or infrastructure
terminations. Results use one sampled trajectory per arm per qualified issue.
[Run ledger](../operations/run-log.md)

## Paired result

The context-corrected official starter control (`wsp-base-v1`) resolved **1/3**
qualified cases (`rich_4077`), whereas `line-anchored-root-v1-8k` resolved **0/3**
(one paired repair loss, zero paired repair wins). Exact source coverage was **1/3**
in each arm (`rich_4077` in the control versus `rich_3521` in the candidate), and
early target coverage was **1/3** in the control versus **0/3** in the candidate.
`line-anchored-root-v1-8k` therefore fails its fresh-transfer promotion gate and is
not promoted over `wsp-base-v1`. `rich_3486` was excluded across both arms during
CPU qualification because its gold reference patch recorded `resolved=false` under
Python 3.12 (`test_traceback_finely_grained_missing` skipped). Both GPU batches
reported `NVIDIA A10` and completed all three qualified cases with zero context or
infrastructure terminations.

| Qualified case | Starter @ 8k (`wsp-base-v1`) | Line-anchored root (`line-anchored-root-v1-8k`) | Verified repairs |
| --- | --- | --- | --- |
| `rich_4077` (`proxy isatty`) | Exact body on attempt 2 (`rich/file_proxy.py` `1–57`), verified fix in 6 calls | Searched `grep -rnE 'isatty' rich/`, read & edited `rich/console.py` (`score 0`), exit 1 | 1 → 0 |
| `rich_3772` (`Fix traceback recursion`) | Repeated `start_line=1` reads (`1–150` four times, `score 1`), hit 10-call cap, empty patch, exit 124 | Paginated `252–350` & `600–749` (`score 1`, missed `extract`), edited `render_stack`, exit 124 | 0 → 0 |
| `rich_3521` (`Segment.split_cells fix`) | Read `1–150` (`score 1`, clipped `151–182`), blind edit at line 148, exit 1 in 4 calls | Located `split_cells` & `_split_cells`, read `111–260` on attempt 4 (`score 2`), exit 1 | 0 → 0 |

The paired traces expose a sharp structural tradeoff between **existing-symbol
pagination** and **missing-method owner matching**:

- **Why `wsp-base-v1` won `rich_4077` and `line-anchored-root-v1-8k` regressed:**
  The official harness injects the three-level `./` repository tree (`## Workspace Layout`,
  including `./rich/file_proxy.py`) into every task prompt. `wsp-base-v1`'s starter
  prompt (*"Extract filenames, functions, classes... directly from the problem statement"*)
  matched `"proxy"` in `"proxy isatty"` to `./rich/file_proxy.py`, saw that `grep -r "isatty" rich/`
  had no match in `file_proxy.py`, read all 57 lines of `rich/file_proxy.py` on call 2,
  added `FileProxy.isatty`, passed `tests/test_file_proxy.py`, and resolved the issue.
  By contrast, `line-anchored-root-v1-8k` replaced filename extraction with a mandatory
  `grep`-first rule (*"never an unanchored `read_file` from line 1"*); searching `isatty`
  matched only modules that *already* define or call `isatty` (`_null_file.py`,
  `console.py`, `progress.py`), diverting the agent into `Console` (`score 0`). A local
  public replay (`artifacts/runtime-validation/development-line-anchored-v1-public-proxy-replay.json`)
  verifies the exact original (`4b0b0da6...`) and submitted (`3a30ce94...`) git blobs on
  `rich/file_proxy.py`.
- **Where `line-anchored-root-v1-8k` fixed the starter's 150-line trap (`rich_3521`, `rich_3772`):**
  In `rich_3772`, `wsp-base-v1` requested `start_line=1, end_line=884/200/300` on
  `rich/traceback.py` and received lines `1–150` four times before exhausting ten
  calls with an empty patch; in `rich_3521`, `wsp-base-v1`'s `1–150` read clipped
  lines `151–182` of `Segment._split_cells` and `Segment.split_cells`. `line-anchored-root-v1-8k`
  avoided `start_line=1` trapping in both cases and reached the full `132–182` target
  body of `rich/segment.py` on attempt 4 (`score 2`), though its replacement logic in
  `_split_cells` still failed `test_split_cells_emoji`.

Neither arm invoked `code_analyzer` (`0` delegations in both traces, even though
`wsp-base-v1` registered it). `wsp-base-v1` used 20 charged tool calls (`6 + 10 + 4`),
29 LLM calls, 253,152 prompt tokens and 13,584 completion tokens;
`line-anchored-root-v1-8k` used 25 charged tool calls (`5 + 10 + 10`), 33 LLM calls,
310,955 prompt tokens and 19,860 completion tokens. The saved reports are
`20261106T164434Z-wsp-base-v1.json` and `20261106T165758Z-line-anchored-root-v1-8k.json`
under `artifacts/panels/development-line-anchored-v1/`, and the paired audit is
`artifacts/runtime-validation/development-line-anchored-v1-audit.json`.
[Run ledger](../operations/run-log.md)

