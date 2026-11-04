# Gemma 4 Developer Agent experiments

We are building an E4B coding agent for the competition's small-model prize. The first milestone is a measured baseline on Modal workspace `ach-bj100`. Weight interpretation and editing require an Ultra checkpoint with the user.

## Repository layout

```text
configs/                Run plans, model/source identifiers, and cost assumptions
docs/
  operations/           Setup instructions and run/spend ledger
  research/             Strategy, baseline notes, and official-asset checksums
requirements/           Client lock, official wheel hashes, and runtime recipes
infrastructure/         Modal runners and private Kaggle runtime diagnostics
src/gemma4_lab/          Python orchestration and asset preparation
submissions/baseline/   Editable YAML agent configuration and prompts
tests/                 Offline regression checks
data/raw/official/     Downloaded originals and inventories (ignored)
artifacts/             Generated run outputs (ignored; created when needed)
```

## Setup and local checks

Python 3.11+ is sufficient for local orchestration. The official remote evaluation harness requires Python 3.12+. No local command below imports PyTorch.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements/tools.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/gemma4-lab plan
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
```

The lock reproduces the local clients and lint tool. Official model/harness packages are kept separate and are not installed into this environment.

## Retrieve official references

Kaggle authentication and competition access have been verified. For a fresh machine, see [setup](docs/operations/setup.md).

```sh
.venv/bin/gemma4-lab inventory
.venv/bin/gemma4-lab fetch
.venv/bin/gemma4-lab verify
.venv/bin/gemma4-lab prepare-baseline
```

`inventory` lists all pages. `fetch` downloads at most 25 MiB of task descriptions, sample agent text, and three small harness wheels; it excludes weights and dummy adapters. `verify` checks recorded sizes and SHA-256 hashes. `prepare-baseline` copies the official sample, selects E4B for every agent, and removes incompatible 31B adapter references while preserving prompts, sampling, and evaluation settings. It refuses to overwrite an existing candidate.

These commands do not launch Modal compute or execute downloaded code. The prepared YAML still requires validation with the official remote harness before submission.

## Run the prepared baseline

Use the authenticated account and staged checkpoint described in [setup](docs/operations/setup.md). Record a new allocation in the [run ledger](docs/operations/run-log.md) before remote execution. The initial runner deliberately permits only one public development issue.

```sh
.venv/bin/gemma4-lab fetch-runtime
.venv/bin/gemma4-lab --task-id requests_7427 fetch-task
MODAL_PROFILE=ach-bj100 .venv/bin/modal run infrastructure/modal/serve_smoke.py --task-id requests_7427 --controls-only
MODAL_PROFILE=ach-bj100 .venv/bin/modal run infrastructure/modal/serve_smoke.py --task-id requests_7427
```

The first remote command runs CPU grader controls. The second allocates one L4 only after matching controls pass. It preserves the baseline's one-minute/ten-tool-call settings, disables outbound networking, and records traces and test results under ignored `artifacts/baseline/`. Reference solutions are excluded from the agent invocation. Running the script without a task performs only a synthetic tool protocol check; `--build-only` allocates no GPU. The [baseline findings](docs/research/baseline.md) document a per-sandbox import-path adaptation needed for the development subprocess backend. Final candidates still require the official Kaggle environment.

## Experiment plan

- [Baseline and compatibility findings](docs/research/baseline.md)
- [Rules and experiment decisions](docs/research/rules-and-decisions.md)
- [Dated novelty register](docs/research/novelty.md)
- [Prize strategy and schedule](docs/research/strategy.md)
- [Run and spending ledger](docs/operations/run-log.md)
- [Working agreement](AGENTS.md)

Initial Modal compute allocation is USD 2 estimated usage within the user's reported USD 30 credit. `plan` includes configured startup, execution, and idle time; image builds, staging, storage, and egress need separate accounting. It is an estimate, not a Modal billing limit.
