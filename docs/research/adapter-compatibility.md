# Controlled E4B adapter application on Modal

The synthetic compatibility probe passed on 4 November 2026. The zero adapter matched the base in every measured top-20 token log-probability list; the active adapter produced repeatable changes on all three fixed prefixes. Both adapters also resolved through the official compiler/adapter resolver/model registry and returned an ADK response.

This establishes the tested serving path on one A10G using the pinned official wheels. The remaining gate is validation in the official Kaggle scorer environment. No repair improvement, learned circuit, or original method is established.

## Package and controls

The approved E4B version-2 int4 checkpoint was unchanged. The [competition overview](https://www.kaggle.com/competitions/gemma-4-developer-agent) permits PEFT LoRA directories referenced by agents; the [staff update](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287) permits E4B. The declarative probe and two standard PEFT directories passed official size/security validation and compilation.

- Target: `model.language_model.layers.41.self_attn.o_proj`, logical dimensions `[2560, 4096]`, observed int32 packed shape `[2560, 512]`.
- Rank/alpha: 8/8; BF16 adapter tensors; fixed CPU seed 20261104. A is normalized by the square root of input width, B by the square root of rank. The zero adapter uses the same A with B set to zero. The active adapter uses deterministic random B. These are diagnostic weights with no task data or claimed repair benefit.
- Package size: 214,570 bytes, including YAML/configs/weights. Editable template/settings are under `submissions/adapter-probe-v1/` and `configs/adapter-probe-v1.toml`; generated packages remain ignored artifacts.
- Per prefix: base, zero, active, active, zero, base; temperature 0, fixed seed, one output token, top-20 log-probabilities keyed by token ID. No competition fixtures, problem statements, reference solutions, or verification tests were mounted.
- Prespecified limits: control drift at most 0.05 nats; active/zero difference greater than 0.20 nats and ten times observed control drift on at least two of three prefixes. Differences use a conservative lower bound when a token is absent from the other top-20 list.

## Results

| Synthetic prefix | Active/zero difference lower bound, nats | Maximum observed control/repeat drift |
| --- | --- | --- |
| `The capital of France is` | 2.892 | 0 |
| `def add(a, b):` followed by an indented `return` | 2.289 | 0 |
| `To list files in a directory, run` | 1.516 | 0 |

All 18 token requests completed. The zero/base and repeated base/zero/active comparisons were identical in the measured lists. All three active effects exceeded the fixed threshold; a listed adapter name alone was not used as evidence of application.

The two compiled-agent routes used the official `resolve_swegemma_adapter` path and `openai/<adapter_name>` registry entries. `probe_zero` returned `READY`; `probe_active` returned `READY.`. Both completed with a parsed ADK response. This covers the tested compiler/resolver/registry/runner route, rather than a full SWE task/scoring sandbox.

Model readiness was 237.21 seconds; total GPU function time was 244.57 seconds. The image remained `im-bEtC1IFnE2DCntpbAu56LW`, with the original parsers, context limit, dtype, and base settings; LoRA was explicitly enabled and sized from the discovered adapters. All 31 local regression checks and Ruff lint/format passed. Both remote apps and local CLI sessions completed; final inspection found no active project apps or queued requests.

## Provenance and next gate

- CPU preparation, [app](https://modal.com/apps/ach-bj100/main/ap-OvTeGK88BprUO8fFiM91BR): `artifacts/adapter-probe-v1/20261104T224306Z/prepare.json` and its generated `submission/` directory.
- GPU probe, runner `bc4e8a7`, [app](https://modal.com/apps/ach-bj100/main/ap-qH3X4eUiGiCXbQXkktkr1F): `artifacts/adapter-probe-v1/20261104T224734Z/gpu.json`. It retains raw responses, package/source/manifest identities, thresholds, numerical assessment, resolved routes, and server logs.
- Independent consistency checks: `artifacts/runtime-validation/adapter-probe-consistency.json`. [Reproduction workflow](../operations/adapter-probe.md); allocation/spending details are in the [run ledger](../operations/run-log.md).

Coverage is limited to this rank, projection, quantized checkpoint, runtime, and A10G/tensor-parallel-1 configuration. Validate the same controlled package on the official Kaggle image/scorer GPU setup before investing in repair adaptation. Preserve the fixed controls and package hashes; record any hardware/parallelism change as an explicit environment validation. Keep the reserved validation issues untouched.

The user confirmed Ultra before adapter construction/application. The probe stage is complete; return to Extra High for routine execution, and obtain Ultra confirmation again before subsequent weight analysis or edits.
