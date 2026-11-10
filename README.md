# Gemma 4 Developer Agent experiments

We are building an E4B coding agent for the competition's small-model prize and a Paper Track study of a closed-form rank-one weight edit. All remote work runs on Modal workspace `onepiecification` (earlier runs, through 6 November, used `ach-bj100`). Effort rules for weight work are in [AGENTS.md](AGENTS.md).

Current state (10 November 2026): the weight-space study is complete through v4 and the paper draft is in [docs/paper-latex/](docs/paper-latex/main.tex); the Writeup is not yet submitted. The adapter is not a competition candidate; `submissions/wsp-base-v1` is the control to improve.

## Repository layout

```text
configs/                Run plans, model/source identifiers, and cost assumptions
docs/
  operations/           Setup instructions and run/spend ledger
  research/             Strategy, frozen protocols, result notes, official-asset checksums
  paper-latex/          LaTeX paper draft, writing guide and source map
requirements/           Client lock, official wheel hashes, and runtime recipes
infrastructure/         Modal runners and private Kaggle runtime diagnostics
src/gemma4_lab/          Python orchestration and asset preparation
submissions/<candidate>/ Editable YAML agent configuration and prompts, one folder per candidate
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
.venv/bin/ruff check .
.venv/bin/ruff format --check .
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
MODAL_PROFILE=onepiecification .venv/bin/modal run infrastructure/modal/serve_smoke.py --task-id requests_7427 --controls-only
MODAL_PROFILE=onepiecification .venv/bin/modal run infrastructure/modal/serve_smoke.py --task-id requests_7427
```

The first remote command runs CPU grader controls. The second allocates one L4 only after matching controls pass. It preserves the baseline's one-minute/ten-tool-call settings, disables outbound networking, and records traces and test results under ignored `artifacts/baseline/`. Reference solutions are excluded from the agent invocation. Running the script without a task performs only a synthetic tool protocol check; `--build-only` allocates no GPU. The [baseline findings](docs/research/baseline.md) document a per-sandbox import-path adaptation needed for the development subprocess backend. Final candidates still require the official Kaggle environment.

If L4 capacity is unavailable, the recorded A10G development fallback uses the same agent/model settings and a separate rate card:

```sh
MODAL_PROFILE=onepiecification GEMMA4_RUN_CONFIG=configs/baseline-a10g.toml .venv/bin/modal run infrastructure/modal/serve_smoke.py --task-id requests_7427
```

Check its allocation first and cancel any earlier request before switching. Scheduling time is separate from Modal's startup/execution limits; monitor the request and cancel it if still unscheduled after 15 minutes. Leave no unattended queued app or deployment. Keep comparisons on matched hardware and budgets.

## Experiment plan

- [Baseline and compatibility findings](docs/research/baseline.md)
- [Controlled adapter application result](docs/research/adapter-compatibility.md)
- [Fixed development-panel results](docs/research/development-panel-v1.md)
- Weight-space study: protocols [v1](docs/research/weight-space-study-v1.md), [v2](docs/research/weight-space-study-v2.md), [v3](docs/research/weight-space-study-v3.md), [v4](docs/research/weight-space-study-v4.md); results [v1 screen](docs/research/wsp-screen-v1.md), [v2](docs/research/wsp-v2-panel-result.md), [v3](docs/research/wsp-v3-panel-result.md), [distillation](docs/research/wsp-v3-distill-result.md), [seeds](docs/research/wsp-v3-seeds-result.md), [v4](docs/research/wsp-v4-result.md)
- [Paper draft (LaTeX)](docs/paper-latex/main.tex) and [writing guide](docs/paper-latex/WRITING-GUIDE.md)
- [Rules and experiment decisions](docs/research/rules-and-decisions.md)
- [Dated novelty register](docs/research/novelty.md)
- [Prize strategy and schedule](docs/research/strategy.md)
- [Run and spending ledger](docs/operations/run-log.md)
- [Fixed panel workflow](docs/operations/panels.md)
- [Controlled adapter compatibility probe](docs/operations/adapter-probe.md)
- [Working agreement](AGENTS.md)

Each job's estimate is capped at USD 2 by `estimate_run`; the overall ceiling is the user's EUR 100. `plan` includes configured startup, execution, and idle time; image builds, staging, storage, and egress need separate accounting. It is an estimate, not a Modal billing limit.
