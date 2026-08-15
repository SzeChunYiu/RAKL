"""E11 item 7: the read-only ORION Observatory UI over the canonical service.

The falsifier this must survive: *the UI recomputes its own epistemic score, or
cannot drill from a displayed claim back to exact source bytes.*

So the design is defensive in one specific way. This module renders HTML from an
``ObservatoryView`` and **cannot compute an epistemic value even if asked to**:

  * it imports nothing that can compute saturation, freshness or a score;
  * every displayed value is stringified straight from the stored record;
  * a field the service did not store renders as the literal ``NOT STORED``,
    never as a default, an inference, or a value derived from siblings;
  * every displayed value that carries a provenance id renders as a link to the
    canonical object, and a value with NO provenance id is marked
    ``unattributed`` in the page itself rather than shown as if it were sourced.

That last rule is the one that makes the drill-down obligation real. A UI that
silently shows unattributed numbers looks identical to one whose every number is
sourced; marking them is what makes the difference visible to an operator.

The page is static HTML with no scripts and no external requests — a UI that
fetched anything at render time could show a number the stored status never
contained, which is the same defect by another route.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from typing import Mapping, Sequence

from .engineering_ops import ObservatoryView

# The service exposes provenance ids per displayed field. Anything not covered
# by that map is unattributed, and the page says so.
NOT_STORED = "NOT STORED"


@dataclass(frozen=True)
class RenderedPage:
    html: str
    displayed_fields: tuple[str, ...]
    unattributed_fields: tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _cell(view: ObservatoryView, field: str, value: object) -> tuple[str, bool]:
    """Render one value with its provenance link, or mark it unattributed.

    Returns (html, attributed). Never derives a value: an absent value is
    NOT STORED, which is visually distinct from a stored zero or empty set.
    """

    shown = NOT_STORED if value in (None, "", "UNKNOWN") else value
    oid = view.provenance_ids.get(field)
    if oid:
        link = (f'<a class="prov" href="#obj-{_esc(oid)}" title="canonical object {_esc(oid)}">'
                f"{_esc(oid)}</a>")
        return f'<span class="val">{_esc(shown)}</span> {link}', True
    return f'<span class="val">{_esc(shown)}</span> <span class="unattributed">unattributed</span>', False


def _rows(view: ObservatoryView, items: Sequence[tuple[str, object]]) -> tuple[str, list[str], list[str]]:
    out, displayed, unattributed = [], [], []
    for field, value in items:
        cell, attributed = _cell(view, field, value)
        displayed.append(field)
        if not attributed:
            unattributed.append(field)
        out.append(f"<tr><th>{_esc(field)}</th><td>{cell}</td></tr>")
    return "\n".join(out), displayed, unattributed


def _mapping_rows(view: ObservatoryView, prefix: str, mapping: Mapping[str, object]) -> tuple[str, list[str], list[str]]:
    if not mapping:
        return (f'<tr><th>{_esc(prefix)}</th><td><span class="val">{NOT_STORED}</span></td></tr>', [prefix], [prefix])
    return _rows(view, [(f"{prefix}.{k}", v) for k, v in sorted(mapping.items())])


STYLE = """
:root { --bg:#fbfbfd; --fg:#1c1c22; --line:#d8d8e0; --muted:#6a6a78;
        --warn:#8a4b00; --warnbg:#fff4e5; --chip:#eef0f6; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg:#14141a; --fg:#e8e8ef; --line:#2e2e3a; --muted:#9a9aab;
  --warn:#ffcf8a; --warnbg:#3a2a10; --chip:#22222c; } }
body { background:var(--bg); color:var(--fg); font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;
       margin:0; padding:24px; }
h1 { font-size:16px; margin:0 0 4px; letter-spacing:.02em; }
.sub { color:var(--muted); margin:0 0 20px; }
h2 { font-size:13px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted);
     margin:24px 0 8px; border-bottom:1px solid var(--line); padding-bottom:4px; }
table { border-collapse:collapse; width:100%; max-width:100%; }
th { text-align:left; font-weight:600; color:var(--muted); padding:4px 12px 4px 0;
     vertical-align:top; white-space:nowrap; }
td { padding:4px 0; }
.val { font-weight:600; }
.prov { color:var(--muted); text-decoration:none; border-bottom:1px dotted var(--line); font-size:12px; }
.unattributed { background:var(--warnbg); color:var(--warn); font-size:11px;
                padding:1px 6px; border-radius:3px; }
.note { background:var(--warnbg); color:var(--warn); padding:10px 12px; border-radius:4px;
        margin:16px 0; font-size:12px; }
.objects { margin-top:8px; }
.objects div { padding:6px 0; border-bottom:1px solid var(--line); }
.chip { background:var(--chip); padding:1px 6px; border-radius:3px; font-size:12px; }
.scroll { overflow-x:auto; }
"""


def render_observatory_html(view: ObservatoryView, *, source_bytes: Mapping[str, str] | None = None) -> RenderedPage:
    """Render the read-only page.

    ``source_bytes`` maps a canonical object id to its exact stored bytes, so a
    reader can drill from any displayed claim all the way down to what was
    written. Ids present in the view but absent from ``source_bytes`` are listed
    as unresolved rather than omitted — a missing source is information, not a
    reason to hide the row.
    """

    sections: list[str] = []
    all_displayed: list[str] = []
    all_unattributed: list[str] = []

    def add(title: str, rows_html: str, displayed: Sequence[str], unattributed: Sequence[str]) -> None:
        sections.append(f'<h2>{_esc(title)}</h2><div class="scroll"><table>{rows_html}</table></div>')
        all_displayed.extend(displayed)
        all_unattributed.extend(unattributed)

    add("identity", *_rows(view, [
        ("project_id", view.project_id),
        ("snapshot_id", view.snapshot_id),
        ("status_id", view.status_id),
        ("freshness", view.freshness),
    ]))
    add("saturation axes", *_mapping_rows(view, "saturation_axes", view.saturation_axes))
    add("route coverage", *_mapping_rows(view, "route_coverage", view.route_coverage))
    add("hard gates", *_mapping_rows(view, "hard_gates", view.hard_gates))
    add("controller", *_rows(view, [("controller_decision", view.controller_decision)]))
    add("costs", *_mapping_rows(view, "costs", view.costs))
    add("workflow / recovery states", *_mapping_rows(view, "workflow_states", view.workflow_states))

    residual_rows = "".join(
        f'<tr><th>residual[{i}]</th><td><span class="val">{_esc(r)}</span></td></tr>'
        for i, r in enumerate(view.residuals)
    ) or f'<tr><th>residuals</th><td><span class="val">{NOT_STORED}</span></td></tr>'
    sections.append(f'<h2>residuals / cuts / repairs</h2><div class="scroll"><table>{residual_rows}</table></div>')

    # drill-down: every provenance id, with its exact stored bytes when available
    sources = dict(source_bytes or {})
    drill: list[str] = []
    for field, oid in sorted(view.provenance_ids.items()):
        raw = sources.get(oid)
        body = (f"<pre>{_esc(raw)}</pre>" if raw is not None
                else '<span class="unattributed">source bytes not supplied to the renderer</span>')
        drill.append(f'<div id="obj-{_esc(oid)}"><span class="chip">{_esc(oid)}</span> '
                     f'&larr; {_esc(field)}{body}</div>')
    sections.append('<h2>canonical objects</h2><div class="objects">'
                    + ("".join(drill) or '<div>no provenance ids in this status</div>') + "</div>")

    banner = ""
    if all_unattributed:
        banner = (f'<div class="note">{len(all_unattributed)} displayed field(s) carry no provenance id and are '
                  f"marked unattributed. This page renders stored values only — it does not compute saturation, "
                  f"freshness or any epistemic score, and it does not fetch anything at render time.</div>")
    else:
        banner = ('<div class="note">Every displayed field carries a provenance id. This page renders stored '
                  "values only — it does not compute saturation, freshness or any epistemic score.</div>")

    page = (f"<title>Orion Observatory — {_esc(view.project_id)}</title>"
            f"<style>{STYLE}</style>"
            f"<h1>ORION OBSERVATORY</h1>"
            f'<p class="sub">project {_esc(view.project_id)} &middot; snapshot {_esc(view.snapshot_id)} '
            f"&middot; status {_esc(view.status_id)}</p>"
            f"{banner}" + "".join(sections))

    return RenderedPage(html=page, displayed_fields=tuple(all_displayed),
                        unattributed_fields=tuple(all_unattributed))


def render_observatory_json(view: ObservatoryView) -> str:
    """The same projection as data, for an operator piping it elsewhere."""

    return json.dumps({
        "project_id": view.project_id, "snapshot_id": view.snapshot_id, "status_id": view.status_id,
        "freshness": view.freshness, "saturation_axes": dict(view.saturation_axes),
        "route_coverage": dict(view.route_coverage), "residuals": list(view.residuals),
        "hard_gates": dict(view.hard_gates), "controller_decision": view.controller_decision,
        "costs": dict(view.costs), "workflow_states": dict(view.workflow_states),
        "provenance_ids": dict(view.provenance_ids),
        "grants_scientific_authority": False,
        "renderer_computes_nothing": True,
    }, indent=2, sort_keys=True)


__all__ = ["NOT_STORED", "RenderedPage", "render_observatory_html", "render_observatory_json"]
