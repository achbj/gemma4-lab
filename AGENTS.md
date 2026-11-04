# Competition working agreement

## Repository organization

- Keep Python orchestration in `src/gemma4_lab/`, its tests in `tests/`, and run settings in `configs/`.
- Keep editable competition YAML and prompts in `submissions/<candidate>/`, separate from Python tooling.
- Put strategy, research notes, and source provenance in `docs/research/`; setup instructions and the run ledger in `docs/operations/`.
- Keep dependency locks in `requirements/`. Downloaded originals belong in ignored `data/raw/official/`; generated run outputs belong in ignored `artifacts/`.
- Keep the repository root limited to standard entry files such as `README.md`, `AGENTS.md`, `pyproject.toml`, and `.gitignore`. Add infrastructure files only when the corresponding runner is implemented. Do not leave scratch scripts or duplicate docs at the root.

## Commit workflow

- Commit each completed logical edit separately, immediately after its relevant checks pass. Do not accumulate unrelated changes into a bulk commit.
- Prefer one file or one closely related change per commit. Keep implementation and its corresponding regression tests together when they form a single change.
- Stage explicit file paths and inspect the staged diff. Preserve any unrelated user changes.
- Use concise commit messages that describe the specific result. Commit locally; push only when the user requests it.

## Goal and budget

- Aim for a monetary prize in the Gemma 4 Developer Agent competition, initially targeting the E2B/E4B small-model category.
- Use only the `ach-bj100` Modal workspace for this project. Set `MODAL_PROFILE=ach-bj100` explicitly on every Modal command; do not rely on the global active profile.
- The user reports USD 30 of existing Modal credit. Prefer this credit for remote experiments. Total additional compute/API spending must remain within the user's EUR 100 ceiling; existing credits are not permission to exceed that ceiling.
- Keep a spend/run ledger. Before a GPU run, estimate cost from current rates, bound resource count and runtime, and record the estimate. No idle deployments or automatic experiment sweeps. Initial baseline allocation: at most USD 2 estimated usage, within the reported credit.

## Reasoning effort and token use

- The user's routine setting is GPT-6.1 Sol, Extra High. Keep updates, logs, and research retrieval concise; reuse saved findings.
- Before substantial interpretation of model weights, causal diagnosis from weights/activations, or designing/applying a weight edit, stop and ask the user to switch this chat to Ultra. If a supported tool can reliably change the current chat's selected effort, it may be used and the result must be verified. Do not claim to have changed effort without evidence.
- Resume weight work only after the switch is confirmed. Ordinary setup, access checks, baseline inference, and collection of behavioral metrics can proceed at the routine setting.
- After the weight-analysis/edit stage, remind the user to return to Extra High for routine execution.
- Do not launch separate paid LLM calls or delegate work merely to emulate Ultra.

## Runtime and reproducibility

- Local `.venv` contains orchestration clients only. Keep the competition's official remote harness, checkpoint, pinned research dependencies, and experiment settings unchanged unless a deliberate experiment is documented.
- Before any local command expected to import PyTorch, including indirect imports through Transformers, tests, quantization, or LLM scripts, use `require_escalated` for that specific command. Explain the known macOS OpenMP shared-memory failure. Do not first try it sandboxed. Use the project interpreter and directory. If escalation is unavailable or denied, report the limitation instead of retrying the crash.
- The local OpenMP workaround does not apply to remote Linux/Modal commands. Do not set `KMP_DUPLICATE_LIB_OK`, suppress crash reporting, or globally disable the sandbox.
- Keep tokens and credentials out of project files, logs, and chat. Authenticate through the services' normal local/browser flows.
- Confirm adapter compatibility with the official scorer before investing in adaptation. Keep development issues separate from reserved validation issues.

## Rules and research claims

- Before each experiment, record the relevant competition rule/source, the proposed change, its budget, and the control needed to assess it. Distinguish explicit permission from interpretation; resolve material ambiguity before relying on it in a submission.
- Choose the best measured approach under the competition's model, harness, time, and cost constraints. Compare against simpler controls before claiming an improvement; do not claim global optimality from a limited search.
- Treat the published weight-space programming method and its replications as prior work. Maintain a dated novelty register, recheck related work when choosing a paper claim and immediately before submission, and narrow or drop any claim already covered elsewhere.
- Novelty remains provisional until the final review. Report only demonstrated contributions and limits, cite borrowed methods, and keep the paper's original work distinct from reproduction or integration.
