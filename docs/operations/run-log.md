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
