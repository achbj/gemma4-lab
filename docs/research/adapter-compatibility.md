# Controlled E4B adapter application across serving environments

The synthetic compatibility probe passed on Modal on 4 November 2026 and on the official Kaggle image with four L4 GPUs on 5 November. The exact same adapter package was used. In each environment, the zero adapter matched the base in every measured top-20 token log-probability list; the active adapter produced repeatable changes on all three fixed prefixes. Both adapters resolved through the official compiler/adapter resolver/model registry and returned an ADK response.

The tested inference/adapter route is verified on the target Kaggle image and hardware. End-to-end SWE task judging, repair improvement, learned circuits, and an original method remain unmeasured.

## Package and controls

The approved E4B version-2 int4 checkpoint was unchanged. The [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent) permits PEFT LoRA directories referenced by agents; the [staff update](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287) permits E4B. The declarative probe and two standard PEFT directories passed official size/security validation and compilation.

- Target: `model.language_model.layers.41.self_attn.o_proj`, logical dimensions `[2560, 4096]`, observed int32 packed shape `[2560, 512]`.
- Rank/alpha: 8/8; BF16 adapter tensors; fixed CPU seed 20261104. A is normalized by the square root of input width, B by the square root of rank. The zero adapter uses the same A with B set to zero. The active adapter uses deterministic random B. These are diagnostic weights with no task data or claimed repair benefit.
- Package size: 214,570 bytes, including YAML/configs/weights. Editable template/settings are under `submissions/adapter-probe-v1/` and `configs/adapter-probe-v1.toml`; generated packages remain ignored artifacts.
- Per prefix: base, zero, active, active, zero, base; temperature 0, fixed seed, one output token, top-20 log-probabilities keyed by token ID. The probe uses synthetic text only. Modal mounted no task fixtures. Kaggle attached the competition for eligibility, but the runner read no issue, reference-solution, or verification-test files.
- Prespecified limits: control drift at most 0.05 nats; active/zero difference greater than 0.20 nats and ten times observed control drift on at least two of three prefixes. Differences use a conservative lower bound when a token is absent from the other top-20 list.

## Results

| Synthetic prefix | Modal A10, TP=1: difference lower bound, nats | Kaggle L4x4, TP=4: difference lower bound, nats |
| --- | --- | --- |
| `The capital of France is` | 2.892 | 2.988 |
| `def add(a, b):` followed by an indented `return` | 2.289 | 2.309 |
| `To list files in a directory, run` | 1.516 | 1.344 |

Each environment completed all 18 token requests. Maximum measured control/repeat drift was zero in both runs. All three active effects exceeded the fixed threshold within each environment; cross-hardware log-probabilities were not required to match. A listed adapter name alone was not used as evidence of application.

The two compiled-agent routes used the official `resolve_swegemma_adapter` path and `openai/<adapter_name>` registry entries. `probe_zero` returned `READY`; `probe_active` returned `READY.`. Both completed with a parsed ADK response. This covers the tested compiler/resolver/registry/runner route, rather than a full SWE task/scoring sandbox.

Model readiness was 237.21 seconds; total GPU function time was 244.57 seconds. The image remained `im-bEtC1IFnE2DCntpbAu56LW`, with the original parsers, context limit, dtype, and base settings; LoRA was explicitly enabled and sized from the discovered adapters. All 31 local regression checks and Ruff lint/format passed. Both remote apps and local CLI sessions completed; final inspection found no active project apps or queued requests.

## Modal provenance

- CPU preparation, [app](https://modal.com/apps/ach-bj100/main/ap-OvTeGK88BprUO8fFiM91BR): `artifacts/adapter-probe-v1/20261104T224306Z/prepare.json` and its generated `submission/` directory.
- GPU probe, runner `bc4e8a7`, [app](https://modal.com/apps/ach-bj100/main/ap-qH3X4eUiGiCXbQXkktkr1F): `artifacts/adapter-probe-v1/20261104T224734Z/gpu.json`. It retains raw responses, package/source/manifest identities, thresholds, numerical assessment, resolved routes, and server logs.
- Independent consistency checks: `artifacts/runtime-validation/adapter-probe-consistency.json`. [Reproduction workflow](../operations/adapter-probe.md); allocation/spending details are in the [run ledger](../operations/run-log.md).

## Official Kaggle validation, 5 November

Private [notebook version 2](https://www.kaggle.com/code/bjacharya/gemma4-adapter-compatibility-20261105) completed with `passed=true`. A no-run revision was saved first; authenticated readbacks verified private/offline metadata, the exact official image digest, only approved E4B version 2, and byte-identical generated/executed source. The competition attachment satisfied the restricted L4 eligibility rule; this was not a leaderboard submission.

The runner verified all eight checkpoint files against the original staging SHA-256 hashes, overlaid the same 41 pinned wheel bytes without dependency resolution, and confirmed four `NVIDIA L4` devices. Tensor parallelism was explicitly 4. Python was 3.12.13 versus Modal's 3.12.10; Torch 2.10.0+cu128, vLLM 0.19.1, Transformers 5.13.1, adk-submission 0.2.13, swegemma 0.2.11, Google ADK 1.36.1, and LiteLLM 1.82.4 matched. No adapter tensor or threshold changed.

Model readiness was 368.48 seconds; the measurement function took 382.26 seconds. Total script time, including wheel installation and checkpoint verification, was 564.11 seconds. Both compiled routes returned the same respective texts as on Modal. Status reached `COMPLETE`; native quota values confirm zero GPU time reserved, 1,143.392 seconds consumed, and 29.6824 hours remaining from 30. No Modal compute or paid API was used for this check.

Artifacts:

- Frozen bundle/build manifest: `artifacts/kaggle-adapter-probe/20261105-v1/`; payload SHA-256 `6ea5c854b0c2bba855652c49c1ac39ea44a86e5ea70b37daea010fa63972da72`.
- Source/metadata readbacks: `artifacts/kaggle-adapter-probe/readback-v1/` and `readback-v2/`.
- Raw report/log: `artifacts/kaggle-adapter-probe/output-v2/`; report SHA-256 `68bc5d3ecdedbaf0f071b5c68971d81d113b5a733f00ac1f3e86f3925566a527`.
- Independent measurement/provenance verification: `artifacts/runtime-validation/kaggle-adapter-consistency-v2.json`; native quota values: `kaggle-adapter-quota-native-after.json`. The SDK's `to_dict()` duration serializer loses whole days; its saved reserialization is not a raw HTTP response and must not be used to infer remaining quota.

## Scope and next research step

Coverage remains limited to the tested rank, projection, quantized checkpoint, and these two serving configurations. This clears the tested deployment prerequisite; final candidate acceptance and full SWE judging still require their own checks. Preserve the frozen controls/package hashes and reserved validation partition.

Next, build focused behavioral diagnostics for edit integrity and failed-test handling before selecting a weight intervention. Compare any proposed intervention against the preserved simple controls and measure verified repairs on fresh development cases. Novelty stays provisional and requires a new prior-work review at claim selection and submission.

The user confirmed Ultra before adapter construction/application. The probe stage is complete; return to Extra High for routine execution, and obtain Ultra confirmation again before subsequent weight analysis or edits.
