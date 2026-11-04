# Run and budget ledger

## 4 November 2026 — access/setup

- Authorized Modal workspace: `ach-bj100`; identity verified through `modal token info`.
- User-reported available Modal credit: USD 30; remaining balance not yet independently verified.
- Read-only Modal billing summary succeeded: current-month billed cost USD 0; reported storage charges were offset by the free-storage allowance. This response does not expose remaining credit.
- Additional compute/API spending ceiling: EUR 100.
- Local Python 3.11 orchestration environment created in `.venv`; direct client versions pinned in `pyproject.toml`.
- Dependency check and Kaggle login-command help passed. The Kaggle CLI required an explicit `six` dependency. Kaggle browser sign-in completed as `bjacharya`; the user confirmed competition entry, and the competition API file listing succeeded.
- No GPU jobs, model inference, training, external LLM API calls, or weight edits launched. Project remote-compute usage: USD 0.
- Official harness README, starter notebook, and input metadata downloaded under `data/raw/official/`. These reference files have not been executed.

## 4 November 2026 — organized baseline preparation

- Moved research and operational docs under `docs/`; local tooling is an installable package under `src/gemma4_lab/` with settings in `configs/baseline.toml` and a dependency lock under `requirements/`.
- Retrieved the complete 524-file competition inventory and 41-file wheelhouse inventory. Downloaded 11 bounded bootstrap assets totalling 2,322,219 bytes (about 2.21 MiB); SHA-256 hashes and source identifiers are recorded in `docs/research/official-assets.json`.
- Confirmed the official task file contains 129 development issues across four repositories. Reference patches were not used to design an agent or update weights.
- Prepared `submissions/baseline/` from the official sample. Both agent model declarations select E4B; incompatible dummy adapter references were removed. Prompts, sampling, and evaluation budgets are preserved.
- Local verification passed: 12 offline regression tests, Ruff lint/format checks, asset checksum verification, dependency consistency, and local documentation links.
- The one-L4 compute plan estimates USD 0.766611 for the configured startup/execution/idle allocation, below the initial USD 2 allocation. Builds, staging, storage, and egress are excluded and must be recorded separately. This is not a provider-enforced cap.
- No Modal application, GPU job, inference, training, or weight editing has been launched. Project remote-compute usage remains USD 0.
- Next execution milestone: reproduce the Python 3.12 Linux harness runtime, validate the YAML with its compiler, and prove an E4B tool-call round trip before attempting one issue. See `docs/research/baseline.md` for compatibility checks and exact sources.

## First remote experiment — planned, not launched

- Objective: prove the approved E4B checkpoint loads, generates valid tool calls, and can attempt one public development issue in a compatible harness.
- Allocation: at most USD 2 estimated Modal usage, using existing credit first.
- Choose GPU, timeout, and exact command after reading the current official harness and model requirements. Record startup/download costs as well as inference costs.
- Success evidence: exact checkpoint and package versions, task ID, raw trace, candidate patch, test outcome, elapsed time, and estimated/observed cost.
- Weight interpretation/editing requires the user's Ultra checkpoint first.

## 4 November 2026 — compiler validation allocation

- Rules review and dated novelty register are committed under `docs/research/`. No original research claim is established.
- The starter's exact `gcr.io/kaggle-private-byod/python` image digest returned an authentication challenge; the registry's anonymous token endpoint returned HTTP 403. Do not spend a Modal build trying to pull it anonymously.
- Planned next run: CPU-only Python 3.12 validation using the official `adk-submission==0.2.13`, `google-adk==1.36.1`, and `google-genai==2.11.0` wheels, pinned by SHA-256. Their dependencies are resolved in a separate development image and recorded after the run.
- Scope: directory/schema checks and agent-tree compilation with inert model/tool registries. This does not validate real tool implementations, inference, adapters, or full scorer parity.
- Bounds: one container, one requested physical CPU core, 2 GiB requested RAM, 120-second function timeout, 600-second startup timeout, two-second scale-down window, and zero function retries. Requested startup/function/idle compute estimates about USD 0.0127; reserve USD 0.10 including this small build. Actual billing and build overhead may differ; this reserve is part of the initial USD 2 allocation.
- No model weights, reference task patches, credentials, or external model APIs are needed for this check. Only the submission text and public official wheels are sent to the user's Modal workspace.

## 4 November 2026 — compiler result and checkpoint staging

- Compiler run `ap-OWHPrMRDaiAwzxiXB7CvM9` built the image but failed on an import-time local-path assumption. The app was stopped before retrying. Fix `3d6b62c` includes an offline container-import regression test.
- Run `ap-wqvNIM6OhQjk964urGqQ9w` passed compilation on Python 3.12.10 using image `im-xXa2wrFOMCoMLyPzVJ2tWO`. No model/tool calls occurred. Report: `artifacts/runtime-validation/20261104T123141Z-compiler.json`.
- All 41 official Linux runtime wheels are cached locally (880,842,601 bytes) and hash-pinned. None was installed or imported on this Mac.
- Next allocation: CPU-only staging of approved E4B version 2 into private Modal volume `gemma4-competition-model-cache`, using a temporary download URL limited to that artifact. No user credentials are uploaded. Archive members and sizes must match the official inventory; source hashes are retained alongside the cache.
- Staging bounds: one container, two requested physical CPU cores, 2 GiB RAM, 900-second execution timeout, 60-second startup timeout, two-second scale-down window, and zero function retries. Requested compute estimate is below USD 0.03; reserve USD 0.10 for this stage within the initial USD 2 allocation. Volume storage is a separate meter; about 11.55 GB of model files will be retained for reuse.
- No tensor runtime or model inference is involved in staging. It does not require the Ultra checkpoint.

## 4 November 2026 — checkpoint cached; serving dependency diagnostic

- CPU staging run `ap-Zq9TXDWoskLXV5Jg9VIa1Q` succeeded: 11,546,103,780 bytes, 176.73 seconds, no tensor runtime loaded. Exact source and per-file hashes are stored with the private Modal cache; local result is under `artifacts/runtime-validation/*-model-staging.json`.
- Serving-image build-only run `ap-2dHS9jWb0RC4Liw5iGEXg2` installed the pinned Torch 2.10.0 CUDA 12.8 stack but failed dependency resolution before allocating a GPU. Official Google ADK 1.36.1 requires Starlette below 1.0, whereas official prometheus-fastapi-instrumentator 8.1.0 requires Starlette 1.x. The source starter installs the wheelhouse with `--no-deps`; a fresh joint resolver is therefore not equivalent to that procedure.
- Preserve every supplied wheel/version. Obtain the starter's base-package inventory instead of silently upgrading or downgrading a research dependency. Saved failure log: `artifacts/runtime-validation/serving-image-build.log`; failed final image: `im-LI2XG4qhUZcE9j2ZkR2tJt`.
- Private CPU-only Kaggle diagnostic `bjacharya/gemma4-runtime-inventory-20261104`, version 1, was started with the starter's exact image digest and official wheel overlay. It exports package metadata before/after installation, does not import a tensor runtime, uses no GPU, and is not a competition submission.
- Latest observed workspace billing snapshot: USD 0 billed; USD 0.01 applied credits; ephemeral-app usage USD 0.01137950. Billing can lag and this is not a remaining-credit report. No GPU inference or software-repair score exists yet.

## 4 November 2026 — serving image ready; GPU probe allocation

- The private Kaggle inventory completed and its actual image digest matched the starter. Observed package metadata is committed in `requirements/kaggle-reference-versions.json`.
- Portable assembly was corrected to use the observed Starlette/OpenTelemetry family and the starter's `--no-deps` official wheel overlay. All official wheel hashes remain unchanged. Nonbundled supporting packages are a documented development reconstruction, not full scorer parity.
- CPU-only build `ap-BH5EsW1YYA5XqGXXSjH8t9` succeeded, including compiler/Transformers/LiteLLM import checks. Serving image: `im-gZnS5ebpNKdzlneWpOhl87`.
- Next run uses the committed serving probe: one L4, two requested physical CPU cores, 16 GiB requested RAM, 1,800-second function timeout, 900-second startup timeout, two-second scale-down window, zero function retries, and outbound networking blocked. The earlier requested-compute estimate is USD 0.766611, within the initial USD 2 allocation including small CPU-stage reserves.
- Scope: checkpoint load, one native tool call, and a synthetic local tool-result follow-up. No issue, reference patch, training data, adapter, or weight change is involved. A pass is protocol evidence, not a repair score or novel paper result.
