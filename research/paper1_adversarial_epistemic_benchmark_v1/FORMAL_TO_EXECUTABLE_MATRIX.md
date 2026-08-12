# Paper I formal-to-executable matrix (#489)

The projection-sufficiency benchmark is a deterministic companion to the existing authority-leakage panels. It asks whether a state abstraction contains enough information for a correct update policy to exist on the registered minimal twins.

| Paper I distinction | Twin family / executable coordinate | Weak projection attacked |
|---|---|---|
| computational access is not authority | F08 workspace-only; F09 experience-only | text memory, transactional state |
| provenance is not evidential authority | F02 indirect vs direct support | provenance-only |
| pairwise compatibility is not global gluing | F03 `global_gluing` with pairwise compatibility fixed true | pairwise-only |
| context/regime is first-class | F04 `context_match` | text/scalar/provenance/transactional |
| independent roots are not root count | F05 `evidence_independence` | text/scalar/pairwise/vote/transactional |
| prediction is not mechanism | F06 `mechanism_support` with predictive summary fixed | scalar/text/provenance/transactional |
| mechanism is not identification | F07 `identification_support` | all weak projections |
| supersession/revocation must remain possible | F10, F15 | text/scalar/pairwise/vote/provenance |
| theorem truth is not novelty | F11 `novelty_checked` | scalar/text/provenance/transactional |
| unknown evidence must remain `CANNOT_CHECK` | F12 `cannot_check` | scalar aggregation and other weak projections |
| negative history is durable state | F13 `negative_history_retained` | weak projections |
| fail-closed cannot mean blanket refusal | F14 legitimate promotion + F15 legitimate supersession | every architecture/policy |

## Impossibility lemma exercised by the benchmark

For a canonical state space `S`, projection `pi`, and required update map `a*`, if there exist `x,y` such that `pi(x)=pi(y)` but `a*(x) != a*(y)`, then no deterministic policy `f(pi(s))` can be correct on both `x` and `y`. The benchmark reports these collisions and the resulting Bayes/identifiability upper bound for each frozen state abstraction.

The result is representational. It does not claim that omitted facts cannot be inferred from unrestricted external observations or natural-language reasoning.
