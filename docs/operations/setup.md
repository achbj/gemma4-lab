# Accounts and environments

## Verified access

On 4 November 2026, the Modal API confirmed workspace `ach-bj100`. Kaggle browser sign-in completed as `bjacharya`, the user confirmed competition entry, and authenticated file listing/downloads succeeded. Credentials remain in the services' normal home-directory configuration and are not copied into this repository.

Use an explicit profile for every Modal command:

```sh
MODAL_PROFILE=ach-bj100 .venv/bin/modal token info
MODAL_PROFILE=ach-bj100 .venv/bin/modal billing summary --for 'this month' --json
```

The checked billing summary reported USD 0 billed this month. It did not report remaining credit; the USD 30 balance is user-reported.

## Authentication on a fresh machine

```sh
.venv/bin/kaggle auth login
```

Complete the browser sign-in and [join the competition](https://www.kaggle.com/competitions/gemma-4-developer-agent). Keep credentials out of shell history, chat, and source control. Reuse the existing Modal profile through its official CLI; do not copy tokens into project configuration.

## Local versus remote runtime

Local Python is for orchestration, metadata inspection, hashing, and tests. The supplied `swegemma==0.2.11` wheel requires Python 3.12 or newer; the official wheelhouse also contains CPython 3.12 Linux binaries. Install that runtime on remote Linux, separately from local clients.

The starter notebook is stored under `data/raw/official/starter/` as reference material. Do not execute its Kaggle-specific paths or package installation cells on this Mac. Inspect wheel contents with ZIP tools instead of importing them locally.

Any local command that imports PyTorch must follow the specific escalation rule in [AGENTS.md](../../AGENTS.md).

## Updating dependencies

Direct local client versions live in `pyproject.toml`; the full local dependency snapshot is `requirements/tools.lock`. Update them deliberately together. The official harness is sourced from Kaggle and recorded separately by SHA-256 in `docs/research/official-assets.json`.

Do not replace the official vLLM wheel with a similarly numbered package from PyPI: the competition wheelhouse can contain host-specific rebuilds. Remote dependency selection is the next compatibility check.
