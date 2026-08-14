"""Static conformance guard for Paper-I scientific-authority choke points.

This module does not decide scientific truth and grants no authority.  It audits
Python production source so new callers cannot silently bypass the registered
agent proposal gateway or the protected v3 scientific-authority mutation layer.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Tuple


@dataclass(frozen=True)
class ChokepointFinding:
    path: str
    line: int
    surface: str
    detail: str


@dataclass(frozen=True)
class ChokepointReport:
    files_checked: int
    findings: Tuple[ChokepointFinding, ...]

    @property
    def passed(self) -> bool:
        return not self.findings

    @property
    def grants_scientific_authority(self) -> bool:
        return False


DEFAULT_ALLOWLIST: Mapping[str, frozenset[str]] = {
    "AuthorityProposal_constructor": frozenset({"src/rakl/agent_authority_gateway.py"}),
    "promote_scientific_authority_call": frozenset({"src/rakl/agent_authority_gateway.py"}),
    "raw_agent_authority_parser_call": frozenset({"src/rakl/driver_learning.py"}),
    "AuthorityLedger_commit_verified_call": frozenset({"src/rakl/v3_scientific_authority.py"}),
    "AuthorityLedger_revoke_call": frozenset({"src/rakl/v3_scientific_authority.py"}),
    "AuthorityLedger_supersede_call": frozenset({"src/rakl/v3_scientific_authority.py"}),
}


def _dotted(node: ast.AST, imports: Mapping[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return imports.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value, imports)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def _imports(tree: ast.AST) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                out[item.asname or item.name.split(".")[0]] = item.name
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for item in node.names:
                if item.name == "*":
                    continue
                canonical = f"{module}.{item.name}" if module else item.name
                out[item.asname or item.name] = canonical
    return out


def _surface_for_call(node: ast.Call, imports: Mapping[str, str]) -> tuple[str, str] | None:
    target = _dotted(node.func, imports) or ""
    leaf = target.rsplit(".", 1)[-1]
    if leaf == "AuthorityProposal":
        return "AuthorityProposal_constructor", target
    if leaf == "promote_scientific_authority":
        return "promote_scientific_authority_call", target
    if leaf == "parse_raw_untrusted_agent_authority_json":
        return "raw_agent_authority_parser_call", target
    if leaf == "commit_verified":
        return "AuthorityLedger_commit_verified_call", target
    if leaf == "revoke":
        return "AuthorityLedger_revoke_call", target
    if leaf == "supersede":
        return "AuthorityLedger_supersede_call", target
    return None


def audit_source_tree(
    repository_root: str | Path,
    *,
    production_root: str = "src/rakl",
    allowlist: Mapping[str, frozenset[str]] = DEFAULT_ALLOWLIST,
) -> ChokepointReport:
    """Audit all Python files below ``production_root`` against registered choke points.

    The audit is deliberately syntax-based and fail-closed: an unparsable source
    file is a finding. Tests/fixtures are outside the production root and do not
    weaken the allowlist.  The raw-agent parser is also single-caller constrained
    so future production code cannot silently create a second model-output
    authority ingestion path with different framing semantics.
    """

    root = Path(repository_root)
    source_root = root / production_root
    findings: list[ChokepointFinding] = []
    files = sorted(source_root.rglob("*.py"))
    for path in files:
        rel = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        except (OSError, UnicodeError, SyntaxError) as exc:
            findings.append(ChokepointFinding(rel, 0, "source_parse", str(exc)))
            continue
        imports = _imports(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            classified = _surface_for_call(node, imports)
            if classified is None:
                continue
            surface, detail = classified
            if rel not in allowlist.get(surface, frozenset()):
                findings.append(
                    ChokepointFinding(rel, getattr(node, "lineno", 0), surface, detail)
                )
    return ChokepointReport(len(files), tuple(sorted(findings, key=lambda x: (x.path, x.line, x.surface))))


def format_findings(findings: Iterable[ChokepointFinding]) -> str:
    return "\n".join(
        f"{item.path}:{item.line}: {item.surface}: {item.detail}" for item in findings
    )
