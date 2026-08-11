from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Tuple

from .breakthrough_learning import ExpertiseChunk
from .experience_substrate import ExperienceLedger, TaskEpisode
from .failure_lattice import FailureExperience, FailureExperienceLattice, query_related_failures
from .problem_solving_algebra import ProblemState, ResearchOperator
from .research_tool_inventory import ResearchTool, ResearchToolInventory, query_research_tools
from .strategy_motifs import MotifInstantiation, StrategyMotif, rank_strategy_motifs


@dataclass(frozen=True)
class ProblemAtom:
    atom_id: str
    goal: str
    context_hash: str
    structural_coordinates: Tuple[str, ...]
    desired_effects: Tuple[str, ...]
    dependencies: Tuple[str, ...] = ()
    interface_keys: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.atom_id or not self.goal or not self.context_hash:
            raise ValueError("problem atom requires id, goal, and context_hash")
        if not self.structural_coordinates:
            raise ValueError("problem atom requires structural coordinates")


@dataclass(frozen=True)
class ProblemDecomposition:
    problem_id: str
    atoms: Tuple[ProblemAtom, ...]

    def __post_init__(self) -> None:
        if not self.problem_id or not self.atoms:
            raise ValueError("problem decomposition requires problem_id and atoms")
        ids = [atom.atom_id for atom in self.atoms]
        if len(set(ids)) != len(ids):
            raise ValueError("problem decomposition atom ids must be unique")
        known = set(ids)
        for atom in self.atoms:
            missing = set(atom.dependencies) - known
            if missing:
                raise ValueError(f"atom {atom.atom_id} has unknown dependencies: {sorted(missing)}")
        visiting: set[str] = set()
        visited: set[str] = set()
        by_id = {atom.atom_id: atom for atom in self.atoms}

        def visit(atom_id: str) -> None:
            if atom_id in visited:
                return
            if atom_id in visiting:
                raise ValueError("problem decomposition dependencies must be acyclic")
            visiting.add(atom_id)
            for dependency in by_id[atom_id].dependencies:
                visit(dependency)
            visiting.remove(atom_id)
            visited.add(atom_id)

        for atom_id in ids:
            visit(atom_id)


@dataclass(frozen=True)
class FibreKnowledgeItem:
    item_id: str
    kind: str
    structural_signature: Tuple[str, ...]
    effects: Tuple[str, ...]
    context_tags: Tuple[str, ...]
    authority: str
    payload_hash: str

    def __post_init__(self) -> None:
        if not self.item_id or not self.kind or not self.payload_hash:
            raise ValueError("fibre knowledge item requires id, kind, and payload hash")


@dataclass(frozen=True)
class ProblemFibre:
    atom: ProblemAtom
    knowledge_items: Tuple[FibreKnowledgeItem, ...]
    tools: Tuple[ResearchTool, ...]
    episodes: Tuple[TaskEpisode, ...]
    failures: Tuple[FailureExperience, ...]
    motifs: Tuple[MotifInstantiation, ...]
    expertise_chunks: Tuple[ExpertiseChunk, ...]
    unresolved_warnings: Tuple[str, ...]
    snapshot_hash: str


@dataclass(frozen=True)
class LocalSection:
    section_id: str
    atom_id: str
    assignments: Tuple[Tuple[str, str], ...]
    assumptions: Tuple[str, ...]
    operator_ids: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]
    verified: bool = False

    def __post_init__(self) -> None:
        if not self.section_id or not self.atom_id:
            raise ValueError("local section requires section_id and atom_id")
        keys = [key for key, _ in self.assignments]
        if len(set(keys)) != len(keys):
            raise ValueError("local section assignment keys must be unique")


@dataclass(frozen=True)
class GluingObstruction:
    left_atom_id: str
    right_atom_id: str
    key: str
    left_value: str
    right_value: str
    reason: str


@dataclass(frozen=True)
class GluingReport:
    compatible: bool
    global_assignments: Tuple[Tuple[str, str], ...]
    obstructions: Tuple[GluingObstruction, ...]
    all_sections_verified: bool
    covered_atom_ids: Tuple[str, ...]

    @property
    def grants_solution_authority(self) -> bool:
        return self.compatible and self.all_sections_verified


def _score_knowledge(item: FibreKnowledgeItem, atom: ProblemAtom) -> int:
    score = 2 * len(set(item.structural_signature) & set(atom.structural_coordinates))
    score += 2 * len(set(item.effects) & set(atom.desired_effects))
    if atom.context_hash in item.context_tags:
        score += 3
    return score


def _score_episode(episode: TaskEpisode, atom: ProblemAtom) -> int:
    score = 2 * len(set(episode.problem_signature) & set(atom.structural_coordinates))
    score += len(set(episode.residual_signature) & set(atom.structural_coordinates))
    if episode.context_hash == atom.context_hash:
        score += 4
    return score


def _score_chunk(chunk: ExpertiseChunk, atom: ProblemAtom) -> int:
    return (
        2 * len(set(chunk.cue_signature) & set(atom.structural_coordinates))
        + 3 * len(set(chunk.deep_structure) & set(atom.structural_coordinates))
    )


def _snapshot_hash(*parts: object) -> str:
    payload = repr(parts).encode("utf-8")
    return sha256(payload).hexdigest()


def compile_problem_fibre(
    atom: ProblemAtom,
    *,
    knowledge_items: Iterable[FibreKnowledgeItem] = (),
    tool_inventory: ResearchToolInventory | None = None,
    failure_lattice: FailureExperienceLattice | None = None,
    experience_ledger: ExperienceLedger | None = None,
    strategy_motifs: Iterable[StrategyMotif] = (),
    operators: Iterable[ResearchOperator] = (),
    problem_state: ProblemState | None = None,
    expertise_chunks: Iterable[ExpertiseChunk] = (),
    candidate_method_families: Tuple[str, ...] = (),
    top_k_each: int = 12,
) -> ProblemFibre:
    """Compile the target-conditioned local problem-solving universe.

    The fibre is a derived working view.  It cannot promote evidence, lessons, or
    tools and it does not imply that co-retrieved items are mutually compatible.
    """

    if top_k_each < 1:
        raise ValueError("top_k_each must be positive")

    scored_knowledge = sorted(
        ((-_score_knowledge(item, atom), item.item_id, item) for item in knowledge_items if _score_knowledge(item, atom) > 0),
        key=lambda row: (row[0], row[1]),
    )
    selected_knowledge = tuple(item for _, _, item in scored_knowledge[:top_k_each])

    tools: Tuple[ResearchTool, ...] = ()
    if tool_inventory is not None:
        tools = query_research_tools(
            tool_inventory,
            structural_coordinates=atom.structural_coordinates,
            desired_effects=atom.desired_effects,
        )[:top_k_each]

    episodes: Tuple[TaskEpisode, ...] = ()
    if experience_ledger is not None:
        scored_episodes = sorted(
            ((-_score_episode(item, atom), item.episode_id, item) for item in experience_ledger.episodes if _score_episode(item, atom) > 0),
            key=lambda row: (row[0], row[1]),
        )
        episodes = tuple(item for _, _, item in scored_episodes[:top_k_each])

    failures: list[FailureExperience] = []
    if failure_lattice is not None:
        seen: set[str] = set()
        for method_family in candidate_method_families:
            for failure in query_related_failures(
                failure_lattice,
                method_family=method_family,
                residual_signature=atom.structural_coordinates,
            ):
                if failure.failure_id not in seen:
                    failures.append(failure)
                    seen.add(failure.failure_id)
                if len(failures) >= top_k_each:
                    break
            if len(failures) >= top_k_each:
                break

    motif_results: Tuple[MotifInstantiation, ...] = ()
    motifs = tuple(strategy_motifs)
    operator_tuple = tuple(operators)
    if problem_state is not None and motifs and operator_tuple:
        motif_results = rank_strategy_motifs(problem_state, motifs, operator_tuple)[:top_k_each]

    scored_chunks = sorted(
        ((-_score_chunk(chunk, atom), chunk.chunk_id, chunk) for chunk in expertise_chunks if _score_chunk(chunk, atom) > 0),
        key=lambda row: (row[0], row[1]),
    )
    selected_chunks = tuple(chunk for _, _, chunk in scored_chunks[:top_k_each])

    warnings: list[str] = []
    if not selected_knowledge:
        warnings.append("no_relevant_epistemic_item_found")
    if tool_inventory is not None and not tools:
        warnings.append("no_relevant_success_derived_tool_found")
    if failure_lattice is not None and candidate_method_families and not failures:
        warnings.append("no_relevant_failure_history_found")
    if experience_ledger is not None and not episodes:
        warnings.append("no_relevant_episode_found")
    if problem_state is not None and motifs and not motif_results:
        warnings.append("no_strategy_motif_instantiated")

    snapshot = _snapshot_hash(
        atom,
        tuple(item.item_id for item in selected_knowledge),
        tuple(item.tool_id for item in tools),
        tuple(item.episode_id for item in episodes),
        tuple(item.failure_id for item in failures),
        tuple(item.motif_id for item in motif_results),
        tuple(item.chunk_id for item in selected_chunks),
        tuple(warnings),
    )
    return ProblemFibre(
        atom=atom,
        knowledge_items=selected_knowledge,
        tools=tools,
        episodes=episodes,
        failures=tuple(failures),
        motifs=motif_results,
        expertise_chunks=selected_chunks,
        unresolved_warnings=tuple(warnings),
        snapshot_hash=snapshot,
    )


def glue_local_sections(
    decomposition: ProblemDecomposition,
    sections: Iterable[LocalSection],
) -> GluingReport:
    """Check whether local atom solutions form one compatible global section."""

    section_tuple = tuple(sections)
    by_atom = {section.atom_id: section for section in section_tuple}
    if len(by_atom) != len(section_tuple):
        raise ValueError("at most one selected local section per atom is allowed")
    known_atoms = {atom.atom_id for atom in decomposition.atoms}
    unknown = set(by_atom) - known_atoms
    if unknown:
        raise ValueError(f"sections reference unknown atoms: {sorted(unknown)}")

    obstructions: list[GluingObstruction] = []
    global_values: dict[str, tuple[str, str]] = {}
    for atom in decomposition.atoms:
        section = by_atom.get(atom.atom_id)
        if section is None:
            continue
        for dependency in atom.dependencies:
            if dependency not in by_atom:
                obstructions.append(
                    GluingObstruction(
                        left_atom_id=atom.atom_id,
                        right_atom_id=dependency,
                        key="__dependency__",
                        left_value="selected",
                        right_value="missing",
                        reason="dependent atom section is missing",
                    )
                )
        for key, value in section.assignments:
            previous = global_values.get(key)
            if previous is None:
                global_values[key] = (section.atom_id, value)
                continue
            previous_atom, previous_value = previous
            if previous_value != value:
                obstructions.append(
                    GluingObstruction(
                        left_atom_id=previous_atom,
                        right_atom_id=section.atom_id,
                        key=key,
                        left_value=previous_value,
                        right_value=value,
                        reason="local sections disagree on a shared interface assignment",
                    )
                )

    assignments = tuple(sorted((key, value) for key, (_, value) in global_values.items()))
    return GluingReport(
        compatible=not obstructions,
        global_assignments=assignments,
        obstructions=tuple(obstructions),
        all_sections_verified=bool(section_tuple) and all(section.verified for section in section_tuple),
        covered_atom_ids=tuple(sorted(by_atom)),
    )
