# Paper I v2 projection repair

Base: `065d707050e46f66326d2da8806e7e542cdb590a`.

The v1 projection benchmark is not suitable as flagship evidence: `transition_type` contains `family_id` and is exposed to every comparator; after stripping that label, identical substantive states can require conflicting gold actions. V2 separates an explicit transition request from the governance decision, removes family identity from candidate-visible state, requires gold to be a function of substantive state plus request, separates invariance tests from decision twins, removes duplicate evidence twins, and adds a stronger ATMS+provenance+revision parent.

A locally executed 28-case/14-family v2 panel has zero contradictory substantive-state+request pairs. A 10-coordinate registered authority basis is sufficient and each coordinate is individually necessary by a decision twin. Representation upper bounds are 0.5714 for the simple controls, 0.6786 for the stronger ATMS+PROV+revision abstraction, and 1.0 for typed authority. Targeted standalone tests: 4 passed. This is development representational evidence only; behavioural and natural-domain gates remain open.
