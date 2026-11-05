# Rules and experiment decisions

Main rules reviewed 4 November 2026. Paper requirements/rules rechecked 5 November through Kaggle's authenticated read-only pages API after web rendering returned no readable content. This is our working interpretation; organizer decisions control eligibility.

## Sources and precedence

- [Main rules](https://www.kaggle.com/competitions/gemma-4-developer-agent/rules): competition-specific sections 2.2, 2.4–2.6, 2.8, and the foundational rules. The page states that foundational rules control conflicting competition-specific terms.
- [Paper rules](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper/rules) and [paper rubric](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper): original work, research reporting, submission requirements, and judging.
- [Model update from staff](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287), downloaded `HARNESS_README.md`, and the official starter: concrete model and execution requirements.

## Current decisions

| Decision | Support and restriction | Application |
| --- | --- | --- |
| E4B baseline | Staff and harness explicitly permit the selected quantized E4B variant; all agents share a variant. | Root and analyzer use the same approved checkpoint. |
| Submission format | Harness accepts declarative agent configuration and supported PEFT adapters. | Our Python orchestration stays outside the submitted agent. Use registered tools and sandboxed skill mechanisms. |
| External development tools | Main and paper section 2.6 permit external models/tools, subject to host restrictions and reasonable accessibility/cost. | Record licenses, availability, usage, and costs. This general permission is not a specific endorsement of a proposed weight-editing technique. |
| Data and code | Rules restrict private sharing and redistribution; public competition-code sharing goes through Kaggle. | Private account-controlled development only. Keep raw data out of Git; do not publish or send competition data outside the permitted scope. |
| Prize reproducibility | Rules require appropriate licensing and delivery of reproducible winning code/documentation. | Pin sources and runtime artifacts, preserve experiments and exact outputs, and record external resources. |

Main-track limits are one daily submission and two selected finals. Paper-track limits are five daily submissions and two selected finals. Entry and submission are separate for the two tracks; joining the main track does not prove paper-track entry.

## Paper submission check, 5 November

- Deadline: 12 November 2026, 23:59 UTC; internal target 11 November.
- Required: join the separate Paper Track and submit a Kaggle Writeup reporting original, unpublished research, maximum 3,000 words. Include title/subtitle, abstract, introduction, methods/experiments, related work and citations. Draft or unsubmitted Writeups are ineligible. Public code/notebook or public PDF project links are optional.
- Evaluation equally weights novelty, quality, relevance, verifiability and clarity. A replication, a deployment check or an inconclusive negative result does not automatically establish an original contribution.
- The account's entered-competition check confirms main entry but does not confirm paper entry; manual confirmation is pending. No paper or public notebook has been submitted.
- Source cache: ignored `data/raw/official/paper/pages-20261105.json`, retrieved with `competition_list_pages`, SHA-256 `c0fb77b91008bdab66b3751dcf3bae01320f100713701bb20bf5865707dce48f`. Entry check: `artifacts/runtime-validation/paper-track-entry-check-20261105.json`.
- 6 November read-only recheck: `artifacts/runtime-validation/paper-track-entry-recheck-20261106.json` lists the main competition but does not confirm separate Paper Track entry. The listing may omit Writeup tracks, so it is not proof of non-entry. Manual confirmation remains pending; no account or submission change was made.

## Baseline decision record

- Change: execute the existing E4B reference candidate remotely, without adapting weights or tuning its supplied settings.
- Control: validate with the official compiler first; separate compiler validation, model/tool-call smoke tests, and actual issue resolution in reporting.
- Cost: one bounded L4 allocation, at most USD 2 estimated initial usage. Record image-build and data-staging costs separately.
- Environment: a Modal development runtime is not proof of parity with the Kaggle scorer. Preserve official package/checkpoint versions and document hardware differences.
- Data boundary: the agent receives the issue, allowed hints, and repository; evaluation-only reference/test patches are not agent input.
- Open point for later edits: the low-rank update must fit supported adapter modules/limits and be accepted by the scorer. A directly rewritten base checkpoint is outside this baseline plan.

## Choosing the strongest permitted approach

For each intervention, record its rule support, hypothesis, fixed development/validation split, resources, comparison, and result. Compare simpler prompt/workflow controls before attributing gains to weight edits. Select on held-out validated repairs under a matched time budget, including deployment failures and regressions. A limited experiment identifies the best measured candidate, not a globally optimal solution.

Recheck host announcements before a materially different experiment and before final submission. Review paper novelty separately in [the novelty register](novelty.md).
