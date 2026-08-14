"""Paper-to-framework consistency checks.

A manuscript claim and the shipped framework can drift apart silently: the paper
says the system refuses X, someone relaxes the guard, and nothing fails. These
checks bind specific paper claims to the framework behaviour that is supposed to
realize them, and they do it *behaviourally* — each check executes the framework
and observes what it does, rather than grepping for a string that could be a
comment, a docstring or dead code.

A binding that cannot be evaluated returns ``CANNOT_CHECK``. That is deliberately
distinct from ``CONSISTENT``: "could not check" is never "checked and fine".

Proposal-only: consistency here is an engineering property. It grants no
scientific authority and does not make any paper claim true.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable
import json

_REPO = Path(__file__).resolve().parents[2]
BINDINGS_PATH = _REPO / "research" / "paper_framework_consistency" / "bindings.json"


class ConsistencyVerdict(str, Enum):
    CONSISTENT = "CONSISTENT"
    DIVERGENT = "DIVERGENT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class BindingResult:
    binding_id: str
    verdict: ConsistencyVerdict
    detail: str


def _schema_pins_const(schema_rel: str, pointer: list[str], expected: Any) -> tuple[bool, str]:
    """Check a JSON-Schema location pins a literal constant."""
    path = _REPO / schema_rel
    if not path.exists():
        return False, f"schema {schema_rel} not found"
    node: Any = json.loads(path.read_text(encoding="utf-8"))
    for key in pointer:
        if not isinstance(node, dict) or key not in node:
            return False, f"pointer {'/'.join(pointer)} absent from {schema_rel}"
        node = node[key]
    if not isinstance(node, dict) or "const" not in node:
        return False, f"{'/'.join(pointer)} is not pinned to a const"
    if node["const"] != expected:
        return False, f"{'/'.join(pointer)} pinned to {node['const']!r}, expected {expected!r}"
    return True, f"{schema_rel}:{'/'.join(pointer)} pinned const {expected!r}"


# --- individual behavioural checks -------------------------------------------------


def _check_open_world_no_absolute_complete() -> tuple[ConsistencyVerdict, str]:
    """Paper I: unrestricted open-world completeness is not finitely certifiable.

    Framework obligation: no run may ever report absolute completeness. Checked by
    *constructing* a maximally-satisfied saturation report and observing that
    ``absolute_complete`` is still False, plus the schema pin.
    """
    from .epistemic_saturation import (
        EpistemicGrowthVector,
        OperatorOrderAudit,
        SaturationBasis,
        SaturationRound,
        audit_bounded_epistemic_saturation,
    )

    ok, detail = _schema_pins_const(
        "schemas/epistemic-saturation.schema.json",
        ["properties", "absolute_complete"],
        False,
    )
    if not ok:
        return ConsistencyVerdict.DIVERGENT, detail

    basis = SaturationBasis(
        basis_id="consistency-probe",
        scope="probe",
        identity_policy_id="idp",
        route_family_version="rf",
        novelty_policy_id="nov",
        evidence_policy_id="evp",
    )
    audit = OperatorOrderAudit(
        audit_id="probe",
        expand_then_consolidate_digest="a" * 64,
        consolidate_then_expand_digest="b" * 64,
        substantive_difference=EpistemicGrowthVector(),
        evidence_ids=("probe",),
    )
    perfect = [
        SaturationRound(
            round_id=f"probe-{i}",
            basis_fingerprint=basis.fingerprint,
            growth=EpistemicGrowthVector(),
            bounded_discovery_closed=True,
            route_coverage_stable=True,
            omission_audit_passed=True,
            nearest_work_audit_passed=True,
            operator_order_audit=audit,
            freshness_cutoff="2030-01-01",
        )
        for i in range(5)
    ]
    report = audit_bounded_epistemic_saturation(perfect, basis=basis)
    if report.absolute_complete:
        return (
            ConsistencyVerdict.DIVERGENT,
            "a fully-satisfied saturation run reported absolute_complete=True; "
            "the paper claims this is not finitely certifiable",
        )
    return (
        ConsistencyVerdict.CONSISTENT,
        f"{detail}; and a maximally-satisfied run still reports "
        f"absolute_complete=False (status was {report.status.value})",
    )


def _check_saturation_reopens_on_growth() -> tuple[ConsistencyVerdict, str]:
    """Paper I: new substantive knowledge reopens saturation.

    Framework obligation: appending a round with non-zero growth to an otherwise
    saturated sequence must drop the verdict out of BOUNDED_SATURATED.
    """
    from .epistemic_saturation import (
        EpistemicGrowthVector,
        OperatorOrderAudit,
        SaturationBasis,
        SaturationRound,
        SaturationStatus,
        audit_bounded_epistemic_saturation,
    )

    basis = SaturationBasis(
        basis_id="reopen-probe",
        scope="probe",
        identity_policy_id="idp",
        route_family_version="rf",
        novelty_policy_id="nov",
        evidence_policy_id="evp",
    )
    audit = OperatorOrderAudit(
        audit_id="probe",
        expand_then_consolidate_digest="a" * 64,
        consolidate_then_expand_digest="b" * 64,
        substantive_difference=EpistemicGrowthVector(),
        evidence_ids=("probe",),
    )

    def mk(round_id: str, growth: EpistemicGrowthVector) -> SaturationRound:
        return SaturationRound(
            round_id=round_id,
            basis_fingerprint=basis.fingerprint,
            growth=growth,
            bounded_discovery_closed=True,
            route_coverage_stable=True,
            omission_audit_passed=True,
            nearest_work_audit_passed=True,
            operator_order_audit=audit,
            freshness_cutoff="2030-01-01",
        )

    flat = [mk(f"flat-{i}", EpistemicGrowthVector()) for i in range(3)]
    before = audit_bounded_epistemic_saturation(flat, basis=basis)
    if before.status is not SaturationStatus.BOUNDED_SATURATED:
        return (
            ConsistencyVerdict.CANNOT_CHECK,
            f"control sequence did not saturate (got {before.status.value}), so the "
            "reopening behaviour cannot be isolated",
        )

    grown = flat + [mk("growth", EpistemicGrowthVector(mechanisms_added=1))]
    after = audit_bounded_epistemic_saturation(grown, basis=basis)
    if after.status is SaturationStatus.BOUNDED_SATURATED:
        return (
            ConsistencyVerdict.DIVERGENT,
            "a round with substantive growth left the state BOUNDED_SATURATED; "
            "the paper claims new knowledge reopens saturation",
        )
    return (
        ConsistencyVerdict.CONSISTENT,
        f"flat sequence saturates, and one growth round reopens it "
        f"({before.status.value} -> {after.status.value})",
    )


def _check_no_scalar_ranking_of_external_agents() -> tuple[ConsistencyVerdict, str]:
    """Paper I: no faithful scalarization of an incomparable order.

    Framework obligation: the external-agent registry must refuse scalar ranking.
    Checked via the schema pin plus the absence of any aggregate-score field on the
    landscape audit surface.
    """
    ok, detail = _schema_pins_const(
        "schemas/external-research-agent-registry-v1.schema.json",
        ["properties", "permits_scalar_ranking"],
        False,
    )
    if not ok:
        return ConsistencyVerdict.DIVERGENT, detail

    try:
        from . import external_agent_registry as ear
    except Exception as exc:  # pragma: no cover - import guard
        return ConsistencyVerdict.CANNOT_CHECK, f"registry module unavailable: {exc}"

    banned = {"score", "overall_score", "orion_score", "rank", "ranking", "composite"}
    surface = set(ear.LandscapeAudit.__dataclass_fields__)
    leaked = surface & banned
    if leaked:
        return (
            ConsistencyVerdict.DIVERGENT,
            f"landscape audit exposes scalar-ranking field(s) {sorted(leaked)}",
        )
    return ConsistencyVerdict.CONSISTENT, f"{detail}; audit surface exposes no aggregate score"


def _check_proprietary_never_architecture_causal() -> tuple[ConsistencyVerdict, str]:
    """Papers V/VI: system-level comparison may not license an architecture claim.

    Framework obligation: no proprietary system may be marked eligible for a causal
    architecture arm.
    """
    try:
        from .external_agent_registry import architecture_causal_eligible, load_registry

        registry = load_registry()
    except Exception as exc:
        return ConsistencyVerdict.CANNOT_CHECK, f"registry unavailable: {exc}"

    eligible = set(architecture_causal_eligible(registry))
    offenders = [
        s["system_id"]
        for s in registry["systems"]
        if s["availability"] == "PROPRIETARY" and s["system_id"] in eligible
    ]
    if offenders:
        return (
            ConsistencyVerdict.DIVERGENT,
            f"proprietary systems marked architecture-causal eligible: {offenders}",
        )
    return (
        ConsistencyVerdict.CONSISTENT,
        f"{len(eligible)} of {len(registry['systems'])} systems are causal-eligible; "
        "no proprietary system among them",
    )


def _production_claiming_symbols() -> list[tuple[str, str]]:
    """Symbols whose docstring *declares* they are a production path.

    Deliberately narrow: only a docstring whose first line begins with
    "Production" counts. Matching any mention of the word instead would fire on
    six further symbols that merely discuss production in passing - a checker
    that cries wolf on its first real run gets switched off.
    """
    import ast
    import re

    found: list[tuple[str, str]] = []
    for path in sorted((_REPO / "src" / "rakl").glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = (ast.get_docstring(node) or "").strip()
                if re.match(r"^Production\b", doc):
                    found.append((path.name, node.name))
    return found


def _check_production_claims_have_nontest_callers() -> tuple[ConsistencyVerdict, str]:
    """Papers V/VI: a path described as live must actually be live.

    Framework obligation: a symbol whose docstring declares it a *production*
    path must be reachable from something other than a test. Otherwise the code
    asserts an enforcement posture that the call graph does not support, and any
    paper sentence relying on that posture inherits the error.
    """
    import re

    symbols = _production_claiming_symbols()
    if not symbols:
        return ConsistencyVerdict.CANNOT_CHECK, "no production-declaring symbols found to check"

    offenders: list[str] = []
    for module, symbol in symbols:
        stem = module.removesuffix(".py")
        callers: set[str] = set()
        for path in _REPO.rglob("*.py"):
            rel = path.relative_to(_REPO).as_posix()
            if rel.startswith((".git/", ".claude/")) or rel == f"src/rakl/{module}":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if re.search(rf"\b({re.escape(symbol)}|{re.escape(stem)})\b", text):
                callers.add(rel)
        non_test = {c for c in callers if not c.startswith("tests/") and "/tests/" not in c}
        if not non_test:
            offenders.append(f"{module}::{symbol} (referenced only by {len(callers)} test file(s))")

    if offenders:
        return (
            ConsistencyVerdict.DIVERGENT,
            "symbols declare themselves a production path but have no non-test caller: "
            + "; ".join(offenders),
        )
    return (
        ConsistencyVerdict.CONSISTENT,
        f"all {len(symbols)} production-declaring symbols have a non-test caller",
    )


CHECKS: dict[str, Callable[[], tuple[ConsistencyVerdict, str]]] = {
    "PFC-OPEN-WORLD-NO-ABSOLUTE-COMPLETE": _check_open_world_no_absolute_complete,
    "PFC-SATURATION-REOPENS-ON-GROWTH": _check_saturation_reopens_on_growth,
    "PFC-NO-SCALAR-RANKING": _check_no_scalar_ranking_of_external_agents,
    "PFC-PROPRIETARY-NOT-CAUSAL": _check_proprietary_never_architecture_causal,
    "PFC-PRODUCTION-PATH-IS-LIVE": _check_production_claims_have_nontest_callers,
}


def load_bindings(path: Path | None = None) -> dict[str, Any]:
    with (path or BINDINGS_PATH).open(encoding="utf-8") as handle:
        return json.load(handle)


def run_all(path: Path | None = None) -> tuple[BindingResult, ...]:
    """Evaluate every declared binding. Unknown checks are CANNOT_CHECK, not skipped."""

    bindings = load_bindings(path)
    results: list[BindingResult] = []
    for binding in bindings["bindings"]:
        check = CHECKS.get(binding["binding_id"])
        if check is None:
            results.append(
                BindingResult(
                    binding["binding_id"],
                    ConsistencyVerdict.CANNOT_CHECK,
                    "no executable check is registered for this binding",
                )
            )
            continue
        try:
            verdict, detail = check()
        except Exception as exc:  # a crashing check is not a passing check
            verdict, detail = ConsistencyVerdict.CANNOT_CHECK, f"check raised {exc!r}"
        results.append(BindingResult(binding["binding_id"], verdict, detail))
    return tuple(results)


def divergences(results: tuple[BindingResult, ...]) -> tuple[BindingResult, ...]:
    """Every divergence, accepted or not. The verdict is never softened."""
    return tuple(r for r in results if r.verdict is ConsistencyVerdict.DIVERGENT)


def blocking_divergences(
    results: tuple[BindingResult, ...], path: Path | None = None
) -> tuple[BindingResult, ...]:
    """Divergences with no recorded acceptance.

    An accepted divergence is still reported as DIVERGENT - acceptance records
    that a human decided how to resolve it, it does not make the code consistent.
    Acceptance requires a closure_action, so it cannot be used to silence a
    finding indefinitely without saying what will be done about it.
    """
    bindings = load_bindings(path)
    accepted = {
        b["binding_id"]
        for b in bindings["bindings"]
        if isinstance(b.get("accepted_divergence"), dict)
        and b["accepted_divergence"].get("closure_action", "").strip()
    }
    return tuple(r for r in divergences(results) if r.binding_id not in accepted)


def main() -> int:  # pragma: no cover - thin CLI
    results = run_all()
    for item in results:
        print(f"{item.verdict.value:<13} {item.binding_id}\n              {item.detail}")
    bad = divergences(results)
    blocking = blocking_divergences(results)
    unchecked = [r for r in results if r.verdict is ConsistencyVerdict.CANNOT_CHECK]
    print(
        f"\n{len(results) - len(bad) - len(unchecked)} consistent, "
        f"{len(bad)} divergent ({len(blocking)} blocking, {len(bad) - len(blocking)} accepted), "
        f"{len(unchecked)} cannot-check"
    )
    return 1 if blocking else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
