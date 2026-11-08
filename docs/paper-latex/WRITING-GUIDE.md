# How to make this paper good (and yours)

Deadline: Kaggle Paper Track Writeup, **12 Nov 2026 23:59 UTC**; aim to submit on **11 Nov**. A draft or unsubmitted Writeup is ineligible. Limit: 3,000 words. Required by the page (see `docs/research/rules-and-decisions.md`): title/subtitle, abstract, introduction, methods/experiments, related work, citations. Public code or a public PDF link is optional.

**Format.** The Writeup itself is entered in Kaggle's editor, not uploaded as LaTeX. Use `main.tex` for writing and for a clean PDF; paste the final text (headings, tables as Markdown, equation as image or plain text) into the Kaggle Writeup, and optionally link the PDF if you host it publicly.

## Order of work (about 6 hours)

1. **Read the numbers first (45 min).** `docs/research/wsp-v3-panel-result.md`, `wsp-v3-distill-result.md`, `wsp-v3-seeds-result.md`, `wsp-v4-result.md`. If you cannot state each result in one sentence, you cannot write the paper.
2. **Write the one-sentence paper.** "A closed-form rank-one edit installs a prompt behaviour in a quantized Gemma 4 E4B through a standard adapter; it works under greedy decoding, is comparable to a trained LoRA, and is only partly reliable at the competition's sampling setting." Every section must serve that sentence.
3. **Rewrite the Introduction (1 h).** Your voice, your motivation. Keep the contribution list to three items and make it match Related Work exactly.
4. **Read the three unread references (1.5 h).** Steer2Edit, Mazzawi et al., Yin et al. (full texts). For each write one line: what it does, how ours differs. If one covers a contribution, drop that contribution. Fix author names in `references.bib`.
5. **Rewrite Method for a stranger (45 min).** Have someone unfamiliar read it; if they cannot say what $\Delta W k^\ast = \alpha d$ means, add a sentence.
6. **Add a worked example (30 min)** from a real row, or delete the subsection.
7. **Write Conclusion (15 min).**
8. **Cut to under 3,000 words (30 min)** counting everything; drop the Reproducibility incident list before dropping any limitation.
9. **Final checks (30 min)** below, then submit on Kaggle.

## What makes it read as a good paper

- Lead with what is solid (greedy result with controls, preserved failures) and say plainly what is not (sampling, no real repairs).
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
| Cost about USD 11 | `docs/operations/run-log.md` |

## Pre-submission checklist

- [ ] Name, affiliation, date filled in; every red `YOU:` marker gone.
- [ ] `\guidefalse` set (or all blue GUIDE boxes deleted) and `make` produces no warnings.
- [ ] Word count of the Kaggle text under 3,000.
- [ ] Full texts of references 3-5 read; author names fixed.
- [ ] Novelty search re-run on 10-11 Nov (`docs/research/novelty.md`).
- [ ] Decision made on public code link (repository is private; nothing published).
- [ ] No claim of real-repair benefit, robustness, or superiority over the prompt.
- [ ] Writeup **submitted** (not saved as draft) and the Paper Track entry confirmed on the competition page.
