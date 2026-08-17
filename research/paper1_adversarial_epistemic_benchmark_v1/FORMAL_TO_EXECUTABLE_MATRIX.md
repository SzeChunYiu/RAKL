# Paper I formal-to-executable matrix (#489)

The current projection-sufficiency benchmark is the repaired v2 instrument in `src/rakl/epistemic_projection_benchmark_v2.py`. It asks whether a state abstraction contains enough information for a correct update policy to exist on the registered minimal cases. Historical v1 artifacts remain preserved as negative history and are not cited as evidence.

| Paper I distinction | v2 executable cases / coordinate | Weak projection attacked |
|---|---|---|
| repeated access is not evidential authority | `I01_LOW_RETRIEVAL`, `I01_HIGH_RETRIEVAL`; `evidence_support` held at `NONE` | text memory |
| computational workspace is not authority | `I08_CANONICAL`, `I08_WORKSPACE`; `workspace_only` | text memory, transactional state |
| experience success is not evidence authority | `I09_CANONICAL`, `I09_EXPERIENCE`; `experience_only` | text memory, transactional state |
| stale retrieval cannot reactivate a superseded claim | `I10_STALE_ONCE`, `I10_STALE_REPEATED`; `superseded` fixed true | text/scalar/pairwise/vote/provenance |
| provenance is not evidential strength | `D02_WEAK`, `D02_DIRECT`; `evidence_support` | provenance-only |
| pairwise compatibility is not global gluing | `D03_LOCAL_ONLY`, `D03_GLOBAL`; `global_gluing` | pairwise-only |
| context/regime is first-class | `D04_MISMATCH`, `D04_MATCH`; `context_match` | text/scalar/provenance/transactional |
| independent roots are not root count | `D05_CORRELATED`, `D05_INDEPENDENT`; `evidence_independence` | text/scalar/pairwise/vote/transactional |
| prediction is not mechanism | `D06_PREDICTION_ONLY`, `D06_MECHANISM`; `mechanism_support` | scalar/text/provenance/transactional and the generic strong parent |
| mechanism is not identification | `D07_NONIDENTIFYING`, `D07_IDENTIFYING`; `identification_support` | weak projections and the generic strong parent |
| theorem truth is not novelty | `D11_UNCHECKED_NOVELTY`, `D11_CHECKED_NOVELTY`; `novelty_checked` | scalar/text/provenance/transactional and the generic strong parent |
| unknown evidence remains `CANNOT_CHECK` | `D12_UNKNOWN`, `D12_RESOLVED`; `cannot_check` | scalar aggregation and other weak projections |
| negative history is durable state | `D13_HISTORY_DROPPED`, `D13_HISTORY_RETAINED`; `negative_history_retained` | weak projections |
| legitimate supersession must remain possible | `D15_NO_SUPERSEDING_EVIDENCE`, `D15_SUPERSEDING_EVIDENCE`; `superseding_evidence` | every architecture that omits the coordinate |

The v2 `TransitionRequest` is candidate-visible and is separate from `GovernanceDecision`; family and case identifiers are not candidate-visible. `assert_gold_is_state_function()` rejects conflicting gold for an identical substantive state plus request, and `assert_no_family_label_visibility()` rejects answer-semantic labels in any frozen projection.

## Impossibility lemma exercised by the benchmark

For a canonical state space `S`, projection `pi`, and required update map `a*`, if there exist `x,y` such that `pi(x)=pi(y)` but `a*(x) != a*(y)`, then no deterministic policy `f(pi(s))` can be correct on both `x` and `y`. The benchmark reports these collisions and the resulting identifiability upper bound for each frozen state abstraction.

On the repaired 28-case / 14-family development panel, the simple comparator projections have identifiable upper bound `16/28 = 0.5714`; the stronger `ATMS_PROV_REVISION` projection rises to `19/28 = 0.6786`; `RAKL_TYPED_AUTHORITY` separates all registered states (`28/28`, zero ambiguous projected states). The registered ten-coordinate authority basis is sufficient and each coordinate is individually necessary on its paired witness in this panel.

## Claim boundary

This is a constructed representational result. It does **not** establish that arbitrary ATMS, W3C-PROV, belief-revision, argumentation, rule-engine, or unrestricted language-reasoning systems cannot be extended with the missing scientific-authority semantics. Behavioural generated-payload assurance and natural-domain construct validity remain separate evidence coordinates.
