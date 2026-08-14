# Paper I — Submission Readiness

Paper: `publication/papers/paper-01-epistemic-mechanics` ("Epistemic Mechanics for
Evidence-Governed Scientific Research"). Assessed 2026-08-14 on branch
`paper1-submission-readiness`. This file records what is VERIFIED and what is OPEN.
Nothing here is a claim that independent review occurred; it did not, and the paper
does not say it did.

## Verified (evidence attached to each line)

| Item | Status | Evidence |
|---|---|---|
| Claim/inventory bijection | PASS | 18 theorem-like environments in `sections/` map 1:1 onto the 18 claims in `theorem_inventory.json`; no unlisted claim, no orphaned row (environment enumeration, 2026-08-14) |
| Claim location pointers | PASS | 5 pointers recomputed after this pass's insertions; only `location` fields touched, no status/note/history field changed |
| Mechanization posture stated | PASS | Intro summary + new appendix subsection "Machine-checked formalization"; 87 axiom-free Lean theorems at archival revision (count CI-pinned in `paper1-formal-proofs.yml`, `expected=87`) |
| Greedy-optimality boundary | PASS | New remark in §Workspace states exactly: ingredients machine-checked, assembly not, Nat special case; matches inventory `status_rationale` |
| §04g implementation remark | PASS | Remark cites `support_solver.py` / `derivation.py` / `certificates.py` / `structure_space.py` / `recursive_solver.py`; benefit experiment stated as *under prospective evaluation*, no result claimed |
| No independent-review claim | PASS | Full-text audit: every "independent review" mention is requirement-form or disclaimer-form; inventory `review_provenance.independent = false`; CI asserts it stays false |
| PDF build | PASS | latexmk rc=0 on laptop billy (isolated worktree `~/rakl-verify-p1sr`, 2026-08-14 14:47), 60 pages |
| Unresolved refs/citations | PASS (zero) | CI failure-pattern grep over `main.log`: 0 hits for undefined references, undefined citations, overfull boxes, any LaTeX warning; grep negative-controlled (planted lines match: 2/2) |
| New content in PDF | PASS | `pdftotext` finds "eight contributions", "Machine-checked formalization", "under prospective evaluation" |
| Bibliography | PASS | 100 bibitems (>= 40 required); CI enforces every item cited |
| Author metadata + AI-use disclosure | PASS | Title page carries name/affiliation/email; disclosure section present; both CI-enforced (`publication-pdfs.yml`) |
| Release identity binding | PASS (by mechanism) | `\ImplementationSHA` / `\SoftwareTests` are rebound by CI to the evaluated HEAD at archival build; source values are placeholders by design |
| `paper_framework_consistency` | PASS for Paper I | 4 consistent, 2 divergent — both accepted divergences name Paper V and Paper VI, not Paper I; no Paper-I-side repair licensed or required |

## Open — operator input required

| Item | Why open | Required input |
|---|---|---|
| Venue selection | Not chosen; every formatting item below is conditional on it | Operator: name the venue |
| Abstract length | 369 words; common journal limits are 150–250 | Operator decision: shortening is a content call, not a mechanical edit |
| Keywords | None in source; venue-dependent taxonomy | Operator-supplied after venue selection |
| Author list / ORCID / funding / competing interests / acknowledgements / licensing | Deliberately not inferred by the repository (stated in the disclosure section) | Operator-supplied submission metadata |
| Anonymization | If the venue is double-blind, title page and artifact links need an anonymized variant | Operator + venue rules |
| Page/format limits | 60 pp, a4 11pt article; fine for most journals, over conference limits | Venue-dependent |
| Independent formal-proof review (issue #216, RES-P1F-004) | Operator waived it for this submission; waiver is not closure. The paper claims only machine-checking and same-context reading, never independent review | External reviewer, post-submission or venue-provided |
| Greedy-optimality Lean assembly (RES-P1F-003) | Assembly of the three mechanized ingredients into the stated theorem is not machine-checked | Optional Lean work; paper is honest without it |
| Benefit experiment | RUNNING at time of writing; paper says prospective, claims no result | If it concludes pre-submission, update the §04g remark to cite the receipt — in either direction, including null |

## Statement coverage

18/18 claims at defended terminals (`theorem_inventory.json`, 2026-08-14):
17 MECHANIZED/FULL, 1 PAPER_PROOF_COMPLETE/PARTIAL (P1-T-GREEDY-OPTIMALITY —
deliberately not labelled partially-mechanized; see its `status_rationale`).
No claim UNREVIEWED, no proof gap recorded.

## Verdict

Formally and mechanically submission-ready: content-consistent with its inventory,
builds clean with zero unresolved references, and makes no claim its evidence does
not license. Blocked from actual submission only by the operator-supplied items
above — venue, abstract shortening, keywords, and submission metadata. No repository
work remains that can substitute for those inputs.
