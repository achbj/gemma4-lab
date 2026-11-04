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

## 4 November 2026 — serving passed; single-issue allocation

- GPU protocol run `ap-X5bA7whrQaI6m0tYq4rZJ1` passed on one NVIDIA L4. Python 3.12.10; image `im-gZnS5ebpNKdzlneWpOhl87`; runner commit `23fe5b3`. Server readiness took 221.77 seconds and the remote function took 225.46 seconds. E4B emitted a valid `get_status` call and handled a synthetic tool response. Raw report: `artifacts/runtime-validation/20261104T131849Z-serving-smoke.json`.
- Next public development case: `requests_7505`. Its snapshot, graph, embeddings, and dependency wheels total 67,090,113 bytes; hashes are in `docs/research/fixtures/requests_7505.json`. It is a development fixture, not reserved validation.
- First run CPU-only unchanged/reference-patch grader controls, in separate sandboxes, with no LLM. One container, two requested CPU cores, 2 GiB RAM, 900-second function/startup limits, two-second scale-down, no retries, outbound networking blocked. Requested-compute bound is about USD 0.0552; reserve USD 0.10 including overhead within the initial USD 2 allocation.
- Only if those controls distinguish failure from success, attempt the issue using the unchanged reference agent: one minute, ten tool calls, fifty turns, 60-second command timeout, and 300-second verification timeout. Retain the serving runner's one-L4 resource/time bounds and USD 0.766611 requested-compute estimate. Combined initial experiment estimates remain below USD 2, including earlier small CPU reserves and the completed short probe; provider billing may differ.
- Control results are not mounted into the agent invocation. The reference solution is removed from that invocation's task payload; verification-only tests remain in host memory. The mounted fixture contains no task-answer JSONL. Save full agent trace, patch, test output, package versions, submission hashes, and source/fixture identities.
- Rules support remains the baseline decision in `docs/research/rules-and-decisions.md`: approved E4B, unchanged official wheels and candidate settings, private development, and no submitted Python orchestration. No weight interpretation, adapter, or novelty claim is involved.

## 4 November 2026 — grader diagnostics and utility-case fallback

- CPU controls `ap-sLkeC1xxUXA3qKLTqc2Wnq` found missing pytest; no tests ran. After restoring the reference test-runtime packages, repeat controls on image `im-bEtC1IFnE2DCntpbAu56LW` reached tests, but both patches failed: 197 HTTP-fixture errors and four network-related failures remained even with the reference fix. Reports: `artifacts/baseline/20261104T133523Z-requests_7505-controls.json` and `20261104T133733Z-requests_7505-controls.json`. No GPU agent was launched for this unsuitable fixture.
- Move the first compatibility case to public development issue `requests_7427`, whose verification targets `tests/test_utils.py`. Selection is based on environment suitability, not agent success; this case cannot represent an unbiased benchmark sample. Preserve the failed controls and the official test/harness logic unchanged.
- Repeat the same bounded CPU controls and, only on a pass, the same bounded L4 baseline. This is a replacement compatibility case, not a sweep. Combined CPU functions so far ran for about 43.1 seconds; the existing USD 0.10 control reserve remains sufficient for another short diagnostic, subject to observed billing. All work remains within the initial USD 2 estimate allocation.
- Latest billing snapshot after serving: workspace ephemeral-app meter USD 0.08010894, applied credits USD 0.08, current-month billed USD 0. Storage and network meters are offset by allowances. Billing may lag and does not establish remaining credit.

## 4 November 2026 — utility grader validated; agent launch

- Initial `requests_7427` controls both passed, exposing host-package shadowing in the supplied subprocess backend. Those results are invalid repair evidence and remain preserved in `artifacts/baseline/20261104T134102Z-requests_7427-controls.json`.
- Deliberate development adaptation `76cc86a` restores each sandbox checkout's root/`src` import paths in its isolated venv. No official wheel, task/test patch, agent setting, or model is modified. Rationale and parity limits are in `docs/research/baseline.md`.
- Corrected CPU controls passed in `ap-isbVfCi6SpOBDz2cUaUYZI`, image `im-bEtC1IFnE2DCntpbAu56LW`, source commit `76cc86a`. Unchanged checkout: 1 failed, 215 passed, 13 skipped. Reference fix: 216 passed, 13 skipped. Report: `artifacts/baseline/20261104T134317Z-requests_7427-controls.json`. No LLM calls occurred.
- Proceed with the already reserved single-L4 reference agent attempt on `requests_7427`. Keep one minute/ten tool calls/fifty turns and 300-second verification. Only the issue, allowed hints, and repository enter the agent context; no reference solution or control output is an agent input. This selected pilot is excluded from any later reserved validation set.

## 4 November 2026 — synthetic-gate correction

- Run `ap-oxgDi3HBYpgdlZnK4GUBpG` loaded E4B in 215.01 seconds and completed its function in 218.46 seconds. The first synthetic response was a valid native `get_status` call. The follow-up returned HTTP 200 with an empty message and normal `stop`; the overly strict probe gate aborted before any real issue/agent call. Report: `artifacts/baseline/20261104T135001Z-requests_7427-agent.json`. No repair score was measured.
- Keep that failed behavioral probe unchanged in the record. Correct the development runner to distinguish instruction-following observations from HTTP/schema failures: synthetic behavior must not select whether an otherwise functioning server attempts the baseline. HTTP/schema failures still abort; model behavior remains visible in the report. No candidate/prompt/sampling/budget change is made.
- Repeat one bounded repair attempt, not an experiment sweep. The two completed GPU functions total about 443.92 seconds, roughly USD 0.126 requested-resource compute plus startup/overhead. With the short CPU diagnostics and the next USD 0.766611 requested-compute reservation, the initial USD 2 estimate allocation still has room. Verify observed billing after completion; no automatic retry is enabled.

## 4 November 2026 — capacity queue and planned A10G fallback

- Corrected L4 run `ap-QOBq8qoIh0LCw08cpyh33S` was created at 13:51:37 UTC. API inspection showed one queued input, zero containers, and zero running inputs. [Modal timeouts](https://modal.com/docs/guide/timeouts) cover execution/startup separately from scheduling; impose an additional manually monitored 15-minute scheduling limit. If still unscheduled, stop the app and verify cancellation before another request.
- Planned capacity fallback: `configs/baseline-a10g.toml` in the same `ach-bj100` workspace. This deliberate hardware change retains the exact checkpoint, official wheels, serving flags, candidate prompts/sampling, one-minute agent budget, and resource/count/time bounds. Hardware throughput differs and this result must be labelled as A10G development evidence, not a matched L4 comparison or scorer parity.
- Fresh account rate API reports GPU A10G USD 1.10/hour, L4 USD 0.80/hour, physical CPU USD 0.04730/core-hour, and RAM USD 0.00800/GiB-hour. Per-second estimates round upward. A10G requested-compute reservation: USD 0.992720, excluding builds/storage/egress. Existing observed ephemeral usage is about USD 0.16, so the new reservation plus prior small diagnostic reserves remains within the initial USD 2 allocation. Latest billed amount remains zero; credit balance is not independently exposed.
- Only one GPU request at a time. No deployment, automatic sweep, paid teacher API, weight edit, or adapter is involved. Stop an unscheduled fallback after the same 15-minute scheduling limit; preserve the cancellation instead of leaving an unattended request.
- At the deadline the L4 backlog was still one with zero containers/inputs. App `ap-QOBq8qoIh0LCw08cpyh33S` was stopped and verified `stopped`, zero tasks, at 14:07:18 UTC. The first noninteractive stop command required `--yes`; the corrected command succeeded. No GPU function executed in that app. Only after verification was the A10G fallback requested.

## 4 November 2026 — first real baseline result; prompt-control allocation

- A10G run `ap-bobUmGLMOuYYJXoqgv7hPH` completed, image `im-bEtC1IFnE2DCntpbAu56LW`, runner commit `34f2167`, approved E4B version 2. Readiness: 245.27 seconds; total function time: 316.77 seconds. Report: `artifacts/baseline/20261104T141310Z-requests_7427-agent.json`. All experiment apps were subsequently verified stopped.
- Unchanged agent outcome: no patch, no explicit submission, 12 LLM calls, 10 counted tool calls, session timeout after about 63.32 seconds. The official evaluator returned before verification (`test_exit_code=-1`, no test output). This is a failed budget-limited agent attempt, not a measured test failure or official leaderboard score. The unchanged/reference CPU controls separately establish that the original checkout fails and the supplied fix passes.
- Trace observation: repeated reads of the first truncated file region, an oversized requested read still subject to the 150-line cap, and an analyzer reporting the target absent after partial navigation. No source edit was made. This is one pilot observation; it establishes neither a general failure rate nor a weight-level cause. Trace usage totals 80,651 prompt and 4,049 completion tokens; the official task summary incorrectly reports zero tokens, so retain the raw trace.
- Current workspace ephemeral meter: USD 0.28656028; credits applied USD 0.29; billed USD 0. This includes setup/diagnostics and may lag. It is not an exact remaining-credit balance.
- Next bounded experiment: `submissions/pagination-v1`, a generic line-range navigation instruction appended to root and analyzer prompts. All other candidate files are byte-identical to baseline. Rules support: declarative prompt changes are supported by the official compiler; no custom submitted Python, extra tools, external inference, model edit, reference solution, or reserved validation feedback is used.
- Hypothesis: better handling of truncated reads reduces repeated navigation and allows a source edit/submission under the same one-minute/ten-tool-call budget. Control: the completed baseline on the same A10G, same checkpoint/image/harness/serving flags and sampling. Compare actual patch/submission, verification outcome, repeated reads, tool/LLM calls, and elapsed time. A pilot success is development evidence only; preserve a failure and broaden later before any general claim.
- Reserve one A10G run with the same USD 0.992720 requested-compute estimate and 15-minute scheduling limit, within the initial USD 2 allocation after observed usage. No sweep or automatic retry. Validate candidate compilation on CPU first; the task/fixture grader controls remain applicable because only agent instructions differ.
