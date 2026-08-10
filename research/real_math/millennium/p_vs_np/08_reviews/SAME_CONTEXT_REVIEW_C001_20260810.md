# Nature-style review preflight — C001

**Independence status:** SAME_CONTEXT_ONLY. These three lenses were produced in the same research invocation and therefore do **not** satisfy the three-isolated-review promotion gate. They are a preflight modeled on `nature-reviewer`, not independent peer review.

## Review setup

- **Input scope** C001 proof draft plus P-vs-NP problem contract and barrier map.
- **Assessment boundary** logical validity, barrier relevance, and novelty risk of the intermediate CLIQUE transfer lemma only.
- **Shared claim summary** a De Morgan circuit for `CLIQUE_{n,k}` with `t` distinct complemented edge variables restricts to a monotone CLIQUE circuit on a vertex subset of size at least about `n^2/(2t+n)`.
- **Visible evidence base** proof draft and standard independent-set inequality. No bound from the monotone CLIQUE literature has yet been imported.
- **Missing materials affecting confidence** theorem-prover artifact, primary-source novelty search, exact parent theorem/circuit conventions, isolated reviews.

# Reviewer 1 — logical soundness lens

## Overall assessment

The restriction argument is short and appears logically sound under the stated De Morgan model. The most important risk is specification drift when this lemma is combined with a literature lower bound using different gate, constant, or parameter conventions.

## Major strengths

The proof has an explicit restriction, explains why complemented literals disappear, and checks that the target becomes exactly a smaller CLIQUE instance rather than merely a related monotone function.

## Major Concerns

### R1-M1

- **Severity** Major
- **Blocking** Yes for promotion, No for retaining as a proof draft
- **Axis** technical soundness / specification
- **Claim pointer** Definitions and Claim C001
- **Evidence pointer** C001 proof draft
- **Concern** The legal parameter range for `CLIQUE_{n,k}` should be frozen explicitly, for example `2 <= k <= n`, and the monotone parent theorem must use compatible size and constant conventions.
- **Why it matters** A later quantitative corollary can be false or misstated if its parent theorem counts literals, constants, fan-in, or gates differently.
- **Resolution test** Freeze parameter and circuit conventions, then bind every imported monotone lower bound to those conventions or prove the conversion overhead.

## Minor Comments

None that affect the mathematical core.

## Recommendation posture

Retain as a useful intermediate lemma. Do not promote above proof draft before exact source/convention binding and formalization.

# Reviewer 2 — complexity/barrier lens

## Overall assessment

C001 correctly isolates one restricted negation parameter but does not come close to general circuits by itself. That limitation is clearly acknowledged and should remain prominent.

## Major strengths

The lemma converts an informal obstruction into an explicit residual. Dense negative-literal access is now a measurable blocker rather than a vague statement that monotone methods do not handle negation.

## Major Concerns

### R2-M1

- **Severity** Major
- **Blocking** Yes for any root-level implication
- **Axis** complexity/barrier audit
- **Claim pointer** What C001 does not buy
- **Evidence pointer** C001 proof draft
- **Concern** The number `t` of distinct complemented input variables after De Morgan normalization is not controlled by the number of internal NOT gates in an arbitrary circuit. A circuit with little syntactic negation can still induce negative dependence on many inputs after normalization.
- **Why it matters** Treating C001 as a lower bound for circuits with few NOT gates would be an invalid strengthening and could create a false route toward P versus NP.
- **Resolution test** Keep C001 explicitly parameterized by complemented input variables, or prove a separate theorem relating the chosen general-circuit parameter to `t` for a nontrivial circuit class.

### R2-M2

- **Severity** Major
- **Blocking** Yes for root progress
- **Axis** barrier relevance
- **Claim pointer** residual following C001
- **Evidence pointer** P-vs-NP barrier map
- **Concern** When `t` is dense in the edge set, the independent-set guarantee can collapse to constant size. The current method therefore inherits monotone lower bounds only in a restricted regime.
- **Why it matters** This is the actual gap to general circuits.
- **Resolution test** Produce a new structural parameter or cancellation theorem that remains informative when complemented-variable access is dense, then verify it against small exact counterexamples before asymptotic proof search.

## Recommendation posture

Good route-sharpening lemma. No P-vs-NP authority.

# Reviewer 3 — novelty and value lens

## Overall assessment

The proof is elementary enough that rediscovery risk is high. Its current value is architectural and diagnostic, not a defensible novelty claim.

## Major strengths

It gives the research program a clean quantitative bridge and a precise next question. That is useful even if the lemma is known.

## Major Concerns

### R3-M1

- **Severity** Major
- **Blocking** Yes for novelty promotion
- **Axis** originality
- **Claim pointer** Claim C001
- **Evidence pointer** no primary-literature novelty packet yet
- **Concern** Lower bounds for monotone CLIQUE under limited negation/complemented-variable resources have a substantial literature. The exact statement may already be known, may follow immediately from a stronger theorem, or may be standard folklore.
- **Why it matters** Machine or informal proof validity cannot mint a new-mathematics claim.
- **Resolution test** Search primary literature using exact, normalized, and structural formulations, including stronger parent theorems for circuits with few negations or limited negative literals. Classify C001 as rediscovery if an equivalent/stronger theorem is found.

## Recommendation posture

Treat as `NOVELTY_UNRESOLVED`. Its strongest current role is a verified-discovery checkpoint and residual generator.

# Cross-review synthesis

## Consensus strengths

The restriction logic is coherent, the theorem is appropriately scoped, and the main value is that it identifies a concrete negation/cancellation residual.

## Consensus blocking concerns

1. Exact circuit and parameter conventions must be bound before importing monotone lower bounds.
2. C001 does not control dense negative-literal access or arbitrary general circuits.
3. Novelty is completely unresolved until primary literature is searched.

## Most important next step

Search for a structural replacement for raw `t` that survives dense complemented-variable access. Candidate parameters must be counterexample-tested before any proof narrative is expanded.

## Risk / unsupported claims

- No claim that C001 is new is supported.
- No claim that C001 yields a superpolynomial general-circuit lower bound is supported.
- No independent reviewer gate has been satisfied by this preflight.
