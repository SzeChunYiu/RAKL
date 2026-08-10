# Round 048 — Nature-skills recursive framework and manuscript review

**Date:** 2026-08-10  
**Status:** same-context internal pre-submission review after recursive hardening. This is **not independent peer review**, does not satisfy the `nature-reviewer` mutual-blindness condition, and does not imply Nature/editor acceptance.

**Frozen release rubric:** `Yuan1z0825/nature-skills@a816314de0bb985e7034886e01596059522255b9`, preserving the same rubric used in Rounds 045–046. Current public Nature-skills polishing guidance was used only as an auxiliary language/style audit; it does not silently replace the frozen release gate.

## Review team and delegated roles

The review was run through three fixed lenses so that formal claims, executable behaviour and publication language were challenged separately before synthesis.

1. **Reviewer A — formal methods / knowledge representation.** Background: algebraic specification, type systems, formal knowledge representation and scientific-model semantics. Primary task: identify theorem inflation, invalid lattice language, hidden assumptions, and places where prose claims exceed executable invariants.
2. **Reviewer B — systems / reproducibility / verification.** Background: reproducible scientific software, CI subject binding, provenance, fail-closed pipelines and adversarial testing. Primary task: trace every publication claim to the exact checkout, test, receipt or typed transition that can support it.
3. **Reviewer C — scientific editorial / prior art.** Background: methods-paper editing, information retrieval, agentic-science literature and claim-local citation review. Primary task: assess novelty boundaries, human readability, section flow, hedging, and whether the prose reads as a paper rather than a specification.

The reviewers shared the final repair ledger, so this is a coordinated internal audit rather than mutually blind external review.

## External prose calibration

The language pass examined recent human-written methods/theory papers for structure and cadence rather than copying wording. Three patterns were retained.

- Chen et al., *An agentic artificially intelligent X-ray scientist* (Nature Machine Intelligence, 2026) moves from a concrete scientific bottleneck to the system contribution and explicitly narrows what is not novel.
- Gurnee et al., *Verbalizable Representations Form a Global Workspace in Language Models* (2026) introduces a functional question in accessible language, then marks philosophical and mechanistic boundaries directly rather than hiding them in a limitations paragraph.
- Garikaparthi et al., *MIR: Methodology Inspiration Retrieval for Scientific Research Problems* (ACL 2025) frames the retrieval failure first, defines the new task only after the gap is clear, and separates empirical result from the broader motivation.

The retained editorial rule is therefore problem-led and evidence-led: introduce formal machinery when the reader knows why it is needed; prefer connected explanatory paragraphs to inventory prose; keep taxonomic lists only where the taxonomy itself matters; and use explicit negative claims to bound novelty.

## Major findings and repairs

### R48-M1 — PR publication builds were not actually bound to the checked-out head

**Reviewer:** B  
**Blocking:** Yes.

**Finding.** The workflow checked out `github.event.pull_request.head.sha` on pull requests, but manuscript builders received `$GITHUB_SHA`. For a pull-request event, `$GITHUB_SHA` denotes GitHub's synthetic merge subject rather than the checked-out PR head. A build could therefore pass the checkout assertion while printing a different commit in the paper.

**Repair.** The checkout-binding step now exports `RAKL_SUBJECT_SHA=$EXPECTED_SHA`. V2.1, V2.2 and *Epistemic Mechanics* all bind the manuscript to `RAKL_SUBJECT_SHA`. A regression test rejects any return to `--subject-sha "$GITHUB_SHA"` and requires all three builders to use the checked-out subject.

**Disposition:** closed in workflow/code; exact PR CI still required on the repaired head.

### R48-M2 — *Epistemic Mechanics* over-promoted construction invariants into theorem language

**Reviewers:** A, C  
**Blocking:** Yes for formal presentation.

**Finding.** Workspace non-authority and conservative workspace extension are important properties, but in the current implementation they follow primarily from write-surface restrictions. Finite-budget OWMD termination is likewise a direct finite-computation observation. Presenting all three as theorems made the mathematical contribution look larger but less credible.

**Repair.** The write-surface results are now propositions (`Authority-preservation invariant` and `Conservative workspace metadata`), with prose stating that the first is an invariant by construction. Finite-budget termination is ordinary explanatory text. The genuinely substantive impossibility result—finite transcripts cannot certify unrestricted open-world non-existence without a complete oracle—remains a theorem.

**Disposition:** closed in manuscript source; compile and render still required.

### R48-M3 — The paper title promised a knowledge lattice while the formal audit denied a global lattice

**Reviewer:** A  
**Blocking:** Yes for claim precision.

**Finding.** The original title, *From Linguistic Claims to Evidence-Governed Knowledge Lattices*, could be read as asserting that the full implemented substrate is an order-theoretic lattice. The paper itself correctly proves only that the historical atom/witness/path object is a typed compatibility complex unless additional scoped order and meet/join obligations are supplied.

**Repair.** The title is now *Epistemic Mechanics: From Linguistic Claims to Evidence-Governed Scientific State*. Lattice language remains inside the paper only where its obligations are discussed explicitly.

**Disposition:** closed.

### R48-M4 — OWMD closure could be self-certified by bare booleans

**Reviewers:** A, B  
**Blocking:** Yes for a claim that bounded closure is evidence-governed.

**Finding.** `audit_bounded_discovery_closure()` previously accepted `independent_omission_review=True`, `nearest_work_equivalence_audit=True`, and `unresolved_preserved=True`. Those values carried no audit identity, reviewer context or evidence pointer. The closure layer therefore demanded provenance rhetorically while allowing release-critical review gates to be asserted without provenance in software.

**Repair.** Closure now requires `DiscoveryAuditEvidence` records containing audit ID, function ID, audit kind, reviewer-context ID, evidence IDs and completion status. The omission review additionally requires an explicit independence flag. Unresolved candidates require `UnresolvedCandidateFiber` records rather than a preservation boolean. Tests verify that a non-independent omission review cannot close discovery and that an unresolved candidate without a fiber keeps closure open. The JSON schema has been updated accordingly.

**Disposition:** closed in reference mechanics; full suite still required.

### R48-M5 — The manuscripts read as specifications rather than papers

**Reviewer:** C  
**Blocking:** Yes for publication quality, not for software correctness.

**Finding.** The new sections were technically careful but relied on dense enumeration, repeated framework declarations, defensive phrases and a uniform formal cadence. The reader met machinery before motivation in several places. The effect was mechanical even where individual sentences were grammatical.

**Repair.** *Epistemic Mechanics* now begins with the practical distinction between making a claim available and making it trustworthy, introduces the motivating discovery miss before OWMD terminology, and uses connected counterexamples to explain access/coherence/authority. The V2.2 overlay was similarly rewritten around the persistent-state/active-context distinction and the ontology-conditioned-closure failure. Repetitive “RAKL claims/ensures” phrasing and theorem-like labels were reduced. Prior-art paragraphs now narrow novelty directly rather than treating lineage as a citation inventory.

**Disposition:** closed at source level; render-level readability remains to be checked.

### R48-M6 — Exact SHA metadata caused the remaining *Epistemic Mechanics* overflow

**Reviewer:** B/C  
**Blocking:** Yes under the zero-overfull-box publication gate.

**Finding.** The 40-character Git SHA was placed inline in a prose paragraph. TeX correctly refused to break the monospaced token, producing a 68.98 pt overfull box.

**Repair.** Exact subject metadata is now displayed on its own centred line. The SHA is still complete and machine-verifiable; no provenance information is truncated for layout convenience.

**Disposition:** source repair complete; final PDF preflight required.

## Minor comments retained for final validation

1. Underfull boxes are presentation signals but are not blocking under the existing gate unless visual inspection shows a damaged page.
2. `GWT-OMISSION-01` remains a retrospective software-contract regression. It must not be described as prospective hidden-concept recall.
3. J-space remains a functional/geometric comparison only. The manuscripts must continue to reject both `J-space = RAKL lattice` and any inference from workspace-like function to phenomenal consciousness.
4. The new audit-evidence records improve closure provenance but do not create genuinely independent reviewers by themselves; reviewer independence is still an externally meaningful property that must be supported by the registered context.
5. The framework paper's receipt-bound figures and the methods paper's exact subject line must be inspected in the final rendered artifacts rather than inferred from successful LaTeX compilation.

## Recommendation after Round 048

**Recommendation: MINOR_REVISION_FINAL_EXACT_SUBJECT_VALIDATION.**

No conceptual blocker remains open in this round after the repairs above. Publication readiness is now contingent on the same exact-subject gates defined in Round 046: full tests and deterministic receipts, exact manuscript/check-out binding, warning-free PDF preflight, complete page rendering and visual inspection, and continued bounded public claims. A final review may return `READY_FOR_PUBLIC_METHODS_PREREGISTRATION_RELEASE` only after those gates are observed on one final subject.
