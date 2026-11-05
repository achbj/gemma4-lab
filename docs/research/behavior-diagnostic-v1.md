# Seeded edit and test-feedback diagnostic, 5 November 2026

The baseline and feedback-only prompts produced the same correctness and completion
counts in this fixed synthetic screen. Each corrected and submitted seven of nine
initially wrong cases, and completed all three already-correct controls. Both failed
the same two prefix-corruption cases within the six-action limit. This supports
testing a specific edit-recovery prompt before investing in a weight intervention.
It establishes no competition repair gain or new research method.

## Fixed comparison

The twelve cases, generation settings, prompts, cost allocation, and measurements
were committed before inference. Three cases per family use different arithmetic
coefficients. Both conditions receive identical seeded histories; condition order
alternates by case index. No cases, prompts, or settings were changed after outcomes.
See the [protocol and reproduction instructions](../operations/behavior-diagnostic.md)
and [run ledger](../operations/run-log.md).

The four tool interfaces use the pinned native resilient editor and a deterministic
restricted test checker. No generated Python is executed. Source correctness means
passing seven fixed integer inputs, including four absent from the visible tests;
it is not a proof for arbitrary inputs. Workflow completion additionally requires a
nonempty explicit submission and a successful targeted check after the final edit.

## Results

| Seed family | Baseline: correct source / complete workflow | Feedback: correct source / complete workflow |
| --- | --- | --- |
| Prefix-corrupted edit | 1/3 / 1/3 | 1/3 / 1/3 |
| Valid wrong edit, failed assertion | 3/3 / 3/3 | 3/3 / 3/3 |
| Correct edit, passing targeted check | 3/3 / 3/3 | 3/3 / 3/3 |
| Passing smoke check, wrong requested behavior | 3/3 / 3/3 | 3/3 / 3/3 |

There were no paired correctness/workflow wins or losses. Across both conditions,
all twenty submissions satisfied the diagnostic workflow; four trajectories exhausted
their action and generation budgets without submission. There were no skipped cases,
HTTP/API failures, wrapper protocol failures, timeouts, length truncations, or checker
results classified as unsupported. Returned tool calls nevertheless produced
errors: ten failing command checks, ten failed replacements, and eight invalid-argument
responses across the 84 post-seed actions. These are behavioral failures, not successful
tool use or infrastructure exclusions.

In `prefix-01` and `prefix-02`, both prompts initially replaced a substring within the
already-corrupted return line, leaving the invalid suffix. The baseline's parsed native
tool calls then repeatedly contained malformed edit argument keys. The feedback condition
repeated failed replacements and read the actual file only on its sixth action. Both retained syntax
errors. In `prefix-03`, each condition made two unsuccessful replacements, read the
current file, replaced the entire corrupted line, ran the targeted check, and submitted
on action six. Parsed calls alone cannot distinguish generation-format errors from
parser behavior. These are trace observations, without a weight-level causal explanation.

The simple assertion failures and irrelevant passing checks were all handled correctly.
This toy screen therefore does not justify a general claim that E4B cannot use failing
tests. The narrower observed problem is recovery from a file state that differs from
the earlier read, including edit argument errors and delayed rereading.

## Provenance and limits

- One stopped [Modal app](https://modal.com/apps/ach-bj100/main/ap-2dWaemMuRcdgAazyShX7U3),
  runner/source commit `4f167f1`. Report:
  `artifacts/behavior-diagnostic-v1/20261105T081814Z/run.json`, SHA-256
  `0548a58bdc49e8173b31f1436383d3778473d9e613a740c4448d9d65dbfa67ec`.
- All twelve native seed preconditions passed before serving. All 24 trajectories
  completed with the unchanged E4B version-2 base and no adapter. The image remained
  `im-bEtC1IFnE2DCntpbAu56LW`; Python 3.12.10 and the seven critical ML/harness package
  versions matched the earlier Modal probe. Ten input/source hashes were retained.
- Model readiness: 194.59 seconds; complete function: 232.38 seconds. Eighty-four
  generation requests reported 161,114 prompt and 2,734 output tokens. These were
  local GPU inference tokens, with no external paid model API.
- Independent consistency/replay audit:
  `artifacts/runtime-validation/behavior-diagnostic-consistency.json`.

This is one greedy draw per case/condition, with synthetic off-policy histories, tiny
files, restricted commands, and a diagnostic action budget. The cases are now inspected
development data. Raw vLLM continuation is not the entire ADK/SWE judging path. Results
cannot estimate hidden-task accuracy, establish broad generalization, or support a
novelty claim. All 68 reserved competition validation issues remain untouched.

Next compare a narrowly specified reread/full-line replacement instruction with the
baseline on fresh synthetic cases, then require verified repairs on fresh development
issues before promotion. Keep passing controls to detect needless refusal or edits.
Any later weight analysis/design still requires the separate Ultra confirmation and
must outperform these simpler controls under matched budgets.
