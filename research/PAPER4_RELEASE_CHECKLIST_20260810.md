# Paper IV Publication Closeout — 2026-08-10

Target manuscript: **Verified Discovery: An Assurance Architecture for LLM-Mediated Mathematical Research**

## Release gates

The paper is publishable from this branch only when all of the following are true for the exact head SHA that is merged:

- [ ] full repository `pytest` passes;
- [ ] hostile mathematical-research assurance packet passes all registered cases;
- [ ] release manuscript is built by `paper/build_math_research_assurance.py` and bound to the exact Git SHA and passing-test count;
- [ ] assurance-decomposition proposition is present in the staged manuscript;
- [ ] typed discovery-search/reference-implementation section is present;
- [ ] AlphaProof citation is normalized to the Nature 651 (2026) version of record;
- [ ] LaTeX compilation succeeds with no undefined citations/references, overfull boxes, undefined control sequences or oversized floats;
- [ ] all PDF pages render successfully;
- [ ] PDF text contains the expected title and load-bearing release sections;
- [ ] publication artifact ZIP contains staged TeX, PDF, logs, font/PDF metadata, page renders, hostile-benchmark receipt and pytest receipt;
- [ ] PR is retargeted to `main` only after ancestry is checked;
- [ ] PR is non-draft and mergeable;
- [ ] the merge uses the exact CI-tested head SHA.

## Scientific claim boundary

Passing these gates establishes release engineering and reference-implementation conformance for the stated assurance architecture. It does not establish global novelty detection, universal problem-solving completeness, autonomous-mathematician performance or empirical superiority on open mathematical research.

## Runtime readiness

A usable release must expose all of the following repository surfaces:

```text
skills/rakl-core/workflows/problem-solving.md
skills/rakl-core/workflows/mathematical-research.md
src/rakl/problem_solving_algebra.py
src/rakl/math_research_runtime.py
src/rakl/math_research_assurance.py
benchmarks/math_research_assurance/tasks_v0.json
docs/PROBLEM_SOLVING_ALGEBRA.md
docs/MATH_RESEARCH_QUICKSTART.md
```

The runtime is considered reference-ready when a user can create a problem signature and research record, receive explicit assurance blockers and candidate operator paths, bind a formalization, attach a proof receipt, attach bounded novelty evidence, perform research-value review and query the final non-compensatory publication stage.
