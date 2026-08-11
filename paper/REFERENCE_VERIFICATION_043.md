# Round 043 Reference Verification

Date: 2026-08-10

Status: bibliography identity/provenance verification for the v2 methods preprint. This document verifies bibliographic identity and the mechanism each source is used to motivate; it does not promote a cited mechanism into RAKL scientific authority.

## Newly assimilated references

| Reference | Identity status | RAKL use |
|---|---|---|
| Alchourrón, Gärdenfors & Makinson (1985), *On the Logic of Theory Change* | VERIFIED, Journal of Symbolic Logic 50(2):510-530, DOI `10.2307/2274239` | prior art for axiomatic contraction/revision and minimal-change belief revision |
| Lindley (1956), *On a Measure of the Information Provided by an Experiment* | VERIFIED, Annals of Mathematical Statistics 27(4):986-1005 | prior art for expected information supplied by experiments |
| Chaloner & Verdinelli (1995), *Bayesian Experimental Design: A Review* | VERIFIED, Statistical Science 10(3):273-304, DOI `10.1214/ss/1177009939` | prior art for utility-based Bayesian experimental design |
| Pearl (2009), *Causality*, 2nd ed. | VERIFIED book identity, Cambridge University Press | intervention/counterfactual distinction and structural causal models |
| Peters, Janzing & Schölkopf (2017), *Elements of Causal Inference* | VERIFIED book identity, MIT Press | explicit causal assumptions, interventions and learning causal structure |
| Abramsky & Brandenburger (2011), *The Sheaf-Theoretic Structure of Non-Locality and Contextuality* | VERIFIED, New Journal of Physics 13:113036 / arXiv:1102.0264 | strong prior art for local-context models and obstructions to global sections |
| Buneman, Khanna & Tan (2001), *Why and Where: A Characterization of Data Provenance* | VERIFIED, ICDT 2001:316-330, DOI `10.1007/3-540-44503-X_20` | database provenance ancestry and the distinction between origins of derived values |
| Sandve et al. (2013), *Ten Simple Rules for Reproducible Computational Research* | VERIFIED, PLoS Computational Biology 9(10):e1003285, DOI `10.1371/journal.pcbi.1003285` | computational provenance/replay discipline |
| Wilson et al. (2017), *Good enough practices in scientific computing* | VERIFIED, PLoS Computational Biology 13(6):e1005510, DOI `10.1371/journal.pcbi.1005510` | research-computing hygiene and reproducibility prior art |
| Lewis et al. (2020), *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* | VERIFIED, NeurIPS 2020 / arXiv:2005.11401 | explicit non-parametric retrieval memory is prior art; RAKL does not claim RAG |
| Liu et al. (2024), *Lost in the Middle* | VERIFIED, TACL 12:157-173, DOI `10.1162/tacl_a_00638` | long context is not automatically uniformly usable; motivation for bounded target-conditioned context |
| Shinn et al. (2023), *Reflexion* | VERIFIED, NeurIPS 2023 | verbal feedback, reflection and episodic feedback memory are prior art |
| Madaan et al. (2023), *Self-Refine* | VERIFIED, NeurIPS 2023 | same-model iterative self-feedback/refinement is prior art |
| Schmidt & Lipson (2009), *Distilling free-form natural laws from experimental data* | VERIFIED, Science 324(5923):81-85, DOI `10.1126/science.1165893` | equation/symbolic-law discovery as a proposal mechanism is prior art |
| Popper (1959 English ed.), *The Logic of Scientific Discovery* | VERIFIED book identity | falsifiability/corroboration as historical scientific-method prior art |
| Obsidian Help, *Graph view* | VERIFIED official documentation | UI analogy only: global/local note graph, filters, link direction and time-lapse |
| Obsidian Help, *Backlinks* | VERIFIED official documentation | UI analogy only: incoming-reference navigation |

## Existing v2 assimilated references retained from the first Round 043 pass

The v2 manuscript also retains verified/primary identities for model criticism, prediction/explanation, mechanisms, TMS/ATMS, partial identification, sensitivity analysis, W3C PROV, FAIR, RO-Crate, nanopublications, analogy, active learning, self-regulated learning, productive failure, bias blind spot, explanation reconstruction, and consider-the-opposite. Their role is documented in `paper/CITATION_ASSIMILATION_043.md`.

## Bibliography policy

1. A reference is included because a specific RAKL operator, distinction, falsifier or novelty correction depends on it; raw bibliography size is not an optimization target.
2. If a peer-reviewed version supersedes a preprint, retain one canonical bibliographic authority plus a version relation rather than double-counting it as independent scientific evidence.
3. A citation establishes intellectual lineage, not the correctness of a RAKL claim.
4. A neighbouring system's failure to mention a capability is not evidence that the capability is absent. Related-work matrices therefore use `not verified` rather than assumed negatives.
5. Obsidian documentation is cited as interface prior art only. Note hyperlinks do not supply RAKL's typed scientific relation, context, provenance or authority semantics.

## Current status

`ROUND043_V2_BIBLIOGRAPHY = VERIFIED_FOR_METHODS_PREPRINT`

A final journal-submission pass should refresh 2025-2026 preprint statuses and regenerate publication metadata from publisher/Crossref/arXiv sources close to submission.
