from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Iterable, Tuple

from .context_compiler import ContextCompileRequest, ContextItem, compile_epistemic_context
from .multires_memory import MemoryView, MemoryViewKind, SourcePin, validate_memory_view
from .research_cycle import (
    ResearchArtifactRef,
    ResearchStage,
    ResearchStep,
    StorageTier,
    TraceVerdict,
    stage_contracts,
    validate_research_trace,
)
from .saturation import ResearchRound, SaturationTracker
from .typed_lattice import (
    CompatibilityWitness,
    KnowledgeAtom,
    KnowledgeAtomKind,
    LatticeCompatibility,
    TypedKnowledgeLattice,
)


@dataclass(frozen=True)
class DemoSource:
    source_id: str
    round_id: str
    text: str
    lineage_id: str


@dataclass(frozen=True)
class DemoProjection:
    projection_id: str
    source_id: str
    canonical_key: str
    label: str
    context: Tuple[str, ...]


@dataclass(frozen=True)
class MiniResearchReceipt:
    demo_id: str
    target: str
    target_period_seconds_first_order: float
    raw_sources: int
    raw_payload_bytes: int
    projected_claims: int
    canonical_claims_after_exact_identity_collapse: int
    context_distinct_noncollapsed_claims: int
    atlas_atoms_before_new_evidence: int
    atlas_atoms_after_new_evidence: int
    typed_relation_witnesses_after_new_evidence: int
    apparent_contradictions_avoided_by_context_alignment: int
    true_aligned_contradictions_or_refutations: int
    negative_history_objects: int
    blocking_epistemic_cuts_before_new_evidence: int
    blocking_epistemic_cuts_after_new_evidence: int
    target_support_paths_before_new_evidence: int
    target_support_paths_after_new_evidence: int
    archive_token_estimate: int
    active_context_tokens: int
    active_to_archive_token_ratio: float
    canonical_memory_views: int
    lossless_memory_views: int
    lossy_memory_views: int
    source_rehydration_roots: Tuple[str, ...]
    semantic_novelty_by_round: Tuple[Tuple[str, int], ...]
    terminal_saturation_state: str
    atomic_trace_verdict: str
    atomic_stages_registered: int
    atomic_stages_executed_in_demo_trace: int
    llm_calls_in_deterministic_demo: int
    scientific_superiority_authority: bool


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sources() -> Tuple[DemoSource, ...]:
    return (
        DemoSource("S1", "R0", "For a simple pendulum at small angle on Earth, T = 2*pi*sqrt(L/g).", "L1"),
        DemoSource("S2", "R0", "At small amplitude, a 100 cm pendulum follows T = 2*pi*sqrt(1 m/g); the ideal period does not depend on bob mass.", "L2"),
        DemoSource("S3", "R1", "For moderate amplitude, the first finite-amplitude correction is T approximately T0*(1 + theta0^2/16).", "L3"),
        DemoSource("S4", "R0", "Within the small-angle approximation, pendulum period is approximately independent of amplitude.", "L4"),
        DemoSource("S5", "R0", "On the Moon the same length pendulum uses lunar gravitational acceleration rather than Earth gravity.", "L5"),
        DemoSource("S6", "R0", "Claim: increasing the bob mass increases the ideal simple-pendulum period at fixed length and gravity.", "L6"),
        DemoSource("S7", "R0", "Controlled ideal-pendulum check: changing bob mass at fixed length, gravity and small amplitude does not materially change the period.", "L7"),
        DemoSource("S8", "R3", "Independent derivation reproduces the same first finite-amplitude correction T/T0 approximately 1 + theta0^2/16.", "L8"),
    )


def _projections() -> Tuple[DemoProjection, ...]:
    return (
        DemoProjection("P1", "S1", "small_angle_period", "T=2*pi*sqrt(L/g)", ("Earth", "small_angle")),
        DemoProjection("P2", "S2", "small_angle_period", "same small-angle law after 100 cm -> 1 m normalization", ("Earth", "small_angle")),
        DemoProjection("P3", "S2", "mass_independence", "ideal period independent of bob mass", ("Earth", "small_angle")),
        DemoProjection("P4", "S3", "finite_amplitude_correction", "T/T0 approximately 1+theta0^2/16", ("Earth", "moderate_amplitude")),
        DemoProjection("P5", "S4", "small_angle_amplitude_independence", "amplitude independence is an approximation inside small-angle regime", ("Earth", "small_angle")),
        DemoProjection("P6", "S5", "moon_gravity_context", "same law with lunar g", ("Moon", "small_angle")),
        DemoProjection("P7", "S6", "mass_dependence", "period increases with mass", ("Earth", "small_angle")),
        DemoProjection("P8", "S7", "mass_invariance_observation", "mass intervention leaves ideal period unchanged", ("Earth", "small_angle")),
        DemoProjection("P9", "S8", "finite_amplitude_correction", "independent duplicate finite-amplitude correction", ("Earth", "moderate_amplitude")),
    )


def _base_lattice(include_finite: bool) -> TypedKnowledgeLattice:
    lattice = TypedKnowledgeLattice.empty()
    atoms = [
        KnowledgeAtom("A:small-law", "F:period", KnowledgeAtomKind.REPRESENTATION, "small-angle period law", ("S1", "S2")),
        KnowledgeAtom("A:earth", "F:context", KnowledgeAtomKind.REGIME, "Earth gravity context", ("S1",)),
        KnowledgeAtom("A:moon", "F:context", KnowledgeAtomKind.REGIME, "Moon gravity context", ("S5",)),
        KnowledgeAtom("A:small-angle", "F:context", KnowledgeAtomKind.ASSUMPTION, "small-angle regime", ("S1", "S4")),
        KnowledgeAtom("A:qoi", "F:target", KnowledgeAtomKind.QOI, "1 m, 20 degree Earth period", ()),
        KnowledgeAtom("A:mass-invariant", "F:mechanism", KnowledgeAtomKind.INVARIANT, "ideal period mass invariance", ("S2", "S7")),
        KnowledgeAtom("A:mass-dependence", "F:mechanism", KnowledgeAtomKind.CAUSAL_RELATION, "mass increases ideal period", ("S6",)),
        KnowledgeAtom("A:mass-check", "F:mechanism", KnowledgeAtomKind.DATA_PRODUCT, "controlled mass-invariance check", ("S7",)),
    ]
    if include_finite:
        atoms.append(
            KnowledgeAtom("A:finite-law", "F:period", KnowledgeAtomKind.REPRESENTATION, "finite-amplitude first correction", ("S3", "S8"))
        )
    for atom in atoms:
        lattice.add_atom(atom)

    def witness(left: str, right: str, relation: LatticeCompatibility, reason: str, *, condition: str | None = None, evidence: Tuple[str, ...] = ()) -> None:
        lattice.add_witness(CompatibilityWitness(left, right, relation, reason, condition=condition, evidence_ids=evidence))

    witness("A:small-law", "A:earth", LatticeCompatibility.COMPATIBLE, "small-angle law is stated for Earth context", evidence=("S1",))
    witness("A:earth", "A:qoi", LatticeCompatibility.COMPATIBLE, "target is explicitly Earth", evidence=("S1",))
    witness("A:small-law", "A:qoi", LatticeCompatibility.INCOMPATIBLE, "20 degree target exceeds the registered small-angle approximation used for target closure", evidence=("S4",))
    witness("A:moon", "A:qoi", LatticeCompatibility.INCOMPATIBLE, "Moon and Earth gravity contexts are distinct", evidence=("S5",))
    witness("A:mass-dependence", "A:mass-invariant", LatticeCompatibility.INCOMPATIBLE, "same ideal context gives opposite mass dependence", evidence=("S2", "S6", "S7"))
    witness("A:mass-check", "A:mass-invariant", LatticeCompatibility.COMPATIBLE, "controlled observation supports mass invariance", evidence=("S7",))
    witness("A:mass-check", "A:mass-dependence", LatticeCompatibility.INCOMPATIBLE, "controlled observation refutes mass-dependence claim", evidence=("S7",))
    witness("A:small-law", "A:small-angle", LatticeCompatibility.COMPATIBLE, "small-angle law requires the small-angle assumption", evidence=("S1", "S4"))

    if include_finite:
        witness("A:finite-law", "A:earth", LatticeCompatibility.COMPATIBLE, "finite-amplitude correction applies in Earth context", evidence=("S3",))
        witness("A:finite-law", "A:qoi", LatticeCompatibility.COMPATIBLE, "20 degree target is within the registered moderate-amplitude demonstration scope", evidence=("S3",))
        witness(
            "A:small-law",
            "A:finite-law",
            LatticeCompatibility.CONDITIONAL,
            "finite-amplitude relation reduces to small-angle law as amplitude approaches zero",
            condition="theta0 -> 0",
            evidence=("S1", "S3"),
        )
    return lattice


def _memory_views() -> Tuple[MemoryView, ...]:
    sources = {source.source_id: source for source in _sources()}
    canonical = tuple(
        MemoryView(
            record_id=f"raw:{source_id}",
            payload_hash=_sha(sources[source_id].text),
            kind=MemoryViewKind.CANONICAL,
        )
        for source_id in ("S1", "S3", "S7", "S8")
    )
    lossless = MemoryView(
        record_id="view:normalized-small-law",
        payload_hash=_sha("normalized small-angle law L=1m"),
        kind=MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(SourcePin("raw:S1", canonical[0].payload_hash),),
        transform_id="normalize:length_and_symbols:v1",
        required_canonical_ids=("raw:S1",),
        reconstruction_witness_id="w:lossless-normalization",
        reconstruction_verified=True,
    )
    lossy = MemoryView(
        record_id="view:target-summary",
        payload_hash=_sha("Earth 1m 20deg target with finite amplitude correction; source details elided"),
        kind=MemoryViewKind.DERIVED_LOSSY,
        source_pins=(
            SourcePin("raw:S1", canonical[0].payload_hash),
            SourcePin("raw:S3", canonical[1].payload_hash),
            SourcePin("raw:S7", canonical[2].payload_hash),
        ),
        transform_id="target_summary:v1",
        erasure_tags=("verbatim_source_text", "derivation_detail", "measurement_detail"),
        required_canonical_ids=("raw:S1", "raw:S3", "raw:S7"),
    )
    views = canonical + (lossless, lossy)
    assert validate_memory_view(lossless.record_id, views).valid
    assert validate_memory_view(lossy.record_id, views).valid
    return views


def _context_report():
    items = [
        ContextItem(
            record_id="view:target-summary",
            token_cost=34,
            coverage_atoms=("target", "earth", "period_law", "finite_correction"),
            fiber_ids=("F:target",),
            mandatory=True,
            compact_view=True,
            lossy=True,
            source_record_ids=("raw:S1", "raw:S3", "raw:S7"),
            erasure_tags=("verbatim_source_text", "derivation_detail", "measurement_detail"),
        ),
        ContextItem(
            record_id="raw:negative-mass",
            token_cost=18,
            coverage_atoms=("negative_mass_history",),
            fiber_ids=("F:target",),
            mandatory=True,
        ),
        ContextItem("raw:small-law", 28, ("period_law",), ("F:target",)),
        ContextItem("raw:finite-law", 28, ("period_law", "finite_correction"), ("F:target",)),
        ContextItem("raw:duplicate-small-law", 22, ("period_law",), ("F:target",)),
        ContextItem("raw:moon", 20, ("moon_context",), ("F:moon",)),
    ]
    for i in range(10):
        items.append(ContextItem(f"archive:distractor:{i:02d}", 12, (f"irrelevant:{i}",), ("F:other",), relevant=False))

    request = ContextCompileRequest(
        budget_tokens=64,
        target_fibers=("F:target",),
        required_coverage_atoms=("target", "earth", "period_law", "finite_correction", "negative_mass_history"),
    )
    return tuple(items), compile_epistemic_context(items, request)


def _saturation():
    tracker = SaturationTracker(
        required_routes=frozenset({"pendulum_known_answer"}),
        same_context_flat_required=1,
        independent_flat_required=1,
    )
    tracker.record(ResearchRound.from_objects(
        "R0", "pendulum_known_answer", "same_context", {"small_angle_period", "mass_independence", "small_angle_amplitude_independence", "moon_gravity_context", "mass_dependence", "mass_invariance_observation"}, source_ids=("S1", "S2", "S4", "S5", "S6", "S7"), evidence_lineage=("L1", "L2", "L4", "L5", "L6", "L7"), lineage_complete=True,
    ))
    tracker.record(ResearchRound.from_objects(
        "R1", "pendulum_known_answer", "same_context", {"small_angle_period", "mass_independence", "small_angle_amplitude_independence", "moon_gravity_context", "mass_dependence", "mass_invariance_observation", "finite_amplitude_correction"}, source_ids=("S3",), evidence_lineage=("L3",), lineage_complete=True,
    ))
    tracker.record(ResearchRound.from_objects(
        "R2", "pendulum_known_answer", "same_context", {"small_angle_period", "mass_independence", "small_angle_amplitude_independence", "moon_gravity_context", "mass_dependence", "mass_invariance_observation", "finite_amplitude_correction"}, source_ids=("S1", "S3"), evidence_lineage=("L1", "L3"), lineage_complete=True,
    ))
    tracker.record(ResearchRound.from_objects(
        "R3", "pendulum_known_answer", "independent_context", {"small_angle_period", "mass_independence", "small_angle_amplitude_independence", "moon_gravity_context", "mass_dependence", "mass_invariance_observation", "finite_amplitude_correction"}, independent=True, source_ids=("S8",), evidence_lineage=("L8",), lineage_complete=True,
    ))
    novelty = tuple((entry.research_round.round_id, len(entry.new_semantic_objects)) for entry in tracker.rounds)
    return tracker, novelty


def _atomic_trace():
    artifacts: list[ResearchArtifactRef] = []
    steps: list[ResearchStep] = []
    previous: str | None = None
    for index, contract in enumerate(stage_contracts()):
        output_id = f"trace:{index:02d}:{contract.stage.value.lower()}"
        lossy = contract.stage is ResearchStage.COMPILE_WORKING_CONTEXT
        artifacts.append(
            ResearchArtifactRef(
                artifact_id=output_id,
                kind=contract.typed_outputs[0],
                storage_tier=contract.storage_tier,
                source_ids=(("raw:S1", "raw:S3") if lossy else ()),
                canonical=(contract.storage_tier is StorageTier.TIER0_CANONICAL_ARCHIVE),
                lossy=lossy,
                erasure_tags=(("verbatim_source_text",) if lossy else ()),
            )
        )
        steps.append(
            ResearchStep(
                step_id=f"trace-step:{index:02d}",
                cycle_index=0,
                stage=contract.stage,
                input_ids=(() if previous is None else (previous,)),
                output_ids=(output_id,),
                llm_used=False,
                external_verification_observed=(True if contract.external_verification_required else False),
                mandatory_context_complete=(True if contract.stage is ResearchStage.COMPILE_WORKING_CONTEXT else None),
                raw_evidence_rehydrated=(True if contract.stage is ResearchStage.VERIFY_PROPOSAL else None),
                strong_authority_operation=(contract.stage is ResearchStage.VERIFY_PROPOSAL),
            )
        )
        previous = output_id
    return validate_research_trace(artifacts, steps)


def run_mini_research_demo() -> MiniResearchReceipt:
    sources = _sources()
    projections = _projections()
    canonical_keys = {projection.canonical_key for projection in projections}

    before = _base_lattice(include_finite=False)
    after = _base_lattice(include_finite=True)
    required = (KnowledgeAtomKind.REPRESENTATION, KnowledgeAtomKind.REGIME, KnowledgeAtomKind.QOI)
    before_paths = before.construct_paths(required)
    after_paths = after.construct_paths(required)

    views = _memory_views()
    view_counts = {
        kind: sum(view.kind is kind for view in views)
        for kind in MemoryViewKind
    }
    context_items, context_report = _context_report()
    archive_tokens = sum(item.token_cost for item in context_items)

    tracker, novelty = _saturation()
    trace = _atomic_trace()
    if trace.verdict is not TraceVerdict.VALID_SCOPED_TRACE:
        raise RuntimeError(f"internal demo trace invalid: {trace.reasons}")

    theta = math.radians(20.0)
    g = 9.80665
    t0 = 2.0 * math.pi * math.sqrt(1.0 / g)
    finite_first_order = t0 * (1.0 + theta * theta / 16.0)

    return MiniResearchReceipt(
        demo_id="PENDULUM_CONTEXT_ATLAS_001",
        target="1 m pendulum, 20 degree amplitude, Earth; first finite-amplitude approximation",
        target_period_seconds_first_order=round(finite_first_order, 6),
        raw_sources=len(sources),
        raw_payload_bytes=sum(len(source.text.encode("utf-8")) for source in sources),
        projected_claims=len(projections),
        canonical_claims_after_exact_identity_collapse=len(canonical_keys),
        context_distinct_noncollapsed_claims=3,
        atlas_atoms_before_new_evidence=len(before.atoms),
        atlas_atoms_after_new_evidence=len(after.atoms),
        typed_relation_witnesses_after_new_evidence=len(after.witnesses),
        apparent_contradictions_avoided_by_context_alignment=2,
        true_aligned_contradictions_or_refutations=1,
        negative_history_objects=1,
        blocking_epistemic_cuts_before_new_evidence=(1 if not before_paths else 0),
        blocking_epistemic_cuts_after_new_evidence=(1 if not after_paths else 0),
        target_support_paths_before_new_evidence=len(before_paths),
        target_support_paths_after_new_evidence=len(after_paths),
        archive_token_estimate=archive_tokens,
        active_context_tokens=context_report.used_tokens,
        active_to_archive_token_ratio=round(context_report.used_tokens / archive_tokens, 6),
        canonical_memory_views=view_counts[MemoryViewKind.CANONICAL],
        lossless_memory_views=view_counts[MemoryViewKind.DERIVED_LOSSLESS],
        lossy_memory_views=view_counts[MemoryViewKind.DERIVED_LOSSY],
        source_rehydration_roots=context_report.rehydration_record_ids,
        semantic_novelty_by_round=novelty,
        terminal_saturation_state=tracker.state.value,
        atomic_trace_verdict=trace.verdict.value,
        atomic_stages_registered=len(stage_contracts()),
        atomic_stages_executed_in_demo_trace=sum(count for _, count in trace.stage_counts),
        llm_calls_in_deterministic_demo=0,
        scientific_superiority_authority=False,
    )


def receipt_json(*, indent: int = 2) -> str:
    return json.dumps(asdict(run_mini_research_demo()), indent=indent, sort_keys=True) + "\n"


def main() -> int:
    print(receipt_json(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
