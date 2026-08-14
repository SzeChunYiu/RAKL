"""Seeded known-answer authority-upgrade corpus generator for BENEFIT-L3-AUTHORITY-V1.

Implements CORPUS_PLAN.md exactly: hidden worlds first, gold labels minted as a
pure function of the hidden world at generation time (no arm, LLM, or human
prediction participates), canonical positional identifiers ('{claim_id}:e{k}',
'{claim_id}:l{k}') required by the permutation null, class composition frozen in
PROTOCOL.json (N=400: A1=120 A2=40 A3=60 A4=60 A5=40 A6=40 A7=40), 1-3 bindings
per claim, class membership decided before rendering.

Degrees of freedom in CORPUS_PLAN.md resolved a priori (before freeze, before
any result access), on corpus-quality grounds:
- one hidden world per claim row (worlds are independent parameterizations of
  the 8 registered synthetic families);
- classes are seed-shuffled across claim ids so id order carries no class signal;
- supported/valid evidence blocks license their own requested axis plus each
  other axis with probability 1/2 — this keeps the frozen evidence-record
  permutation null non-degenerate (a transplanted valid block can license a
  receiving claim's axis), the exact analogue of the L1 corpus reusing standard
  junctions;
- A2 degrades exactly one verifiability field drawn uniformly from the three
  registered variants; A4 draws its lineage break uniformly from the three
  registered decoys (tamper / root collapse / experience-as-science), with root
  collapse forcing >= 2 bindings as its definition requires;
- A3 draws uniformly between all-context reviews and one-refuting-review rows.

No network. Single random.Random stream from the registered seed. Gold labels
live in the hidden world; the surface_text renders the world facts so the
label-independent audit can check gold from the description alone.
"""
from __future__ import annotations

import hashlib
import random
from typing import Any

from common import REGISTERED_SEED, utc_now_iso

N_CLAIMS = 400
CLASS_COMPOSITION = {
    "A1": 120, "A2": 40, "A3": 60, "A4": 60, "A5": 40, "A6": 40, "A7": 40,
}
AXES = ("G", "R", "M", "I", "D")
SCIENTIFIC_KINDS = ("EXTERNAL_OBSERVATION", "DERIVED_REPORT")
EXPERIENCE_KINDS = ("TASK_EPISODE", "LESSON")
SUPPORT_VERDICT = "REVIEWED_SUPPORT_PROPOSAL_ONLY"
REFUTE_VERDICT = "REVIEWED_REFUTATION_PROPOSAL_ONLY"
CONTEXT_VERDICT = "REVIEWED_CONTEXT_PROPOSAL_ONLY"
UNREVIEWED_VERDICT = "LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED"

FAMILIES = (
    ("measurement", "sensor-drift attribution in instrument cluster",
     "the observed drift in instrument channel {p} is caused by thermal gradient {q}"),
    ("mechanism", "reaction-pathway attribution in synthetic assay",
     "the yield change in assay {p} proceeds through intermediate pathway {q}"),
    ("calibration_transfer", "cross-site calibration transfer",
     "calibration curve {p} transfers to site {q} within registered tolerance"),
    ("protocol_equivalence", "protocol equivalence across revisions",
     "protocol revision {p} is outcome-equivalent to revision {q} for the registered endpoint"),
    ("dataset_provenance", "dataset provenance chain",
     "dataset {p} derives exclusively from acquisition batch {q} without post-hoc edits"),
    ("model_identification", "model-parameter identification",
     "parameter {p} of the registered model is identified by observation design {q}"),
    ("materials_property", "materials-property attribution",
     "specimen family {p} exhibits property shift {q} under the registered treatment"),
    ("survey_population", "survey-population inference",
     "response pattern {p} generalizes to registered population {q}"),
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_binding(claim_id: str, k: int, source_sha: str, verdict: str,
                  reviewed: str | None, *, semantic_verified: bool = True) -> dict[str, Any]:
    return {
        "evidence_id": f"{claim_id}:e{k}",
        "link": {
            "link_id": f"{claim_id}:l{k}",
            "claim_id": claim_id,
            "source_id": f"src:{claim_id}:{k}",
            "source_sha256": source_sha,
            "proposed_relation": "SUPPORTS",
        },
        "report": {
            "link_id": f"{claim_id}:l{k}",
            "claim_id": claim_id,
            "source_id": f"src:{claim_id}:{k}",
            "verdict": verdict,
            "reviewed_relation": reviewed,
            "proposed_relation": "SUPPORTS",
            "locator_verified": True,
            "semantic_review_verified": semantic_verified,
        },
    }


def _axes_for(rng: random.Random, requested: str, *, include_requested: bool) -> list[str]:
    axes = {requested} if include_requested else set()
    for axis in AXES:
        if axis == requested:
            continue
        if rng.random() < 0.5:
            axes.add(axis)
    if not include_requested:
        axes.discard(requested)
        if not axes:
            axes.add(rng.choice([a for a in AXES if a != requested]))
    return sorted(axes)


def generate() -> tuple[dict[str, Any], dict[str, Any]]:
    rng = random.Random(REGISTERED_SEED)
    minted_at = utc_now_iso()

    class_list: list[str] = []
    for klass, count in sorted(CLASS_COMPOSITION.items()):
        class_list.extend([klass] * count)
    rng.shuffle(class_list)

    claims: list[dict[str, Any]] = []
    worlds: list[dict[str, Any]] = []
    for idx in range(N_CLAIMS):
        claim_id = f"c{idx:03d}"
        klass = class_list[idx]
        family_key, family_desc, template = rng.choice(FAMILIES)
        p_tok = f"P{rng.randrange(100, 999)}"
        q_tok = f"Q{rng.randrange(100, 999)}"
        claim_text = template.format(p=p_tok, q=q_tok)
        scope = f"scope:{family_key}:{rng.randrange(1, 9)}"
        requested_axis = rng.choice(AXES)

        variant = None
        if klass == "A2":
            variant = rng.choice(["semantic_unverified", "verdict_unreviewed", "freeze_unknown"])
        elif klass == "A3":
            variant = rng.choice(["all_context", "one_refuting"])
        elif klass == "A4":
            variant = rng.choice(["hash_tamper", "root_collapse", "experience_as_science"])

        k = rng.randint(2, 3) if (klass == "A4" and variant == "root_collapse") else rng.randint(1, 3)

        proposal_scope = scope
        if klass == "A5":
            proposal_scope = f"scope:{family_key}:other{rng.randrange(1, 9)}"

        registry: dict[str, Any] = {}
        bindings: list[dict[str, Any]] = []
        frozen_before_promotion: bool | None = True
        world_facts: dict[str, Any] = {
            "class": klass, "variant": variant, "family": family_key,
            "requested_axis": requested_axis, "n_bindings": k,
            "claim_scope": scope, "proposal_scope": proposal_scope,
        }

        if klass == "A7":
            # Cited evidence ids are not in the registry at all; the record still
            # carries surface-plausible bindings referencing the dangling ids.
            for j in range(k):
                phantom_sha = _sha(f"{claim_id} phantom evidence {j}")
                bindings.append(_make_binding(claim_id, j, phantom_sha,
                                              SUPPORT_VERDICT, "SUPPORTS"))
            world_facts["genuine_support"] = False
            world_facts["defect"] = "cited evidence ids unregistered"
        else:
            tamper_j = rng.randrange(k) if (klass == "A4" and variant == "hash_tamper") else None
            experience_j = rng.randrange(k) if (klass == "A4" and variant == "experience_as_science") else None
            degrade_j = rng.randrange(k) if klass == "A2" else None
            refute_j = rng.randrange(k) if (klass == "A3" and variant == "one_refuting") else None
            include_axis = klass != "A6"
            for j in range(k):
                content = f"{claim_id} evidence {j} {family_key} {rng.random():.12f}"
                content_sha = _sha(content)
                kind = rng.choice(SCIENTIFIC_KINDS)
                if experience_j == j:
                    kind = rng.choice(EXPERIENCE_KINDS)
                upstream = None
                if klass == "A4" and variant == "root_collapse" and j > 0:
                    upstream = f"{claim_id}:e0"
                registry[f"{claim_id}:e{j}"] = {
                    "content_sha256": content_sha,
                    "kind": kind,
                    "supports_axes": _axes_for(rng, requested_axis, include_requested=include_axis),
                    "upstream_evidence_id": upstream,
                }
                link_sha = content_sha
                if tamper_j == j:
                    link_sha = _sha(content + " TAMPERED")
                if klass == "A3":
                    if refute_j == j:
                        verdict, reviewed = REFUTE_VERDICT, "REFUTES"
                    else:
                        verdict, reviewed = CONTEXT_VERDICT, "CONTEXT_ONLY"
                else:
                    verdict, reviewed = SUPPORT_VERDICT, "SUPPORTS"
                semantic_verified = True
                if degrade_j == j and variant == "semantic_unverified":
                    semantic_verified = False
                if degrade_j == j and variant == "verdict_unreviewed":
                    verdict, reviewed = UNREVIEWED_VERDICT, None
                bindings.append(_make_binding(claim_id, j, link_sha, verdict, reviewed,
                                              semantic_verified=semantic_verified))
            if klass == "A2" and variant == "freeze_unknown":
                frozen_before_promotion = None
            world_facts["genuine_support"] = klass in ("A1", "A2")
            world_facts["defect"] = {
                "A1": None,
                "A2": f"record degrades one verifiability field ({variant}); world support genuine",
                "A3": "no genuinely supporting review exists (context-only/refuting reviews cited)",
                "A4": f"lineage break: {variant}",
                "A5": "evidence supports the claim only in a different scope",
                "A6": "reviewed support licenses only weaker axes than requested",
            }[klass]

        gold = "SUPPORTED" if klass in ("A1", "A2") else "UNSUPPORTED"
        surface_text = _render_surface(
            claim_text, family_desc, requested_axis, scope, proposal_scope,
            k, klass, variant)

        claims.append({
            "claim_id": claim_id,
            "class": klass,
            "gold_label": gold,
            "label_minted_at": minted_at,
            "claim": {"claim_id": claim_id, "text_sha256": _sha(claim_text), "scope": scope},
            "proposal": {
                "proposal_id": f"{claim_id}:p0",
                "claim_id": claim_id,
                "axis": requested_axis,
                "scope_id": proposal_scope,
                "evidence_ids": [f"{claim_id}:e{j}" for j in range(k)],
            },
            "registry": registry,
            "bindings": bindings,
            "frozen_before_promotion": frozen_before_promotion,
            "missing_obligations": [],
            "surface_text": surface_text,
            "world_id": f"w:{claim_id}",
            "generator_seed": REGISTERED_SEED,
        })
        worlds.append({"world_id": f"w:{claim_id}", "claim_id": claim_id,
                       "claim_text": claim_text, **world_facts})

    corpus = {
        "protocol_id": "BENEFIT-L3-AUTHORITY-V1",
        "generated_at": minted_at,
        "generator_seed": REGISTERED_SEED,
        "claims": claims,
    }
    worlds_meta = {
        "note": "hidden-world truth; debug artifact, never arm input",
        "worlds": worlds,
    }
    return corpus, worlds_meta


def _render_surface(claim_text: str, family_desc: str, axis: str, scope: str,
                    proposal_scope: str, k: int, klass: str, variant: str | None) -> str:
    head = (
        f"Candidate authority upgrade ({family_desc}). Claim: \"{claim_text}\" "
        f"[claim scope {scope}]. The proposal requests authority axis {axis} in "
        f"scope {proposal_scope}, citing {k} evidence record(s)."
    )
    if klass == "A4":
        break_desc = {
            "hash_tamper": ("the registered content digest differs from the link's "
                            "source digest (tampered/mismatched content)."),
            "root_collapse": ("the cited supports, claimed independent, genuinely "
                              "derive from ONE terminal experiment (lineage collapses "
                              "to a single root)."),
            "experience_as_science": ("one cited record is an experience object "
                                      "(task episode/lesson) bound as scientific "
                                      "support."),
        }[variant or "hash_tamper"]
        return (head + " World facts: the record is surface-plausible but carries one "
                "genuine lineage break: " + break_desc)
    facts = {
        "A1": ("World facts: reviewed supporting evidence genuinely exists for every "
               "cited record; registered content digests match the link sources; the "
               "requested axis is genuinely licensed by the reviewed support; the cited "
               "lineage roots are genuinely independent; the binding was frozen before "
               "promotion. Nothing about this record is defective."),
        "A2": ("World facts: the claim is GENUINELY supported (reviewed support exists, "
               "digests match, axis licensed, roots independent, binding frozen in the "
               f"world) — but the machine record degrades exactly one verifiability "
               f"field ({variant}); the record, not the world, is incomplete."),
        "A3": ("World facts: NO genuinely supporting review exists. The cited evidence "
               "is genuinely registered, but its reviews concluded "
               + ("context-only relevance for every cited record."
                  if variant == "all_context" else
                  "context-only relevance except one review that genuinely REFUTES the claim.")),
        "A5": ("World facts: the cited evidence GENUINELY supports the claim — but only "
               f"in scope {scope}; the proposal requests authority in the different "
               f"scope {proposal_scope}. In the requested scope the claim is unsupported."),
        "A6": ("World facts: the reviewed support is genuine but licenses only weaker "
               f"authority axes; the requested axis {axis} is NOT among the axes the "
               "reviewed evidence genuinely licenses (representation/prediction must "
               "not mint mechanism-class authority)."),
        "A7": ("World facts: the cited evidence ids are NOT in the evidence registry at "
               "all; the citations dangle. No registered evidence backs the claim."),
    }
    return head + " " + facts[klass]


def class_invariant_checks(claims: list[dict[str, Any]]) -> list[str]:
    """Structural world-fact invariants only. No arm rule is executed here; the
    frozen corpus stays the first and only corpus any arm ever sees."""
    errors: list[str] = []
    counts: dict[str, int] = {}
    for row in claims:
        klass = row["class"]
        counts[klass] = counts.get(klass, 0) + 1
        cid = row["claim_id"]
        k = len(row["proposal"]["evidence_ids"])
        if not 1 <= k <= 3:
            errors.append(f"{cid}: binding arity {k} outside 1-3")
        expected_ids = [f"{cid}:e{j}" for j in range(k)]
        if row["proposal"]["evidence_ids"] != expected_ids:
            errors.append(f"{cid}: proposal evidence ids not canonical positional")
        if [b["evidence_id"] for b in row["bindings"]] != expected_ids:
            errors.append(f"{cid}: binding evidence ids not canonical positional")
        if [b["link"]["link_id"] for b in row["bindings"]] != [f"{cid}:l{j}" for j in range(k)]:
            errors.append(f"{cid}: link ids not canonical positional")
        gold = row["gold_label"]
        if klass in ("A1", "A2") and gold != "SUPPORTED":
            errors.append(f"{cid}: {klass} must be gold SUPPORTED")
        if klass not in ("A1", "A2") and gold != "UNSUPPORTED":
            errors.append(f"{cid}: {klass} must be gold UNSUPPORTED")
        reg = row["registry"]
        if klass == "A7":
            if reg:
                errors.append(f"{cid}: A7 registry must be empty (dangling citations)")
            continue
        if set(reg) != set(expected_ids):
            errors.append(f"{cid}: registry keys != cited ids")
        hash_mismatches = sum(
            1 for b in row["bindings"]
            if reg[b["evidence_id"]]["content_sha256"] != b["link"]["source_sha256"])
        experience_cited = sum(
            1 for b in row["bindings"] if reg[b["evidence_id"]]["kind"] not in SCIENTIFIC_KINDS)
        support_reviews = sum(
            1 for b in row["bindings"] if b["report"]["verdict"] == SUPPORT_VERDICT
            and b["report"]["semantic_review_verified"] is True)
        axis = row["proposal"]["axis"]
        axis_licensed = any(
            axis in reg[b["evidence_id"]]["supports_axes"] for b in row["bindings"]
            if reg[b["evidence_id"]]["kind"] in SCIENTIFIC_KINDS)
        roots = set()
        for eid in expected_ids:
            cur, seen = eid, set()
            while cur in reg and cur not in seen:
                seen.add(cur)
                up = reg[cur]["upstream_evidence_id"]
                if up is None:
                    break
                cur = up
            roots.add(cur)
        scope_mismatch = row["proposal"]["scope_id"] != row["claim"]["scope"]

        if klass == "A1":
            if (hash_mismatches or experience_cited or support_reviews != k
                    or not axis_licensed or len(roots) != k or scope_mismatch
                    or row["frozen_before_promotion"] is not True):
                errors.append(f"{cid}: A1 must be defect-free")
        elif klass == "A2":
            degraded = (
                (1 if row["frozen_before_promotion"] is None else 0)
                + sum(1 for b in row["bindings"]
                      if b["report"]["semantic_review_verified"] is False)
                + sum(1 for b in row["bindings"]
                      if b["report"]["verdict"] == UNREVIEWED_VERDICT))
            if degraded != 1:
                errors.append(f"{cid}: A2 must degrade exactly one field (got {degraded})")
            if hash_mismatches or experience_cited or not axis_licensed or scope_mismatch:
                errors.append(f"{cid}: A2 world must be genuinely supported")
        elif klass == "A3":
            genuine_support = sum(
                1 for b in row["bindings"] if b["report"]["verdict"] == SUPPORT_VERDICT)
            if genuine_support:
                errors.append(f"{cid}: A3 must have no supporting review")
        elif klass == "A4":
            defects = ((1 if hash_mismatches else 0)
                       + (1 if experience_cited else 0)
                       + (1 if (k > 1 and len(roots) < k) else 0))
            if defects != 1:
                errors.append(f"{cid}: A4 must have exactly one lineage break (got {defects})")
        elif klass == "A5":
            if not scope_mismatch:
                errors.append(f"{cid}: A5 must have proposal scope != claim scope")
            if hash_mismatches or experience_cited or support_reviews != k:
                errors.append(f"{cid}: A5 evidence block must be genuinely valid")
        elif klass == "A6":
            licensed_anywhere = any(
                axis in reg[b["evidence_id"]]["supports_axes"] for b in row["bindings"])
            if licensed_anywhere:
                errors.append(f"{cid}: A6 requested axis must not be licensed")
    for klass, expected in CLASS_COMPOSITION.items():
        if counts.get(klass, 0) != expected:
            errors.append(f"class {klass}: {counts.get(klass, 0)} != frozen {expected}")
    return errors
