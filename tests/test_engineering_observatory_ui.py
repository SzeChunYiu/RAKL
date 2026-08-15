"""E11 item 7 — the Observatory UI, tested against its falsifier.

Falsifier: the UI recomputes its own epistemic score, or cannot drill from a
displayed claim back to exact source bytes.

The load-bearing test is `test_ui_displays_a_self_inconsistent_status_verbatim`:
a UI that quietly "corrects" what the service stored is exactly the defect this
fibre names, and the only way to catch it is to feed it a status that a
recomputing renderer could not resist fixing.
"""

from __future__ import annotations

import re

from rakl.engineering_observatory_ui import (
    NOT_STORED,
    render_observatory_html,
    render_observatory_json,
)
from rakl.engineering_ops import project_observatory

FULL_STATUS = {
    "project_id": "orion", "project_snapshot_id": "snap-7", "status_id": "st-7",
    "saturation_axes": {"knowledge": "SATURATED", "operators": "OPEN"},
    "route_coverage": {"required": 6, "covered": 6},
    "freshness": "FRESH",
    "residual_ids": ["res-1", "res-2"],
    "hard_gates": {"power": "PASS", "independence": "FAIL"},
    "controller_decision": "REFUSE_UNTIL_GATE_PASSES",
    "costs": {"solver_ms": 412},
    "workflow_states": {"wf-1": "RECOVERY_REQUIRED"},
    "provenance_ids": {
        "project_id": "project:orion", "snapshot_id": "snapshot:snap-7", "status_id": "status:st-7",
        "freshness": "status:st-7", "saturation_axes.knowledge": "receipt:r-11",
        "saturation_axes.operators": "receipt:r-12", "hard_gates.power": "receipt:r-13",
        "hard_gates.independence": "receipt:r-14", "controller_decision": "decision:d-3",
        "route_coverage.required": "route:rt-1", "route_coverage.covered": "route:rt-1",
        "costs.solver_ms": "run:run-9", "workflow_states.wf-1": "workflow:wf-1",
    },
}


def view(**over):
    return project_observatory({**FULL_STATUS, **over})


# --- the falsifier: never recompute ---------------------------------------


def test_ui_displays_a_self_inconsistent_status_verbatim() -> None:
    """Stored status says SATURATED while coverage is 1/6 and a gate FAILed.

    A renderer that computed anything would reconcile these. This one must show
    exactly what the service stored, contradictions included.
    """

    page = render_observatory_html(view(
        saturation_axes={"knowledge": "SATURATED"},
        route_coverage={"required": 6, "covered": 1},
        hard_gates={"power": "FAIL"},
        freshness="FRESH",
    ))
    assert "SATURATED" in page.html
    assert ">1<" in page.html or "1</span>" in page.html
    assert "FAIL" in page.html
    assert "FRESH" in page.html
    # nothing that looks like a derived correction appears
    assert "RECOMPUTED" not in page.html.upper()
    assert "CORRECTED" not in page.html.upper()


def test_module_exposes_no_computing_entry_point() -> None:
    import rakl.engineering_observatory_ui as ui

    assert not [n for n in dir(ui) if n.startswith(("compute", "score", "recompute", "derive", "evaluate"))]


def test_absent_field_is_not_stored_never_derived() -> None:
    page = render_observatory_html(project_observatory({"project_id": "p"}))
    assert NOT_STORED in page.html
    # an empty saturation map must not be rendered as if it were a computed verdict
    assert "SATURATED" not in page.html
    assert "OPEN" not in page.html


def test_stored_zero_is_distinct_from_not_stored() -> None:
    page = render_observatory_html(view(costs={"solver_ms": 0}))
    assert ">0<" in page.html or "0</span>" in page.html


# --- drill-down ------------------------------------------------------------


def test_every_displayed_field_with_a_provenance_id_links_to_it() -> None:
    v = view()
    page = render_observatory_html(v)
    for field, oid in v.provenance_ids.items():
        assert f"#obj-{oid}" in page.html, f"{field} does not link to {oid}"
        assert f'id="obj-{oid}"' in page.html, f"{oid} has no canonical object anchor"


def test_drill_down_reaches_exact_source_bytes() -> None:
    raw = '{"gate":"independence","verdict":"FAIL","p_value":0.31}'
    page = render_observatory_html(view(), source_bytes={"receipt:r-14": raw})
    assert "&quot;verdict&quot;:&quot;FAIL&quot;" in page.html or "verdict" in page.html
    assert "0.31" in page.html


def test_a_provenance_id_without_supplied_bytes_says_so_rather_than_hiding_it() -> None:
    page = render_observatory_html(view(), source_bytes={})
    assert "source bytes not supplied" in page.html


def test_unattributed_fields_are_marked_and_counted() -> None:
    page = render_observatory_html(view(provenance_ids={"project_id": "project:orion"}))
    assert page.unattributed_fields
    assert "unattributed" in page.html
    assert "carry no provenance id" in page.html
    # the no-alarm case: a fully attributed status must NOT raise the banner
    full = render_observatory_html(view())
    assert "carry no provenance id" not in full.html
    assert "Every displayed field carries a provenance id" in full.html


# --- the page cannot reach outside itself ---------------------------------


def test_page_has_no_scripts_and_no_external_requests() -> None:
    page = render_observatory_html(view(), source_bytes={"receipt:r-14": "<script>alert(1)</script>"})
    assert "<script" not in page.html.lower()
    assert not re.search(r"https?://", page.html)
    assert "fetch(" not in page.html and "XMLHttpRequest" not in page.html


def test_stored_content_is_escaped_not_executed() -> None:
    """The payload survives as inert text; what must not survive is an unescaped tag.

    `html.escape` renders `<img ...>` as `&lt;img ...&gt;`, a text node with no
    element for a browser to attach a handler to. So the assertion is on the
    absence of a real tag, not on the absence of the substring.
    """

    page = render_observatory_html(view(controller_decision="<img src=x onerror=alert(1)>"))
    assert "<img" not in page.html
    assert "&lt;img src=x onerror=alert(1)&gt;" in page.html


# --- the json projection ---------------------------------------------------


def test_json_projection_matches_and_declares_no_authority() -> None:
    import json

    data = json.loads(render_observatory_json(view()))
    assert data["saturation_axes"]["knowledge"] == "SATURATED"
    assert data["hard_gates"]["independence"] == "FAIL"
    assert data["grants_scientific_authority"] is False
    assert data["renderer_computes_nothing"] is True


def test_rendered_page_grants_no_scientific_authority() -> None:
    assert render_observatory_html(view()).grants_scientific_authority is False
