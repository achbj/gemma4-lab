# Fixed development-panel runs

The panel in `configs/development-panel-v1.json` contains four metadata-selected development cases. It does not contain any of the 68 reserved validation issues. Record a fresh allocation in [the run ledger](run-log.md) before running remote commands. Use only `MODAL_PROFILE=ach-bj100`.

## Prepare and qualify

The approved checkpoint and official wheel cache must already be staged as described in [setup](setup.md). Download each selected fixture through the bounded asset tool:

```sh
.venv/bin/gemma4-lab --task-id rich_3535 fetch-task
.venv/bin/gemma4-lab --task-id rich_3480 fetch-task
.venv/bin/gemma4-lab --task-id requests_6757 fetch-task
.venv/bin/gemma4-lab --task-id requests_6629 fetch-task
MODAL_PROFILE=ach-bj100 .venv/bin/modal run infrastructure/modal/serve_smoke.py --panel configs/development-panel-v1.json --controls-only
```

Fixture manifests belong in `docs/research/fixtures/`; raw files remain ignored. The limit is 128 MiB per fixture. CPU controls run all four cases, save each output, and preserve exclusions. A usable case requires an unchanged-checkout test failure (exit 1) or timeout (exit 124), followed by a reference fix that resolves with exit 0. A timeout alone is insufficient. The timeout amendment and original reports are retained in the ledger.

At least two cases must qualify. Do not replace rejected cases, reduce the minimum, alter tests, or use agent outcomes to change eligibility. Qualification on 4 November retained the two Rich cases and excluded both Requests cases because their reference controls failed. This subset cannot measure cross-repository transfer.

## Run the two fixed conditions

Both candidates must have matching successful CPU compilation reports. Keep evaluation and sampling files identical to those used by the controls. Confirm no prior project GPU job is active, then run these commands separately, verifying the first app has stopped before the second:

```sh
MODAL_PROFILE=ach-bj100 GEMMA4_RUN_CONFIG=configs/baseline-a10g.toml GEMMA4_CANDIDATE=baseline .venv/bin/modal run infrastructure/modal/serve_smoke.py --panel configs/development-panel-v1.json
MODAL_PROFILE=ach-bj100 GEMMA4_RUN_CONFIG=configs/baseline-a10g.toml GEMMA4_CANDIDATE=pagination-v1 .venv/bin/modal run infrastructure/modal/serve_smoke.py --panel configs/development-panel-v1.json
```

One A10G serves each fixed batch with a single model startup. Every case has a new evaluator, sandbox, and agent context. Reference solutions are stripped before the GPU invocation; verification tests stay out of agent workspace files. The checkpoint, official wheels, tools, and candidate budgets are unchanged. This is a fixed comparison, not an automatic tuning sweep.

### Matched three-minute diagnostic

The separately allocated `baseline-3m` and `pagination-v1-3m` candidates change only `max_time_minutes` from 1 to 3. Keep the original candidates and reports. Compile each named candidate, then rerun CPU controls with the new evaluation file; the runner requires matching control hashes and does not silently reuse controls from a different budget:

```sh
MODAL_PROFILE=ach-bj100 GEMMA4_CANDIDATE=baseline-3m .venv/bin/modal run infrastructure/modal/validate_compiler.py
MODAL_PROFILE=ach-bj100 GEMMA4_CANDIDATE=pagination-v1-3m .venv/bin/modal run infrastructure/modal/validate_compiler.py
MODAL_PROFILE=ach-bj100 GEMMA4_CANDIDATE=baseline-3m .venv/bin/modal run infrastructure/modal/serve_smoke.py --panel configs/development-panel-v1.json --controls-only
```

Require the same two qualified cases before launching either GPU condition. Run the earlier A10G commands separately with `GEMMA4_CANDIDATE=baseline-3m` and then `GEMMA4_CANDIDATE=pagination-v1-3m`, confirming the first app stopped. Reports remain under the same frozen panel directory, with distinct timestamps and candidate names. A longer time limit leaves the ten-tool-call cap unchanged; report whichever limit is reached.

### Feedback-only development screen

`feedback-v1-3m` changes only the root test-feedback policy relative to `baseline-3m`. Its separate allocation uses the saved three-minute baseline as a historical control. Existing three-minute CPU controls may be reused only if the runner's image, fixture, source, evaluation, and sampling identity checks pass; a prompt change does not change verification. Keep the fixed cases and exclusions. This screen is exploratory, with no fresh baseline draw.

```sh
MODAL_PROFILE=ach-bj100 GEMMA4_CANDIDATE=feedback-v1-3m .venv/bin/modal run infrastructure/modal/validate_compiler.py
MODAL_PROFILE=ach-bj100 GEMMA4_RUN_CONFIG=configs/baseline-a10g.toml GEMMA4_CANDIDATE=feedback-v1-3m .venv/bin/modal run infrastructure/modal/serve_smoke.py --panel configs/development-panel-v1.json
```

The batch reserves configured agent time, 300 seconds for verification, 120 seconds for setup, and 30 seconds for shutdown before starting another case. Its Modal function still has a hard execution timeout; requested CPU/RAM and estimated cost are not provider billing caps. Preserve skipped/incomplete cases as resource failures instead of silently dropping them.

## Reports and stopping

Reports live under ignored `artifacts/panels/development-panel-v1/`. CPU controls, source/fixture/runtime identities, candidate hashes, package versions, each completed case, and final server logs are retained. GPU results stream to an atomic local report after each case; an interrupted stream keeps earlier outputs and records the error.

Use `evaluation.results.agent.resolved` for repair success. Pipeline completion or a valid test exit is not a successful repair. Report paired outcomes, exclusions, timeouts, and the very small sample. One draw per condition is not a robust gain or novelty claim.

Scheduling is separate from startup/execution timeouts. Monitor the app and cancel it if still unscheduled after 15 minutes:

```sh
MODAL_PROFILE=ach-bj100 .venv/bin/modal app stop --yes APP_ID
MODAL_PROFILE=ach-bj100 .venv/bin/modal app list --json
```

Leave no queued request or deployment after the experiment. Do not launch a replacement until cancellation is confirmed. Weight interpretation and edits still require the user's Ultra checkpoint.
