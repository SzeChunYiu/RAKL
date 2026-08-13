# Primary-source / nearest-parent ledger used by the integration audit

This is a bounded routing ledger, not a complete bibliography.

| Source / family | Why it matters to RAKL | Integration consequence |
|---|---|---|
| RFC 8785 — JSON Canonicalization Scheme | canonical crypto serialization; preserves parsed Unicode strings rather than normalizing them | RAKL NFC behavior must be explicit/versioned and not mislabeled JCS |
| Python `decimal` documentation | `normalize()` applies context rounding before simplification | never use ambient-context Decimal normalization for integrity commitments |
| SLSA provenance v1.2 | artifact digest + how/where produced are supply-chain evidence | prefer SLSA-compatible build provenance for release-bearing artifacts |
| Conditional Similarity Networks | condition-specific similarity/embedding subspaces | task-conditioned geometry alone is not RAKL novelty |
| relational bottleneck / Abstractor family | explicit relational computation | relational structure alone is not RAKL novelty; use as parent |
| causal abstraction / interchange-intervention training | neural alignment to causal abstractions | causal structural alignment alone is not RAKL novelty |
| skill-aware data selection / model-aware curricula | allocate data to weak skills/model state | learner-conditioned selection alone is not RAKL novelty |
| textual/external skill → adapter/LoRA work | compile reusable external skills into weights | generic cognitive compilation is occupied; RAKL residual must be typed governance + authority firewall |
| e-graphs / equality saturation | compact equivalence universes and extraction | quotienting alternatives is parent mechanism; account for saturation/compilation cost |
| hidden-metric network navigability | local routing can exploit hidden geometry | motivates but does not establish VTG local navigability |
| reachability/plannability-aware latent world models | predictive representation may not be plannable | VTG must evaluate multi-horizon closed-loop reachability, not prediction/similarity |
| proof planning / rippling / analogy | structured goal residual and transfer under proof-relevant mappings | goal field/analogy are parent components, not standalone novelty |

The supplied VTG research note additionally identifies nearby proof-space, path-integral, higher-rewriting/polygraph and physical/biological solver families. Reverify exact citations and priority before publication.
