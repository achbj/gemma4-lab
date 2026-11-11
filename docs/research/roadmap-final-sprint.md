# Final-sprint roadmap: graph-assisted E4B agent plus forward-pass-only weight programming

Written 11 November 2026. Covers 11 November to the main final deadline, 2 December 2026 23:59 UTC (entry deadline 25 November). It supersedes the schedule in [strategy.md](strategy.md); the rules reading in [rules-and-decisions.md](rules-and-decisions.md) and the working agreement in [AGENTS.md](../../AGENTS.md) still apply. This is a plan, not a result: nothing below has been run.

## Where we start (measured)

- Control candidate `wsp-base-v1` (E4B, 8,192-token context, 3 minutes, 10 tool calls) resolves 0 to 1 of 3 qualified Rich development issues per draw. No prompt, budget or navigation change has passed a promotion gate.
- The closed-form rank-one edit shifts a synthetic behaviour (v4: mixed, one batch passes and one fails) and did not help on real issues: 0 of 3 in both arms, with the edit arm slower ([result](real-issue-check-v1-result.md)).
- No leaderboard submission has been made, so we have no official score and no reading of the small-model standings.
- The 68 reserved HTTPX/FastAPI validation issues are untouched.
- Modal credit is roughly USD 4 by the user's last report (the API does not show the balance). Metered project spend so far: about USD 5.6.

The honest reading: the prize depends mostly on the agent loop solving more issues. Weight programming is the differentiator only if it removes a failure the loop cannot.

## Constraints that shape the design (from `HARNESS_README.md`)

| Fact | Consequence |
| --- | --- |
| Submission is declarative YAML, prompts, skills and PEFT adapters. Allowed extensions: `.yaml`, `.yml`, `.md`, `.txt`, `.py` (skill scripts), `.json`, `.safetensors`. No Python entrypoint. | Graphify cannot be installed or shipped as a package: it needs tree-sitter binaries and `pip`. |
| Task sandbox is air-gapped (`network_mode="none"`), 4 GiB RAM, 2 vCPUs. | Anything used at scoring time must be stdlib-only Python inside a skill, or a built-in tool. |
| Skills may carry `.py` scripts (50 MiB per skill), exposed through `load_skill`, `load_skill_resource`, `run_skill_script`. | This is the only route for our own code at scoring time. Where `run_skill_script` executes, and whether it can read `/workspace`, is **unverified** and is the first gate. |
| Built-in graph tools exist only when the host has a pre-built graph for the repository. Test repositories differ from all public ones. | Do not depend on them. Build our own index from the workspace at run time. |
| Adapters: LoRA only, rank at most 128, 3 GiB total. Base checkpoint cannot be replaced. | Every weight edit ships as a LoRA factorisation. Already proven on Kaggle L4x4 ([adapter compatibility](adapter-compatibility.md)). |
| Budgets are ours to set in `eval_config.yaml` (defaults 60 minutes, 100 tool calls; we use 3 minutes and 10). The overall scoring-run wall limit is not in the README. | Per-task budget is an untested major lever. Find the run limit before raising it. |
| One leaderboard submission per day; two selected finals. | About 20 submissions remain. Each one must answer a question. |

## How Graphify is used

Graphify builds a code graph by deterministic tree-sitter AST parsing (no LLM for code) and answers `query`, `path` and `explain` over `graph.json`. Two uses, kept separate:

1. **Development time (real Graphify, on our machines).** Install `graphifyy` in a separate tool environment and build graphs for the development repositories. Use them to (a) check our run-time index against Graphify's nodes and edges, and (b) study which graph facts actually locate the edit for solved and failed issues. Licence is Apache-2.0/MIT; record version and usage in the provenance notes. Competition data stays local.
2. **Scoring time (our own stdlib reimplementation, `graphkit`).** A single-file skill script using only `ast`, `os`, `re`, `json`. Test repositories are Python, so `ast` gives the same structure tree-sitter would. It is not Graphify and must not be described as Graphify in the write-up; it borrows the query/path/explain interface, which we cite.

`graphkit` commands, each printing at most about 3,000 characters so E4B's context survives:

- `locate "<issue text>"`: rank symbols by overlap between issue terms (identifiers, error strings, file names) and definitions, docstrings and string literals; print the top five with file and exact line range.
- `explain <symbol>`: signature, line range, callers, callees, and the tests that reference it.
- `path <A> <B>`: shortest call/import chain.
- `tests-for <file-or-symbol>`: the narrowest pytest target.

Exact line ranges directly address the measured `start_line=1` 150-line clipping failure and the wrong-symbol selection (`add_column` for an `add_row` issue).

**Gate G0 (before writing more than a stub):** a probe submission runs a ten-line skill script through `run_skill_script` in the official image and shows it can read `/workspace` and finish in under five seconds. If it cannot, fall back to the same script delivered through `run_command` via a prompt-supplied one-line invocation; if that is also impossible, graph assistance reduces to prompt rules plus the built-in tools, and the roadmap continues without `graphkit`.

## Agent design

One base model (E4B), stages wired declaratively so the model never has to plan the workflow itself:

1. **Localise** (read-only sub-agent): `graphkit locate`, then `explain` on the top candidates; output at most three `file:start-end` targets.
2. **Reproduce**: write a failing check in `/tmp`, run it once.
3. **Edit**: read only the located ranges, make the smallest edit.
4. **Verify**: run the `tests-for` target; one bounded retry loop on failure.
5. **Submit**: `submit_patch`, with the scratch files outside `/workspace`.

Each stage is a separate comparison against the previous best, on the same panel and budget. A stage that does not add verified repairs is removed.

## Forward-pass-only weight programming

The method follows Takehi et al.'s Experiment 8: an LLM programmer reads weights, spends a fixed budget of forward passes, and writes a small edit, with no gradients. Their own limit applies to us: an edit can remove an obstacle but did not add a missing ability (their Gemma 3 270M result was null).

**Sandbox (`wsplab`), enforced rather than promised:**

- Modal function with the network blocked, model volume mounted read-only, checkpoint SHA-256 checked before and after each session.
- Model in `eval()` under `torch.inference_mode()`, all parameters `requires_grad_(False)`. A regression test fails if any module in `wsplab` references `backward`, `autograd.grad` or `torch.optim`, and a run-time assertion fails if any output tensor carries a `grad_fn`.
- Three verbs only. `read`: weight statistics and decompositions on CPU. `probe`: one batch of prompts in, logits and named activations out; each call is one forward pass and is written to a pass ledger with input hash. `write`: an edit specification (layer, module, direction, key, scale) compiled to LoRA `A`/`B` safetensors with a norm cap and rank at most 128.
- Pass budget per edit programme: 50, as in the source, fixed before the session. The session ends when the ledger is full.
- The programmer is the chat model at the effort level AGENTS.md requires for weight work. No separate paid LLM calls.

**What to edit.** Only obstacles observed in real traces, ranked by how many repairs they block, taken from the Phase 1 taxonomy. Candidates already seen: dismissing a failing test, submitting without verification, editing before reading, empty or unclosed tool calls. One target at a time.

**Controls and promotion gate.** Zero, random and sign-flipped adapters; the equivalent prompt instruction; and a gradient-trained LoRA on the same data as the conventional comparison (run outside `wsplab`, clearly labelled). An edit enters a submission only if, at temperature 0.2 with thinking, it adds verified repairs on the real development panel in two independent draws and costs no session time-outs. If the prompt or the trained LoRA does better, that is what ships, and the write-up says so.

## Fresh code layout

New subpackages inside `src/gemma4_lab/`, as AGENTS.md requires. Existing modules stay frozen as paper evidence; reuse only `weight_io`, `submission`, `modal_runtime` and the grader controls.

```text
src/gemma4_lab/arena/     Panel runner, paired comparison, trace classifier, gate checks
src/gemma4_lab/graphkit/  Stdlib index and query code; exported as one skill script
src/gemma4_lab/wsplab/    Forward-only sandbox: read, probe, write, pass ledger
submissions/graph-agent-v*/skills/graphkit/   SKILL.md and the generated script
infrastructure/modal/     arena_run.py, wsplab_session.py
tests/                    Offline tests, including the no-gradient guard
```

## Schedule

| Dates | Work | Exit condition |
| --- | --- | --- |
| 11–12 Nov | Submit the Paper Track Writeup (due 12 Nov 23:59 UTC). Submit `wsp-base-v1` unchanged to the leaderboard. Read the small-model standings and the scoring-run time limit. Skill-script probe (G0). | Official baseline score known; G0 answered. |
| 13–15 Nov | `arena`: run the control on every qualifying Requests/Rich development issue at two budgets (current, and a longer one the run limit allows). Classify every failure. | Failure taxonomy with counts; budget decision. |
| 14–19 Nov | `graphkit` and the staged agent, one stage per paired comparison. Graphify cross-check of the index. | A candidate that beats the control on the development panel in two draws. |
| 16–23 Nov | `wsplab`: build the sandbox, then one edit programme against the top-ranked obstacle, with all controls. At most one revision. | Edit passes or fails the promotion gate. Stop either way. |
| 24–27 Nov | Freeze the best agent. Run it once on the 68 reserved issues against the control. Daily leaderboard submissions of frozen candidates only. | Held-out paired result. |
| 28 Nov–1 Dec | Clean end-to-end packaging from a fresh checkout, licence and provenance notes, final novelty recheck. | Two candidates verified in the official image. |
| 2 Dec | Select finals: A, the best agent without an adapter; B, the same agent with the edit if it passed its gate, otherwise the second-best agent variant. | Selection confirmed on Kaggle before 23:59 UTC. |

## Budget

Estimates from the A10G rate card in `configs/`, to be re-priced in the ledger before each run. All within the EUR 100 ceiling and beyond the remaining credit, so each line needs the user's approval before launch.

| Item | Bound |
| --- | ---: |
| Baseline panel and taxonomy | USD 12 |
| Graph agent comparisons | USD 20 |
| Weight programme and controls | USD 20 |
| Reserved validation | USD 12 |
| Reserve for reruns | USD 10 |

Kaggle's free GPU quota is used for official-image checks and is not counted here.

## Rule points to settle before relying on them

- Whether skill scripts execute at scoring time, and where (G0).
- The scoring-run wall limit, which bounds per-task minutes.
- The open question in [strategy.md](strategy.md) on LLM-designed adapter weights; ask it on the forum before an edited adapter becomes a final selection.
- Graphify licence and attribution for any interface or code we borrow.

## Sources

- Graphify: <https://github.com/Graphify-Labs/graphify> (README on `main` and the `v8` default branch, read 11 November 2026; the two differ in details and the canonical owner of the install script was not verified).
- Takehi, Teoh, Zhang, Khattab, "Sparks of Weight-Space Programming", 2 November 2026: <https://rikiyat.github.io/blog/weight-space-programming/>.
- `data/raw/official/competition/HARNESS_README.md` (local copy, hashes in `official-assets.json`).
