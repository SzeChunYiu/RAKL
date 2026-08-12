from __future__ import annotations

from enum import Enum


class FamilyId(str, Enum):
    SEQUENCE_COMPOSITION = "sequence_composition"
    BALANCE_CONSERVATION = "balance_conservation"
    STATE_REACHABILITY = "state_reachability"


class GoldLabel(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class ControlKind(str, Enum):
    NORMAL = "NORMAL"
    TEMPLATE_LEAK_PROBE = "TEMPLATE_LEAK_PROBE"
    COORDINATE_ABLATED_TWIN = "COORDINATE_ABLATED_TWIN"
    SEMANTIC_NEAR_DECOY = "SEMANTIC_NEAR_DECOY"


class StructuralCoordinate(str, Enum):
    PRINCIPLE = "PRINCIPLE"
    COMPOSITION = "COMPOSITION"
    BOUNDARY = "BOUNDARY"
    REPRESENTATION = "REPRESENTATION"
    DOMAIN_SHELL = "DOMAIN_SHELL"
    SURFACE_DETAIL = "SURFACE_DETAIL"
