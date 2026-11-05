# Baseline specification and findings

## Sources acquired on 4 November 2026

- [Official starter notebook](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent): downloaded source and input metadata under `data/raw/official/starter/`.
- `HARNESS_README.md`, public tasks, and sample submission from the [competition data](https://www.kaggle.com/competitions/gemma-4-developer-agent/data).
- Three small wheels from the [official wheelhouse](https://www.kaggle.com/datasets/metric/gemma-4-developer-agent-wheelhouse): `adk-eval-core==0.1.0`, `adk-submission==0.2.13`, and `swegemma==0.2.11`. Their contents were inspected as ZIP data, not imported.

The complete file inventory contains 524 competition assets and 41 wheelhouse assets. The task file contains 129 development issues across FastAPI, HTTPX, Requests, and Rich. Ground-truth patches are present in that file; future agent input must expose only the issue, hints, and repository state.

## Candidate configuration

The official starter's model-selection procedure is followed for `submissions/baseline/`: select `gemma-4-e4b-it-qat-w4a16-ct` for the root and analyzer agents and remove the sample 31B-shaped adapters. The source copy remains in the ignored raw-data directory. Prompts, sampling, and evaluation settings remain the supplied reference settings.

The sample evaluation budget is one minute and ten tool calls per issue. This is a compatibility reference, not a tuned competition configuration. Any later budget or prompt change must be a named experiment with a comparison against this reference.

The approved model source is `google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2`, exactly as listed in the starter's input metadata. Its single weight file is 11,513,861,828 bytes. The unmodified checkpoint is staged in the private Modal cache with source hashes. No tensor-level inspection or editing has occurred.

## Remote compatibility work remaining

Compiler milestone passed on 4 November 2026: Python 3.12.10, official compiler/ADK wheels, and an E4B agent tree compiled with inert registries. [Modal run](https://modal.com/apps/ach-bj100/main/ap-wqvNIM6OhQjk964urGqQ9w), runner commit `3d6b62c`, image `im-xXa2wrFOMCoMLyPzVJ2tWO`. The raw report and resolved package inventory are saved at `artifacts/runtime-validation/20261104T123141Z-compiler.json`. Real tool implementations, competition limits, inference, and scoring were not exercised.

All 41 official runtime wheels are now cached (880,842,601 bytes) with hashes in `requirements/remote-runtime-wheels.json`. The official vLLM wheel metadata pins `torch==2.10.0`, `torchaudio==2.10.0`, `torchvision==0.25.0`, `compressed-tensors==0.15.0.1`, and FlashInfer 0.6.6. Preserve these constraints when constructing the separate serving image.

The private CPU [reference inventory run](https://www.kaggle.com/code/bjacharya/gemma4-runtime-inventory-20261104) completed successfully against the exact starter-image digest. Its returned image metadata matched the requested digest. The resulting 970-package inventory is recorded in `requirements/kaggle-reference-versions.json`: Python 3.12.13, Torch 2.10.0+cu128, Starlette 0.52.1, FastAPI 0.136.1, NumPy 2.0.2, and LiteLLM 1.82.4.

The one-L4 serving milestone passed in [Modal run `ap-X5bA7whrQaI6m0tYq4rZJ1`](https://modal.com/apps/ach-bj100/main/ap-X5bA7whrQaI6m0tYq4rZJ1): Python 3.12.10, server readiness in 221.77 seconds, total function time 225.46 seconds. E4B loaded with the starter's parsers and 32,768-token context setting, produced a native `get_status` call, and answered a synthetic tool result. Outbound networking was blocked. This short input establishes protocol compatibility and initial fit, not long-context capacity, successful repairs, or official scorer parity.

Several supplied wheel metadata requirements are not satisfied even by that reference image after its `--no-deps` overlay. In particular, ADK's Starlette range and the supplied metrics wheel's range cannot both satisfy a fresh resolver. The Modal assembly therefore installs supporting dependencies separately, retains the observed Starlette/FastAPI/NumPy/LiteLLM versions, and overlays all supplied wheels without dependency resolution, as the starter does. The supporting recipe is `requirements/remote-runtime-base.txt`; exact resulting packages must be recorded with each run. This is a documented development reconstruction, not a claim of complete scorer parity. The CUDA wheel source follows the [official PyTorch 2.10.0 installation instructions](https://pytorch.org/get-started/previous-versions/).

1. Validate real issue scoring with the official harness and competition limits. The first CPU controls found missing pytest in the reconstructed base; neither the unchanged nor reference-patch control reached tests. This is an infrastructure failure, not an agent result. Restore the observed pytest 8.4.2 and supporting test packages from the reference inventory in `requirements/remote-evaluation-base.txt`; preserve all supplied model/harness wheels.
2. Attempt public development issue `requests_7427` only after the unchanged/reference controls distinguish failure from success. The original `7505` fixture remains unsuitable because its full test file needs missing HTTP fixtures/network behavior. Record the raw trace, patch, verification result, exact packages, submission hashes, runtime, and cost. Reference answers must never be mounted into the agent invocation.
3. Verify adapter application separately before adapting weights. Weight interpretation and editing require the user's Ultra checkpoint.
4. Recheck final candidates using the official Kaggle runtime and scorer hardware before making submission-compatibility claims.

The initial Modal plan uses one L4, whereas the scorer uses four L4s. The first real issue attempt used a documented A10G capacity fallback after an unscheduled L4 request was cancelled. These development configurations must be labelled separately. No successful repair or model improvement has been measured yet.

## Documented development adaptation: checkout import paths

The unchanged `requests_7427` control unexpectedly passed alongside the reference patch. Inspection of the supplied `swegemma==0.2.11` wheel showed that both editable-package installation and dependency setup return immediately for `SubprocessManager`. Its environment supplies the workspace root on `PYTHONPATH`, but does not add `workspace/src`; an installed Requests package can consequently shadow the checkout. Such results are invalid evidence of agent repair.

The development wrapper now preserves the manager's original lifecycle and writes a `workspace_paths.pth` into each sandbox's own venv after creation. It places that sandbox's workspace and `src` first on the Python import path. This restores the intended checkout imports; it changes no reference/test patch, repository source, model, sampling, budget, or official wheel. The adaptation is reported in every evaluation result and checked against a synthetic host-package shadowing regression. Repeat both grader controls before any GPU agent attempt. This deliberate runtime adaptation is not a claim of exact Kaggle/scorer parity; final candidates need independent official-environment verification.

## First real agent attempt: failed pilot

The corrected `requests_7427` CPU controls distinguish the unchanged checkout (one failure, 215 passed, 13 skipped) from its reference fix (216 passed, 13 skipped). The issue is an inspected development pilot and is excluded from the reserved validation partition.

The unmodified baseline then ran on one NVIDIA A10G in [Modal app `ap-bobUmGLMOuYYJXoqgv7hPH`](https://modal.com/apps/ach-bj100/main/ap-bobUmGLMOuYYJXoqgv7hPH). E4B readiness took 245.27 seconds; total function time was 316.77 seconds. The agent timed out after about 63.32 seconds with 12 LLM calls, ten counted tool calls, no source modification, and no patch submission. The evaluator returned before tests (`test_exit_code=-1`); do not report this as a verified test failure or an official leaderboard score. Raw trace and result: `artifacts/baseline/20261104T141310Z-requests_7427-agent.json`.

Five effective reads of the beginning of `utils.py` failed to expose the later target implementation. The agent repeated default truncated reads and once requested 500 lines despite the 150-line cap. Its analyzer also inferred that the target was absent after partial navigation. This is a behavioral observation from one issue, not a weight-level diagnosis or a general failure-rate estimate. The trace records 80,651 prompt and 4,049 completion tokens; the official task summary's zero-token total is inconsistent with its trace.

The next candidate, `pagination-v1`, adds only a generic line-number/range-reading instruction to both prompts. Model/tool declarations, sampling, and evaluation budgets remain byte-identical to baseline. Compare it on the same A10G and pilot before any weight intervention. Preserve a negative result; a single success would need broader development and untouched validation evidence. No novelty claim follows from this prompt change.

## Matched pilot prompt control: no repair gain

`pagination-v1` compiled on CPU with the official compiler, then ran on the same A10G/image/checkpoint and reference budgets in [Modal app `ap-kUQRXIkAt18z5EqxbrcE5N`](https://modal.com/apps/ach-bj100/main/ap-kUQRXIkAt18z5EqxbrcE5N). Report: `artifacts/baseline/20261104T192220Z-requests_7427-agent.json`; runner commit `02dc98e`. Model readiness took 252.27 seconds and total function time was 327.88 seconds.

| Pilot observation | Baseline | Pagination prompt |
| --- | --- | --- |
| LLM calls | 12 | 8 |
| Counted tool calls | 10 | 8 |
| Source patch | None | One source file edited |
| Explicit patch submission | No | No |
| Agent timeout | Yes | Yes |
| Verification | Not reached | 213 passed, 3 failed, 13 skipped |
| Successful repairs | 0 | 0 |
| Trace-reported prompt/completion tokens | 80,651 / 4,049 | 59,858 / 4,357 |

The candidate used a line-number search and a bounded read to reach the target implementation. It created a patch but dropped existing host-with-port handling; the verifier found regressions. The agent timed out with a test command in flight, so it did not receive that result or submit explicitly. The harness recovered its working-tree diff and ran verification separately. The report's top-level `passed=true` means the pipeline reached a test outcome; the authoritative repair result is `evaluation.results.agent.resolved=false`.

This is one unseeded draw per condition on a selected development pilot. Reduced navigation/call counts are proxy observations, not proof of better repair success or a causal weight mechanism. Keep both outcomes; do not promote a winner from this comparison. Token totals are trace-reported and may omit a cancelled in-flight response; they are not paid API charges.

Next: choose a small fixed panel from the frozen development pool, check its grader controls, and compare the baseline and pagination candidate under matched budgets. If the reference one-minute budget is changed, create a separate experiment and rerun both conditions at the same new budget after checking host limits and cost. Preserve the 68 reserved validation issues. Confirm adapter deployment before any adaptation; ask for Ultra before weight interpretation or editing. No weight experiment or novel research finding is established by these pilots.

## Adapter serving interface audit, 4 November

At this source-audit stage, runtime adapter compatibility was unverified. The later [controlled Modal and Kaggle probes](adapter-compatibility.md) established the tested inference path, including the official image and L4x4 hardware. Full SWE judging and repair gains remain separate checks. The following original observations came from reading pinned source files, without importing ML runtimes, interpreting learned tensors, constructing an adapter, or changing any serving setting:

- Baseline calls to `src/gemma4_lab/remote_serving.py` keep `enable_lora=False`. The original inference and repair attempts therefore establish no adapter-loading or adapter-effect evidence. The later probe uses an explicit opt-in adapter manifest.
- The pinned vLLM 0.19.1 `vllm/model_executor/models/gemma4_mm.py` declares `Gemma4ForConditionalGeneration` with `SupportsLoRA` at lines 883–899. That interface declaration does not establish that a particular adapter works with the approved E4B compressed-tensors checkpoint.
- Official starter notebook cell 8 discovers adapters, enables LoRA when adapters exist, sizes adapter count/rank from discovery, and passes the manifest to `VllmServer`. The pinned `adk_submission/server.py` builds the corresponding adapter CLI arguments at lines 759–798 and registers adapter names at lines 397–421. Its rank value of 128 is a fallback; detected ranks are right-sized/rounded in code, so this value alone is not evidence of a universal rank permission or limit.
- A later compatibility experiment must preserve the approved base/wheels, follow that discovery/registry path, validate the submission, and demonstrate that requests reach and use the intended adapter. A listed model name or successful YAML compilation alone is insufficient. The final candidate still needs the official Kaggle scorer environment.

Pinned wheel identifiers, source-member hashes, line references, and starter-notebook hash are saved in ignored `artifacts/runtime-validation/adapter-interface-audit.json`. This is an engineering audit, not a weight diagnosis, edit design, runtime success, or novelty claim. The user's Ultra checkpoint remains in force before weight work.
