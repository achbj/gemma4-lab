# Synthetic adapter compatibility probe

This probe checks the pinned E4B serving path before repair adaptation. It uses synthetic text only, with no issue fixtures or reference solutions. Its adapters are diagnostic perturbations with no claimed repair benefit.

The checkpoint and official wheels must already be staged as described in [setup](setup.md). Use only `ach-bj100`, record a bounded allocation in the [run ledger](run-log.md), and obtain the user's Ultra confirmation before constructing/applying adapter weights.

## Prepare on CPU

```sh
MODAL_PROFILE=ach-bj100 .venv/bin/modal run infrastructure/modal/adapter_probe.py --prepare-only
```

Settings are fixed in `configs/adapter-probe-v1.toml`; editable probe YAML lives in `submissions/adapter-probe-v1/`. CPU preparation checks the actual packed projection metadata, builds zero/nonzero rank-8 PEFT packages, validates them with official submission limits, and compiles both aliases with inference disabled. It leaves the base unchanged. Generated files and provenance belong under ignored `artifacts/adapter-probe-v1/<UTC timestamp>/`.

Require `passed=true`, `completed=true`, the expected runtime image, and the exact generated file hashes. Preserve every failed preparation report. Do not silently relax settings or reuse a package after changing its preparation/serving source.

## Run one explicitly allocated GPU probe

Use the successful report printed by preparation. The first recorded example is:

```sh
MODAL_PROFILE=ach-bj100 .venv/bin/modal run infrastructure/modal/adapter_probe.py --preflight artifacts/adapter-probe-v1/20261104T224306Z/prepare.json
```

The runner checks settings, template, source hashes, runtime image, and package hashes before invocation. It mounts no competition fixtures. One A10G serves the base, zero adapter, and active adapter. Per prefix, requests run in base/zero/active/active/zero/base order, with deterministic one-token sampling and top-20 token log-probabilities.

Compatibility requires the fixed numerical controls/effect thresholds and successful compiled-agent routing/response checks. The raw responses, conservative top-k difference bounds, resolved aliases, packages, model manifest, and server logs are retained. Partial events stream to an atomic local `gpu.json` report; pipeline completion is separate from `passed`.

Monitor scheduling separately and cancel a request still unscheduled at 15 minutes. Confirm the app stopped after completion/failure; leave no queued request or deployment. Do not automatically vary rank, amplitude, or target module after a failed test.

## Interpretation

Successful discovery or a listed model alias establishes only registration. A stable zero/base control and reproducible nonzero effect provide evidence that the served adapter is applied. The compiled-agent checks cover the official compiler/adapter resolver/registry route. Modal uses the pinned official wheels but does not establish complete Kaggle scorer hardware/environment parity; verify the final adapter there before investing in adaptation claims.

The [source audit](../research/baseline.md#adapter-serving-interface-audit-4-november) records the original interface evidence. Remind the user to return to Extra High after the weight/probe stage, and retain the Ultra checkpoint for subsequent weight work.
