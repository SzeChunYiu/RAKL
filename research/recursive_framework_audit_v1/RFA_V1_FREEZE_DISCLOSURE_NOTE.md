# RFA v1 freeze — disclosure note (2026-08-15)

The frozen bytes of `RFA_V1_CLAIM_BOUNDARY.md`, `RFA_V1_FROZEN_BENCHMARK.json` and
`RFA_V1_PARENT_MATRIX.md` are **not edited by this note**. Outcomes exist as of
`RFA_V1_CONFORMANCE_RESULT.json` (merged in #722), so the freeze is governed and a
correction is carried alongside it rather than applied to it — the same handling as
the Paper III narrowing correction (#679/#680).

## Disclosed defect

`RFA_V1_CLAIM_BOUNDARY.md` (section "Utility path", line 53) cites the vendored RFC-v1
benchmark design as:

```text
reference/RFC_V1_BENCHMARK_DESIGN.json
```

The file is vendored at:

```text
reference/22_RFC_V1_BENCHMARK_DESIGN.json
```

The cited path does not resolve. Every other path referenced by the freeze does
(`reference/recursive_framework_audit_reference.py`, `src/rakl/self_evolution_controller.py`).

## Scope of the defect

Pointer only. The vendored file is byte-identical to the handoff packet
(`sha256 d32d57926e00ac069c5ffed3c67de6ea3707f76347b507b76e8be89965aca3c0`, matching
`26_MANIFEST.json`), its status is unchanged (`DESIGN_FOR_FUTURE_FREEZE`), and no
conformance case, invariant check or terminal reads the claim-boundary prose. The
committed conformance result is unaffected.

The same section also reads "un unfamiliar-problem arm comparison"; "an" is intended.

## Standing obligation restated

The RFC-v1 utility design must be re-frozen on the implementation subject before any
utility execution. Known-world conformance remains instrument evidence only and is not
utility, scientific or method-promotion evidence.

## Independence caveat recorded at the same time

The 14 reference conformance cases and the 12 hostile priority cases in
`RFA_V1_FROZEN_BENCHMARK.json` are transcriptions of the vendored reference
implementation's own action vocabulary and priority chain. They test that the production
controller reproduces the reference, not that the reference's ordering is correct. The 8
structural invariant checks (`S01`--`S08`) are the part of the benchmark that can fail
independently of the reference. The claim boundary already scopes the result as
"reference conformance only"; this note makes the reason explicit.
