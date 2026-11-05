# Deadline-bound weight-space study

Decision date: 5 November 2026. Targets: the Paper Track by **12 November, 23:59 UTC**
and a separately eligible main-track E4B agent. Internal submission target: **11 November**.
This protocol sets the research scope; it does not authorize an unspecified GPU sweep.

## What has and has not been tested

| Question | Current evidence |
| --- | --- |
| Infer an unknown network's training task from its weights | Not attempted |
| Construct a game-playing network without feedback | Not attempted; does not produce an eligible Gemma coding agent |
| Diagnose a learned Gemma behavior from numerical weights and deliberately edit it | Not attempted |
| Load a synthetic adapter and measure its application | Passed on Modal and the official Kaggle image; diagnostic random weights only |
| Improve repair performance with prompt controls | Synthetic edit-recovery gain; no verified gain on the four-case real development screen |

The existing zero/random adapter probe is deployment evidence, not semantic weight
understanding. Our failed agent runs do not test or refute the article's claims.
The article's small-network demonstrations, feedback-assisted Qwen editing, and
unsuccessful Gemma 3 math experiment have different conditions. We have not reproduced
them. The current chat/model is not evidence of a matched GPT-6 Astra replication.

## One research question

Can a task-directed, LLM-reasoned weight intervention improve a frozen quantized E4B
coding agent's recovery behavior and independently verified repairs beyond cheap
prompt controls and matched nonspecific interventions?

This is a transfer/feasibility question, not an assertion that Gemma or LoRA makes the
method new. The actual mechanism, inspected tensors and intervention must be selected
only after the required Ultra confirmation. No matrix, direction or amplitude is
chosen by this document.

## Bound the work

1. Correct the known context/output mismatch once, with the same generation settings
   across all study conditions. Check the correction on fixed diagnostic inputs;
   do not restart an open-ended prompt/harness search.
2. After Ultra confirmation, inspect actual numerical weights and write a falsifiable
   explanation and predicted effect **before** testing an intervention. Preserve exact
   inspection queries, outputs, model identity, tensor provenance and proposed change.
   If no defensible explanation emerges, record that as a feasibility outcome.
3. Permit **one primary intervention and at most one documented revision** using
   development evidence. No gradient training, automatic sweeps, or hidden-test access
   in this bounded WSP attempt. State exactly which behavioral feedback was available;
   our prior trace inspection prevents a claim of feedback-free discovery.
4. Freeze and compare the unchanged base, simple prompt control, task-directed edit,
   and a matched nonspecific/identity control. Specify and hash the exact controls,
   budgets and decision thresholds before allocating GPU inference. Adapter loading
   alone and token changes cannot count as semantic or repair improvements.
5. Freeze the selected candidate before any reserved issue content is inspected.
   Select held-out issue IDs from metadata, retain base/reference qualification failures,
   and evaluate real repairs with the same budgets. Keep targets and unaffected cases
   separate; report paired wins/losses, uncertainty, regressions, failures and cost.

Existing inspected synthetic cases and both Rich panels are development data. All
68 reserved issues remain untouched. A synthetic gain alone cannot support repair
transfer. If controls do not isolate a weight effect, say so; no causal claim follows
from an LLM's explanation alone.

## Dates and decisions (UTC)

| By | Required deliverable |
| --- | --- |
| 5 November | This protocol, initial paper draft, verified requirements, entry check and fresh overlap review |
| 6 November | Numerical inspection and one frozen, testable proposal after Ultra confirmation; context correction checked once |
| 7 November | First genuine WSP feasibility result against controls; select one research direction or stop the intervention search |
| 8–9 November | Freeze candidate; held-out/negative-control evaluation and required repeat/ablation within the fixed budget |
| 10 November | Freeze evidence and claims; recheck related work; finish the paper text and reproducibility record |
| 11 November | Review and submit the Paper Track Writeup; verify submitted status, not merely draft status |
| 12 November | Deadline buffer and final verification; no new research branch |

The main competition continues after the paper deadline. Prepare one valid main-track
submission from the best demonstrated eligible agent; the WSP adapter is optional and
must not be promoted solely to support the paper's narrative. Final main deadline is
2 December. Entry in the main track does not establish Paper Track entry.

If no weight benefit is established by 7 November, stop trying additional edits.
Complete a bounded, reproducible negative/feasibility study only if its controls and
finding support an original insight; do not present setup work as a novel method.
A positive result, a prize, and a defensible novelty claim cannot be promised.

## Budget and rules

Planning ceiling for new work through the paper deadline: **USD 25 estimated compute**,
split at most USD 10 feasibility and USD 15 confirmation/held-out work. Prefer reported
existing Modal credit; this is not a verified remaining-credit balance. The user's
EUR 100 additional compute/API ceiling still controls. Each actual CPU/GPU job needs
its own current-rate estimate, resource/runtime bounds and ledger entry before launch.
No idle deployments, automatic sweeps or separate paid teacher API calls are planned.

Use only `MODAL_PROFILE=ach-bj100`, approved base/wheels and declarative submission
interfaces. Keep inspection/orchestration outside submitted YAML. Standard PEFT
packaging must remain within official limits; the tested adapter route is already
available. Do not assume every target module or arbitrary edit is supported.
Record the editing model, licenses, accessibility and costs under the rules' external
tools provisions. Using Sol at Ultra does not make a study an Astra replication.

## Novelty and submission requirements

The 5 November review finds existing Gemma weight-edit studies, controlled numerical
weight-reading tests, and a quantized coding-agent editing lead. See [novelty](novelty.md).
Any contribution must be a specific demonstrated finding beyond those works. Recheck
at claim selection and immediately before submission; drop overlapping claims.

Official Paper Track requirements retrieved through Kaggle's read-only pages API on
5 November: a **submitted Kaggle Writeup**, at most **3,000 words**, original/unpublished
research, title/subtitle, abstract, introduction, methods/experiments, related work and
citations. Public code or a public PDF project link is optional. A draft is ineligible.
Joining the Paper Track is required. Its rubric equally scores novelty, quality,
relevance, verifiability and clarity; a replication or negative outcome does not
automatically satisfy those criteria.

Sources: [WSP article](https://rikiyat.github.io/blog/weight-space-programming/),
[Paper requirements](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/overview/submission-requirements),
[Paper evaluation](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/overview/evaluation),
[Paper timeline](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/overview/timeline),
[rules](rules-and-decisions.md). Original page cache:
`data/raw/official/paper/pages-20261105.json`, SHA-256
`c0fb77b91008bdab66b3751dcf3bae01320f100713701bb20bf5865707dce48f`.
