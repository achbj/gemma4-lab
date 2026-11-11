# gemma4-lab

Experiments for the Kaggle Gemma 4 Developer Agent competition on the quantized E4B model: a declarative coding agent, and a training-free rank-one weight edit shipped as a standard PEFT LoRA adapter.

## Layout

```text
configs/         Run plans, panels, frozen case sets, fixture manifests, cost assumptions
infrastructure/  Modal runners and Kaggle runtime diagnostics
requirements/    Client lock and official wheel hashes
src/gemma4_lab/  Python orchestration, weight I/O, adapter construction, evaluation
submissions/     One folder per agent candidate (YAML, prompts, skills)
tests/           Offline regression checks
```

Downloaded competition files go to `data/` and run outputs to `artifacts/`; both are ignored.

## Setup

Python 3.11 or newer. The local environment holds orchestration clients only and never imports PyTorch.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements/tools.lock
.venv/bin/python -m pip install --no-deps -e .
```

## Local checks

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

## Fetch the official assets

Sign in to Kaggle (`.venv/bin/kaggle auth login`) and join the competition first.

```sh
.venv/bin/gemma4-lab inventory
.venv/bin/gemma4-lab fetch
.venv/bin/gemma4-lab verify
.venv/bin/gemma4-lab fetch-runtime
.venv/bin/gemma4-lab --task-id rich_4077 fetch-task
```

`verify` checks every downloaded file against the recorded sizes and SHA-256 hashes.

## Run an agent candidate

Remote runs use [Modal](https://modal.com). The runners are pinned to a single Modal profile as a spending guard; set your own profile name in `configs/*.toml`, `src/gemma4_lab/config.py` and the runner scripts before use, and stage the approved checkpoint with `infrastructure/modal/stage_model.py`.

```sh
export MODAL_PROFILE=<your-profile>
export GEMMA4_CANDIDATE=wsp-base-v1

# 1. Compile the candidate with the official compiler (CPU only)
.venv/bin/modal run infrastructure/modal/validate_compiler.py

# 2. Qualify the panel's issues with grader controls (CPU only)
.venv/bin/modal run infrastructure/modal/validate_panel.py --panel configs/development-line-anchored-v1.json

# 3. Run the agent on the panel (one A10G, network blocked)
GEMMA4_RUN_CONFIG=configs/real-issue-check-a10g.toml .venv/bin/modal run infrastructure/modal/serve_smoke.py --panel configs/development-line-anchored-v1.json
```

Reports are written under `artifacts/`. Each run is bounded by the timeout in its config; `.venv/bin/gemma4-lab plan` prints the cost estimate before you launch.

## Weight-edit study

The rank-one edit is built and evaluated by `infrastructure/modal/prepare_wsp_v2.py`, `wsp_v3_select.py` and `evaluate_wsp_v2.py`, using the frozen cases and panels in `configs/wsp-v*.json`. The gradient-trained comparison is `wsp_v3_distill.py`.
