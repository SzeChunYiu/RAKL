# Probe G on the controlled-witness extraction instrument — REFUTES the extraction reading

Status: `AUXILIARY_DIAGNOSTIC__PRIOR_TERMINAL_REFUTED_AS_AN_EXTRACTION_CLAIM`

Authority: same-context analysis. Not independent review. Promotes nothing.

Lineage. Subject is `research/paper2_controlled_witness_extraction_v1/`
(`PROTOCOL.json`, `FINAL_RECEIPT.json`). **Nothing frozen there is modified.**
The original protocol, receipt and workflow are preserved verbatim as negative
history. This directory is a superseding auxiliary audit, not a rewrite.

## 1. What was under test

`FINAL_RECEIPT.json` reports, under terminal
`PROMOTE_CONDITIONALLY_CONTROLLED_TEXT_STRUCTURAL_WITNESS_EXTRACTION` and scope
`CONTROLLED_SCIENTIFIC_PROSE_OVER_EXISTING_SIX_EXACT_VERIFIER_FAMILIES`:

```
full_controlled_extractor.exact_decision      1.0
full_controlled_extractor.invalid_false_accept 0.0
full_controlled_extractor.cannot_check_recall  1.0
strongest_parent_exact                        0.888…
```

Probe G had already shown the six-family robustness packet contains zero
extraction signal (`research/paper2_six_family_audit_v1/`, §5b). This run asks
the same question of the controlled-text instrument, which is the artifact that
carries Paper II's *text*-extraction reading.

## 2. Result — the text is inert and the extractor is a serialization inverse

Executed on laptop billy, `~/rakl-verify`, `.venv/bin/python` 3.11.14, at repo
`d4f57b58`, seed `202608140801`, n = 1296 base tasks / 2592 text surfaces
(gold 1152 ACCEPT / 1152 REJECT / 288 CANNOT_CHECK).

| measurement | result |
| --- | --- |
| rendered surface **changed** by text scramble | **1296 / 1296** |
| gold unchanged after text scramble | **1296 / 1296** |
| full arm unchanged after text scramble | **2592 / 2592** |
| `task.public` recovered byte-identically from the rendered text | **2592 / 2592** |
| parse complete | 2592 / 2592 |

The reproduced full arm matches the receipt exactly (`exact_decision` 1.0,
`invalid_false_accept` 0.0, `cannot_check_recall` 1.0, `valid_accept` 1.0), so
this is the same arm, not a re-specification.

The first row rules out the benign explanation: the scramble *did* reach the
candidate-visible surface. The surface changed on every item and nothing
downstream moved.

## 3. Why `exact_decision = 1.0` is entailed rather than measured

`render_controlled_task` emits `Label :: <json.dumps(value)>` lines. The
structural records `source`, `target`, `mapping`, `candidate_actions` — which
hold the answer — are serialized verbatim. `extract_controlled_task` splits on
`" :: "` and calls `json.loads` on the payload.

So the composition is the identity on `task.public`:

```
extract(render(t)).public == t.public      2592 / 2592
```

The arm then calls the *unchanged* gold verifier on that reconstructed task.
Predicted decision therefore equals gold whenever parsing succeeds, and parsing
succeeded 2592/2592. `exact_decision = 1.0` measures **serialization fidelity**,
not recovery of a structural witness from prose.

`source_text` and `target_text` are rendered onto the surface but no verifier in
`objective_transfer_benchmark_v2` reads them.

## 4. Clean baselines and shuffle-equal-n null

Required because selectivity is not edge, and because a null that merely rules
out a degenerate label distribution is not evidence of signal.

| arm | exact | valid_accept | invalid_FA | cc_recall |
| --- | --- | --- | --- | --- |
| `always_reject` | 0.444 | 0.000 | **0.000** | 0.000 |
| `always_accept` | 0.444 | 1.000 | 1.000 | 0.000 |
| `always_cannot_check` | 0.111 | 0.000 | 0.000 | 1.000 |
| full controlled extractor | 1.000 | 1.000 | 0.000 | 1.000 |

Shuffle equal-n null (200 reps, text↔answer binding destroyed, marginals
preserved): mean exact `0.407`, 95% `[0.391, 0.427]`; observed `1.000`.

The observed value lies far outside the null and no trivial arm reaches it —
and that is uninformative here, because §3 shows the gap is produced by the
round trip. A null can only tell you the labels vary; it cannot tell you the
score was earned.

## 5. What survives, and what does not

**Refuted as an extraction claim.** The terminal
`PROMOTE_CONDITIONALLY_CONTROLLED_TEXT_STRUCTURAL_WITNESS_EXTRACTION` cannot be
read as evidence that a bounded scientific-prose interface was compiled into an
applicability state. No prose was compiled. The scope string
"CONTROLLED_SCIENTIFIC_PROSE" overstates a labeled-JSON transport format.

**Survives.** The registered 10-mutation panel (`DROP_MAPPING`, `DROP_QOI`,
`DROP_BOUNDARY`, `DROP_PRECONDITION`, `DROP_RELATION_OR_DIRECTION`,
`UNKNOWN_AS_REJECT`, `UNKNOWN_AS_ACCEPT`, `IGNORE_TARGET_VALUE`,
`IGNORE_SOURCE_REQUIREMENT`, `DROP_SOURCE_SPAN_BINDING`; all caught) is a valid
test of **fail-closed parser behaviour under field omission and span-hash
tampering**. That is a real property of the interface. It is not extraction.

The honest residual claim of `paper2_controlled_witness_extraction_v1` is:
a hash-bound field-transport interface fails closed on omission, duplication,
unknown-label and span-mismatch. Reported as
`SERIALIZATION_INTERFACE_FAIL_CLOSED`, not as text extraction.

**Not established by this audit.** Nothing about whether structural coordinates
*can* be recovered from text. Probe G is a refutation of an instrument, not a
negative result about extraction capability.

## 6. Failure-lattice entry

Two independent Paper II instruments (`objective_transfer_robustness`, six
families; `controlled_witness_extraction`, six families) were built to test
text→structure recovery, and in both the text is inert because the answer is
carried alongside it in pre-parsed form.

```
residual signature   R1 schema/parser  +  R2 leakage
broken assumption    "a candidate-visible text surface implies a text-reading task"
shared mechanism     answer transported in a structured sibling field of the text
repair specification an instrument is only probative for extraction if
                     destroying the text destroys performance — this must be an
                     acceptance test run BEFORE any score is reported
```

Successor work must run probe G as a **pre-registration gate**, not as an audit
discovered afterwards.

## 7. Reproduction

```
PYTHONPATH=src:. .venv/bin/python \
  research/paper2_controlled_witness_extraction_audit_v1/probe_g_controlled_text_inertness.py
```

Result: `results/PROBE_G_CONTROLLED_TEXT_INERTNESS.json`.
