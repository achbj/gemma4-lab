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
