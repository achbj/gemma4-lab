# How to make this paper good (and yours)

Deadline: Kaggle Paper Track Writeup, **12 Nov 2026 23:59 UTC**; aim to submit on **11 Nov**. A draft or unsubmitted Writeup is ineligible. Limit: 3,000 words. Required by the page (see `docs/research/rules-and-decisions.md`): title/subtitle, abstract, introduction, methods/experiments, related work, citations. Public code or a public PDF link is optional.

**Format.** The Writeup itself is entered in Kaggle's editor, not uploaded as LaTeX. Use `main.tex` for writing and for a clean PDF; paste the final text (headings, tables as Markdown, equation as image or plain text) into the Kaggle Writeup, and optionally link the PDF if you host it publicly.

## State on 10 November

`main.tex` is a complete draft: about 2,400 words, 6 pages, builds with no warnings. The only markers left are your name and affiliation. Everything below is for your own editing pass.

## Order of work (about 2 hours)

1. **Read the numbers first (30 min).** `docs/research/wsp-v3-panel-result.md`, `wsp-v3-distill-result.md`, `wsp-v3-seeds-result.md`, `wsp-v4-result.md`, `real-issue-check-v1-result.md`. If you cannot state each result in one sentence, do not submit yet.
2. **Check the one-sentence paper.** "A closed-form rank-one edit installs a prompt behaviour in a quantized Gemma 4 E4B through a standard adapter; it works under greedy decoding, is comparable to a trained LoRA, is only partly reliable at the competition's sampling setting, and did not help on three real issues." Every section must serve that sentence.
3. **Edit the Introduction into your own voice (30 min).** Keep the three contributions as they are; they match Related Work.
4. **Skim the related papers yourself (30 min).** Steer2Edit and Mazzawi et al. were read in full text except the last part of each page; Yin et al. only as the abstract (the PDF body could not be extracted). The Related Work sentence on Yin et al. says no more than the abstract does. Keep it that way unless you read the paper.
5. **Paste into Kaggle and submit (30 min)**, then run the checklist below.

## What makes it read as a good paper

- Lead with what is solid (greedy result with controls, preserved failures) and say plainly what is not (sampling, and no repair on three real issues where the edit arm also ran slower).
- Numbers in tables, one claim per sentence, no adjectives like "robust", "significant" (unless the protocol pre-registered the test), "novel".
- Say "comparable to a gradient LoRA" not "matches or beats". Say "mixed" for v4.
- The strongest honest framing: **a controlled deployment study with preserved failures**. Do not oversell as a new method; the related work covers the algebra.
- Prefer one clean figure (included) to many tables.

## Facts you must not change without re-checking the source

| Claim | Source |
| --- | --- |
| Greedy: edit 21 and 23 of 24, base 5 and 4, sign-flipped 0, prompt 24, LoRA 24 | `wsp-v3-panel-result.md`, `wsp-v3-distill-result.md` |
| T=0.7: seed 101 pass, 103 fail (empty completions), 102 incomplete | `wsp-v3-seeds-result.md` |
| T=0.2 + thinking: A 15/3, B 10/6 (edit/base) | `wsp-v4-result.md` |
| Real issues: base 0 of 3, edit 0 of 3, edit hit the session limit twice; earlier base draw 1 of 3 | `real-issue-check-v1-result.md` |
| Cost under USD 6 metered in total (4.85 + 0.70) | `docs/operations/run-log.md`, 10 Nov entries |

## Pre-submission checklist

- [ ] Name and affiliation filled in; every red `YOU:` marker gone; `make` produces no warnings.
- [ ] Word count of the Kaggle text under 3,000.
- [x] Author names fixed in `references.bib`. Full-text reading status is in step 4 above.
- [ ] Novelty search re-run on 10-11 Nov (`docs/research/novelty.md`).
- [ ] Decision made on public code link (repository is private; nothing published).
- [ ] No claim of real-repair benefit, robustness, or superiority over the prompt.
- [ ] Writeup **submitted** (not saved as draft) and the Paper Track entry confirmed on the competition page.
