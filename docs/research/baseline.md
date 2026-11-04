# Baseline specification and findings

## Sources acquired on 4 November 2026

- [Official starter notebook](https://www.kaggle.com/code/ryanholbrook/getting-started-gemma-4-developer-agent): downloaded source and input metadata under `data/raw/official/starter/`.
- `HARNESS_README.md`, public tasks, and sample submission from the [competition data](https://www.kaggle.com/competitions/gemma-4-developer-agent/data).
- Three small wheels from the [official wheelhouse](https://www.kaggle.com/datasets/metric/gemma-4-developer-agent-wheelhouse): `adk-eval-core==0.1.0`, `adk-submission==0.2.13`, and `swegemma==0.2.11`. Their contents were inspected as ZIP data, not imported.

The complete file inventory contains 524 competition assets and 41 wheelhouse assets. The task file contains 129 development issues across FastAPI, HTTPX, Requests, and Rich. Ground-truth patches are present in that file; future agent input must expose only the issue, hints, and repository state.

## Candidate configuration

The official starter's model-selection procedure is followed for `submissions/baseline/`: select `gemma-4-e4b-it-qat-w4a16-ct` for the root and analyzer agents and remove the sample 31B-shaped adapters. The source copy remains in the ignored raw-data directory. Prompts, sampling, and evaluation settings remain the supplied reference settings.

The sample evaluation budget is one minute and ten tool calls per issue. This is a compatibility reference, not a tuned competition configuration. Any later budget or prompt change must be a named experiment with a comparison against this reference.

The approved model source is `google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2`, exactly as listed in the starter's input metadata. Its file listing reports a single 11,513,861,828-byte weight file. Model metadata was listed; weights have not been downloaded or inspected. Single-L4 fit must be measured, not inferred from the E4B name.

## Remote compatibility work remaining

1. Reproduce a Python 3.12 Linux environment using the official wheelhouse and compatible base dependencies. The wheelhouse contains `vllm==0.19.1` and `transformers==5.13.1`; exact wheel hashes matter.
2. Prove checkpoint load and a tool-call round trip before evaluating an issue. Use the starter's Gemma tool/reasoning parsers, 32,768-token context, and documented environment settings.
3. Verify the YAML using the official compiler/validator. Current local tests cover preparation, asset integrity, and spending estimates; they do not establish acceptance by the scorer.
4. Attempt one public Requests issue and record the raw trace, patch, verification result, exact package versions, runtime, and cost. Start with `requests_7505` only if its repository/test setup passes the reference controls.
5. Verify adapter application separately before adapting weights. Weight interpretation and editing require the user's Ultra checkpoint.

The initial Modal plan uses one L4, whereas the scorer uses four L4s. This development configuration must be labelled separately, and final candidates must be rechecked in the official Kaggle environment. No benchmark success or model improvement has been measured yet.
