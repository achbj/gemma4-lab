# First task-directed weight-space screen

5 November 2026. **The fixed edit failed its behavioral gate.** It was applied correctly
but completed 9/12 synthetic workflows, versus 10/12 for the base and random control
and 12/12 for the prompt control. Do not promote this adapter or spend real-task
evaluation compute on it. This is a failed specific hypothesis, not a refutation of
the published weight-space programming demonstrations.

## What we actually tried

After the user confirmed Ultra, inspect learned numerical values from the approved
E4B version-2 quantized checkpoint. Verify all eight source-file hashes, then decode
two attention projections with the pinned official INT4/group-32 implementation:
the final layer-41 output projection and its shared layer-23 value projection.
Inspect the relevant learned norm/scalar gains and token-embedding rows for `error`,
`ok`, `read_file` and `edit_file`. The independent decoder/transport fixture passed
exactly; scales are promoted to FP32 before dequantization.

The frozen heuristic maps mean label embeddings through the source input norm,
value projection, per-head value norm and grouped-query expansion. Remove the
`ok`-prototype component from the `error` prototype and normalize to obtain input
direction `a`. Construct output direction `b` from the `read_file - edit_file`
embedding difference, adjusted by the actual post-attention/final norm gains and
final scalar sign. Form `delta_W = beta * b @ a.T`, with beta fixed before inference
at 1% of the decoded output projection's Frobenius norm. Encode this rank-one change
inside the already-tested rank-8/alpha-8 standard PEFT route; seven components stay zero.

The observed output-projection norm was 48.421669 and beta 0.48421669. Error/ok
prototype cosine was 0.141617, below the frozen 0.95 degeneracy threshold. Stored
BF16 delta norm was 0.48413002, or 0.00999821 relative to base. The seeded random
control matched the semantic delta norm within 0.009261%; the zero control shared
its A factor and had exactly zero B.

These are **static token prototypes, not actual deep-layer hidden states**. Their
algebraic separation does not establish error detection or a causal weight defect.
The editor knew architecture, label meanings and prior development traces. This is
task-informed construction from inspected weights, with no gradients or full-model
forward passes during construction. It is neither blind task identification nor
from-scratch game-network construction, and is not an exact Astra replication.

## Frozen controls and result

[Settings](../../configs/wsp-screen-v1.json) preserve the 12 already-inspected synthetic
development cases, native editing tool and restricted arithmetic checker. All five
conditions share six actions, 60 seconds per case, 1,536 output tokens, temperature
zero and a fixed seed. Rotate condition order per case. The prompt arm uses the
preserved reread/full-line instructions; other arms share the base prompt. These
synthetic settings are separate from the shared 8,192-token full-agent configuration.

| Condition | Completed correct workflows | Passing controls | First source reads on 3 prefix cases |
| --- | ---: | ---: | ---: |
| Base | 10/12 | 3/3 | 0/3 |
| Zero edit | 10/12 | 3/3 | 0/3 |
| Proposed weight edit | 9/12 | 3/3 | 0/3 |
| Matched random edit | 10/12 | 3/3 | 0/3 |
| Prompt control | 12/12 | 3/3 | 3/3 |

All 60 trajectories completed and were valid for comparison. Base/zero actions,
final sources and workflow outcomes matched exactly. The proposed edit had zero
paired workflow wins and one loss versus base, and one fewer completed workflow
than random. No condition submitted prematurely. Source correctness and workflow
completion counts agree in this run.

In `prefix-fresh-03`, the proposed edit alternated failed replacement and successful
reread three times, then exhausted its six-action allowance. It retained the malformed
line. Base/zero/random read the changed source on their third action, replaced the
complete observed line, checked it and submitted. Thus the proposed arm did reread;
it failed to use the observed source to correct its replacement. No first-action
reread improvement or useful recovery gain followed from the construction.

Application is measured separately: 24 repeated one-token requests across three fixed
prefixes showed zero measured control drift. Proposed-edit log-probability distance
lower bounds were 0.159433, 0.241985 and 0.140605 nats, all above 0.001. Random effects
also cleared the threshold. All three compiled adapter routes resolved correctly and
returned READY. This rules out an unapplied adapter for these measurements; token
effects do not establish the intended semantic mechanism.

## Provenance, cost and limits

- Numerical report: `artifacts/wsp-numeric-v1/20261105T183157Z/inspection.json`.
- Native CPU package/compiler report: `artifacts/wsp-read-v1/20261105T184707Z/prepare.json`.
- Full GPU report: `artifacts/wsp-screen-v1/20261105T185216Z/run.json`, source commit
  `c44583f`, image `im-bEtC1IFnE2DCntpbAu56LW`, NVIDIA A10, Python 3.12.
- GPU app `ap-C3xGGWRhPzGwzorgBKIMOl`: 243.197 seconds to readiness, 352.621 seconds total.
  Raw requests/responses, native editing histories, source states and server log are retained.
- One GPU job, no sweep/retry, with USD 1.20 estimate reserve; numerical and preparation
  CPU reserves were separately recorded. See the [run ledger](../operations/run-log.md)
  for rules, rate snapshots, requested-compute bounds and workspace billing qualifications.

This is one heuristic, one checkpoint, one random direction and one deterministic draw
on tiny inspected templates. It cannot estimate general repair accuracy or establish
that weight-space programming broadly succeeds or fails. No reserved issue was accessed.
The failed gate blocks real-repair evaluation of this candidate. At most one documented
revision remains available under the [study protocol](weight-space-study-v1.md), with
fresh controls and a new allocation before execution; none is selected here.

The [published WSP method](https://rikiyat.github.io/blog/weight-space-programming/)
and [rank-one model editing](https://arxiv.org/abs/2202.05262) are prior work. This
feasibility result does not establish an original mechanism or a prize-ready paper.
The [novelty register](novelty.md) remains provisional and needs claim-time and
pre-submission review.
