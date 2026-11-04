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
2. Attempt public development issue `requests_7505` only after the unchanged/reference controls distinguish failure from success. Record the raw trace, patch, verification result, exact packages, submission hashes, runtime, and cost. Reference answers must never be mounted into the agent invocation.
3. Verify adapter application separately before adapting weights. Weight interpretation and editing require the user's Ultra checkpoint.
4. Recheck final candidates using the official Kaggle runtime and scorer hardware before making submission-compatibility claims.

The initial Modal plan uses one L4, whereas the scorer uses four L4s. This development configuration must be labelled separately. No benchmark success or model improvement has been measured yet.
