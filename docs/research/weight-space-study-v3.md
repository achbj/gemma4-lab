# Weight-space study v3 — pre-registration

Drafted 8 November 2026 (UTC) after the [v2 primary gate failed](wsp-v2-panel-result.md) and
its post-hoc diagnostic on the 24 v2 evaluation prompts. Approved by the user on 8 November
as a second revision beyond the v1/v2 revision limits. **v3 is a new experiment, not a rescue
of v2:** v2's outcome stays a recorded negative. Paper deadline 12 November 23:59 UTC
(internal submit 11 November); the main competition (final 2 December) is independent.

## What v3 changes, and what it keeps

The v2 diagnostic found the edit's key fires, its direction is right and the effect is monotone
in strength, but α = 1 recovers only ~6% of the prompt's margin. v3 therefore changes **one
thing**: the strength α, chosen by a frozen rule from *design cases only*. Everything else is
the v2 construction, unchanged and reused byte-for-byte: layer 29 `o_proj`, key `k*`, shift `d`,
background covariance and ridge (`weight-space-study-v2.md`, capture
`/cache/wsp-v2/capture-v1.safetensors`, SHA-256 `786e7295…3271`), rank-1 inside rank-8/alpha-8
PEFT, same random and sign-flipped control construction. No new capture, no new layer, no
new direction.

## Selection of α (design cases only, before any v3 panel inference)

Dense Transformers simulation of the edit at all positions (as in the v2 diagnostic), base
prompt, greedy 64-token continuation, on the **v2 design cases** (never evaluated):
12 prefix-corruption and 12 non-target (6 failing-assertion, 6 passing-control).
Frozen grid: α ∈ {2, 3, 4, 6, 8}. Choose the **smallest** α satisfying both:

1. greedy first tool call is `read_file` in ≥ 11 of the 12 design prefix cases;
2. the greedy first tool call name is unchanged from α = 0 in all 12 non-target design cases.

If no α satisfies both, **v3 is aborted** and no panel is run; the paper reports the failed
selection. α is not tuned, extended or re-gridded after seeing the selection result.

## Fresh evaluation panel

36 new cases (24 prefix-corruption target, 6 failing-assertion, 6 passing-control), from a
seeded generator with label `wsp-v3-cases`, disjoint from every coefficient pair in
`behavior-diagnostic-v1/v2` and `wsp-v2-cases` (all 60 v2 pairs, design and evaluation).
No v2 evaluation case is reused. Same protocol as v2: six actions, 60 seconds, 1,536 tokens,
temperature 0, seed 20261105, wsp-base-v1 prompt (edit-integrity prompt only in the prompt arm).

**Arms (6 × 36 = 216 trajectories):** base; zero adapter; random adapter (seeded, norm-matched);
**A** (selected α); **A−** (sign-flipped, same norm); prompt (edit-integrity, no adapter). Arm
order rotates left by case index. No base-repeat arm: v2's base and repeat agreed on all 36 cases.

## Gates (identical in form to v2, minus the repeat comparator)

Primary success requires all of:
1. All 216 trajectories valid; A completes all 6 passing controls; application check passes
   (zero-control drift ≤ 0.05 nats, A/A−/random log-probability shifts above threshold).
2. On the 24 target cases, A beats each of base, zero and random with ≥ 6 net paired workflow
   wins and one-sided exact sign-test p < 0.05 for each.
3. A's net advantage over A− is ≥ 4 target cases.
4. A has ≤ 1 paired loss to base on the 12 non-target cases.

Secondary, reported but not gating: first-action reread counts, A versus the prompt arm,
target completions per arm. Pass → report a deployment-constrained, design-selected keyed
rank-one edit with its limits (one synthetic behaviour, single draw); only then, under a new
ledger entry, one paired development-panel check on real Rich issues. Fail → close the weight
branch; v1, v2 and v3 are reported together as a controlled negative result. **No further
revision, α change, layer change or panel is permitted.**

## Prior work, claims and limits

Unchanged from v2: the algebra is ROME's keyed rank-one update with activation-derived keys and
values; steering, context distillation and the weight-space-programming article are prior work
([novelty.md](novelty.md)). Any claim is limited to what the controls show here. Selection on
design cases and testing on fresh cases limits, but does not remove, researcher degrees of
freedom: the v2 diagnostic motivated the strength range. Both facts are stated in the paper.
The numerical-access question (weights visible versus hidden) remains untested.

## Budget and schedule (UTC)

Workspace `onepiecification` only. Selection ≈ USD 0.20, CPU packaging ≈ USD 0.10, panel ≈
USD 1.00, optional real-task check ≈ USD 2.80; v3 cap **USD 3.50 without the real-task check,
USD 6.50 with it**, inside the EUR 100 ceiling (spent so far about USD 1.7 estimated; workspace
credit still unverified). Each job gets its own current-rate ledger entry first. 8 Nov: freeze,
generate cases, run selection. 9 Nov: package, run panel, record gate. 10 Nov: freeze evidence,
final novelty recheck, finish paper. 11 Nov: submit and verify status. Paper Track entry still
needs the user's manual confirmation.
