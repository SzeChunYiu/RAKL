"""Verification in the loop: edge licensing backed by certificates, not assertion.

The solver's weakest node. Every edge in ``support_solver`` and ``derivation``
carries a ``licensed_at`` integer that was, until this module, *asserted* by
whoever built the structure. All three dead gates found on 2026-08-14 were
verification-layer failures of exactly this shape: a number that looked like a
check and was actually a claim.

Here an edge's authority is **derived from a certificate**, and a route or
derivation is re-verified against the live registry at use time:

* a certificate names its subject and its kind (kernel-checked proof, executable
  test, external label, or bare assertion);
* authority comes from an explicit ordinal *policy* over kinds — a declared
  governance choice, visibly not a measurement, with kernel-checked strictly
  above executable above external above asserted;
* verification runs the certificate's checker *now*: a checker that fails
  demotes the edge, and a checker that raises yields ``CANNOT_CHECK`` — never a
  pass. "Could not check" is not "checked and fine".

The real-data test binds certificates to the repository's own Lean development:
the checker re-parses ``formal/RaklFormal.lean`` for the named theorem, whose
axiom-freedom CI enforces. A poisoned certificate — a theorem name not in the
file — must demote its edge and block the derivation.

Proposal-only. A live certificate makes an edge's *license* honest; it does not
make any claim true.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum

from .derivation import DerivationDag, HyperEdge
from .support_solver import SupportEdge, SupportRoute


class CertificateKind(str, Enum):
    KERNEL_CHECKED = "KERNEL_CHECKED"
    EXECUTABLE_TEST = "EXECUTABLE_TEST"
    EXTERNAL_LABEL = "EXTERNAL_LABEL"
    ASSERTED = "ASSERTED"


class CertificateState(str, Enum):
    LIVE = "LIVE"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class Certificate:
    cert_id: str
    kind: CertificateKind
    subject: str
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.cert_id.strip() or not self.subject.strip():
            raise ValueError("certificate identity and subject are required")


@dataclass(frozen=True)
class AuthorityPolicy:
    """An explicit, ordinal mapping from certificate kind to authority.

    This is a declared governance choice, not a measurement, and it says so. The
    only structural requirement is the order: kernel-checked strictly above
    executable, above external, above asserted — an edge backed by a weaker kind
    must never outrank one backed by a stronger kind.
    """

    levels: Mapping[CertificateKind, int]

    def __post_init__(self) -> None:
        required = [
            CertificateKind.ASSERTED,
            CertificateKind.EXTERNAL_LABEL,
            CertificateKind.EXECUTABLE_TEST,
            CertificateKind.KERNEL_CHECKED,
        ]
        for kind in required:
            if kind not in self.levels:
                raise ValueError(f"policy must assign a level to {kind.value}")
        ordered = [self.levels[k] for k in required]
        if not all(a < b for a, b in zip(ordered, ordered[1:])):
            raise ValueError(
                "policy must be strictly increasing from ASSERTED to KERNEL_CHECKED"
            )

    def authority(self, kind: CertificateKind) -> int:
        return self.levels[kind]


#: The default ordinal policy: 0 < 1 < 2 < 3. Nothing about these integers is
#: tuned or empirical; only their ORDER carries meaning.
ORDINAL_POLICY = AuthorityPolicy(
    levels={
        CertificateKind.ASSERTED: 0,
        CertificateKind.EXTERNAL_LABEL: 1,
        CertificateKind.EXECUTABLE_TEST: 2,
        CertificateKind.KERNEL_CHECKED: 3,
    }
)


@dataclass
class CertificateRegistry:
    """Certificates plus the checkers that keep them honest."""

    _certs: dict[str, Certificate] = field(default_factory=dict)
    _checkers: dict[str, Callable[[Certificate], bool]] = field(default_factory=dict)

    def register(
        self, cert: Certificate, checker: Callable[[Certificate], bool]
    ) -> None:
        if cert.cert_id in self._certs:
            raise ValueError(f"certificate {cert.cert_id} already registered")
        self._certs[cert.cert_id] = cert
        self._checkers[cert.cert_id] = checker

    def get(self, cert_id: str) -> Certificate | None:
        return self._certs.get(cert_id)

    def verify(self, cert_id: str) -> CertificateState:
        """Run the checker NOW. A raising checker is CANNOT_CHECK, never LIVE."""
        cert = self._certs.get(cert_id)
        if cert is None:
            return CertificateState.UNKNOWN
        try:
            return (
                CertificateState.LIVE
                if self._checkers[cert_id](cert)
                else CertificateState.FAILED
            )
        except Exception:
            return CertificateState.CANNOT_CHECK


def certified_edge(
    source: str,
    target: str,
    cost: float,
    cert_id: str,
    registry: CertificateRegistry,
    *,
    policy: AuthorityPolicy = ORDINAL_POLICY,
) -> SupportEdge:
    """Build an edge whose license is DERIVED, never hand-set.

    A certificate that is not LIVE at construction yields an edge licensed at the
    ASSERTED floor — the edge exists (the claim was made) but carries no borrowed
    authority.
    """
    cert = registry.get(cert_id)
    if cert is not None and registry.verify(cert_id) is CertificateState.LIVE:
        level = policy.authority(cert.kind)
    else:
        level = policy.authority(CertificateKind.ASSERTED)
    return SupportEdge(source=source, target=target, cost=cost, licensed_at=level)


def certified_hyperedge(
    edge_id: str,
    premises: frozenset[str],
    conclusion: str,
    cert_id: str,
    registry: CertificateRegistry,
    *,
    cost: float = 1.0,
    policy: AuthorityPolicy = ORDINAL_POLICY,
) -> HyperEdge:
    """Hypergraph counterpart of :func:`certified_edge`."""
    cert = registry.get(cert_id)
    if cert is not None and registry.verify(cert_id) is CertificateState.LIVE:
        level = policy.authority(cert.kind)
    else:
        level = policy.authority(CertificateKind.ASSERTED)
    return HyperEdge(
        edge_id=edge_id,
        premises=premises,
        conclusion=conclusion,
        cost=cost,
        licensed_at=level,
    )


@dataclass(frozen=True)
class EdgeVerification:
    edge_label: str
    cert_id: str | None
    state: CertificateState


@dataclass(frozen=True)
class UseTimeVerification:
    """Re-verification of a route or derivation at the moment of use.

    ``certificate_backed`` demands every edge bound to a certificate that is LIVE
    *now*. An unbound edge, a failed checker, or a raising checker all deny it —
    each for a stated reason, each distinctly recorded.
    """

    edges: tuple[EdgeVerification, ...]
    certificate_backed: bool
    reasons: tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _verify_labels(
    labels: list[tuple[str, str | None]], registry: CertificateRegistry
) -> UseTimeVerification:
    results: list[EdgeVerification] = []
    reasons: list[str] = []
    for label, cert_id in labels:
        if cert_id is None:
            results.append(EdgeVerification(label, None, CertificateState.UNKNOWN))
            reasons.append(f"{label}: no certificate bound")
            continue
        state = registry.verify(cert_id)
        results.append(EdgeVerification(label, cert_id, state))
        if state is not CertificateState.LIVE:
            reasons.append(f"{label}: certificate {cert_id} is {state.value}")
    return UseTimeVerification(
        edges=tuple(results),
        certificate_backed=not reasons,
        reasons=tuple(reasons),
    )


def verify_route(
    route: SupportRoute,
    bindings: Mapping[tuple[str, str], str],
    registry: CertificateRegistry,
) -> UseTimeVerification:
    """Re-verify every edge of an OR-route against the live registry."""
    labels = [
        (f"{e.source}->{e.target}", bindings.get((e.source, e.target)))
        for e in route.edges
    ]
    return _verify_labels(labels, registry)


def verify_derivation(
    dag: DerivationDag,
    bindings: Mapping[str, str],
    registry: CertificateRegistry,
) -> UseTimeVerification:
    """Re-verify every fired hyperedge of a derivation against the live registry."""
    labels = [(e.edge_id, bindings.get(e.edge_id)) for e in dag.fired]
    return _verify_labels(labels, registry)
