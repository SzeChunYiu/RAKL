"""Additive v3 canonical commitment migration surface.

Historical ``state_fingerprint``/``state_fingerprint_v2`` values must not be
silently re-keyed.  This module introduces a third, explicitly versioned
commitment domain suitable for dual-write migration and cross-runtime replay.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .canonical_commitment import CanonicalProfile, UnicodePolicy, sha256_digest


@dataclass(frozen=True)
class ComponentCommitmentV3:
    name: str
    schema_version: str
    digest: str

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.schema_version.strip():
            raise ValueError("component identity/schema required")
        if not self.digest.startswith("sha256:") or len(self.digest) != 71 or any(ch not in "0123456789abcdef" for ch in self.digest[7:]):
            raise ValueError("component digest must be sha256:<64 lowercase hex>")


@dataclass(frozen=True)
class StateCommitmentV3:
    state_schema_version: str
    components: tuple[ComponentCommitmentV3, ...]
    sequence: int
    previous_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.state_schema_version.strip() or self.sequence < 0:
            raise ValueError("state schema and nonnegative sequence required")
        names = [c.name for c in self.components]
        if not names or names != sorted(names) or len(names) != len(set(names)):
            raise ValueError("components must be nonempty, unique, and sorted")
        if (self.sequence == 0) != (self.previous_digest is None):
            raise ValueError("predecessor presence must match initial/noninitial state")
        if self.previous_digest is not None and (
            not self.previous_digest.startswith("sha256:")
            or len(self.previous_digest) != 71
            or any(ch not in "0123456789abcdef" for ch in self.previous_digest[7:])
        ):
            raise ValueError("previous_digest must be sha256:<64 lowercase hex>")

    @property
    def digest(self) -> str:
        return sha256_digest(self, domain="rakl-v3-state-commitment/v3")


# Preserve exact Unicode scalar sequences in the state commitment. Any field that
# semantically requires NFC must validate that invariant at its own schema boundary;
# an integrity commitment should not silently rewrite or globally forbid older state.
STATE_PROFILE = CanonicalProfile(unicode_policy=UnicodePolicy.PRESERVE)


def commit_named_components_v3(
    state: Mapping[str, object],
    *,
    component_schema_versions: Mapping[str, str],
    state_schema_version: str,
    sequence: int,
    previous_digest: str | None = None,
) -> StateCommitmentV3:
    if set(state) != set(component_schema_versions):
        raise ValueError("component/schema key mismatch")
    components = tuple(
        ComponentCommitmentV3(
            name=name,
            schema_version=component_schema_versions[name],
            digest=sha256_digest(
                {"schema_version": component_schema_versions[name], "payload": state[name]},
                domain=f"rakl-v3-component/{name}/v3",
                profile=STATE_PROFILE,
            ),
        )
        for name in sorted(state)
    )
    return StateCommitmentV3(
        state_schema_version=state_schema_version,
        components=components,
        sequence=sequence,
        previous_digest=previous_digest,
    )


def state_commitment_v3(state: object, *, sequence: int = 0, previous_digest: str | None = None) -> StateCommitmentV3:
    """Commit the six current ``RAKLV3State`` coordinates without changing v1/v2.

    The function intentionally uses attribute access rather than importing the
    runtime class, avoiding a module cycle while failing loudly on incompatible
    state objects.
    """
    fields = ("experience", "tools", "failures", "saturation", "evolution", "scientific_authority")
    values = {name: getattr(state, name) for name in fields}
    # "current" is forbidden here: a commitment schema must not change meaning
    # when code advances. These names deliberately pin the migration subject.
    base = "3c24a9f78722ee5fa47ee3527e7e0e774aff91c6"
    schemas = {
        "experience": f"rakl.experience-ledger/python-value.v1@{base}",
        "tools": f"rakl.research-tool-inventory/python-value.v1@{base}",
        "failures": f"rakl.failure-lattice/python-value.v1@{base}",
        "saturation": f"rakl.saturation-vector/python-value.v1@{base}",
        "evolution": f"rakl.evolution-archive/python-value.v1@{base}",
        "scientific_authority": f"rakl.scientific-authority-projection/python-value.v1@{base}",
    }
    return commit_named_components_v3(
        values,
        component_schema_versions=schemas,
        state_schema_version=f"rakl-v3-state/v3-migration@{base}",
        sequence=sequence,
        previous_digest=previous_digest,
    )
