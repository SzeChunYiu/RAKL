#!/usr/bin/env python3
"""
Telemetry audit tool for RAKL experiment results.

Schema version: orion-telemetry-audit-v1
grants_scientific_authority: false
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ArtifactCoverage:
    path: str
    present: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    uncomputable: List[str] = field(default_factory=list)
    coverage_fraction: float = 0.0
    
    def compute_coverage(self, required_fields: Set[str], total_fields: Set[str]):
        self.coverage_fraction = len(self.present) / len(total_fields) if total_fields else 0.0


@dataclass
class AuditReport:
    schema_version: str = "orion-telemetry-audit-v1"
    grants_scientific_authority: bool = False
    canonical_fields: List[str] = field(default_factory=list)
    per_artifact: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class TelemetryAuditor:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.schema = self._load_schema()
        self.canonical_fields = set(self.schema["fields"].keys())
        self._build_field_patterns()
    
    def _load_schema(self) -> Dict:
        schema_path = self.repo_root / "research/unified_problem_solving_v1/results/TELEMETRY_SCHEMA.json"
        if schema_path.exists():
            with open(schema_path) as f:
                return json.load(f)
        # Fallback import
        sys.path.insert(0, str(self.repo_root / "tools"))
        from telemetry_schema import get_schema_dict
        return get_schema_dict()
    
    def _build_field_patterns(self):
        self.field_patterns = {}
        for field_name, field_def in self.schema["fields"].items():
            patterns = [field_name]
            for example in field_def.get("examples", []):
                example_key = example.lower().replace("{", "").replace("}", "").replace("'", "").split(":")[0].strip()
                patterns.append(example_key)
            self.field_patterns[field_name] = patterns
    
    def _check_field_in_data(self, field_name: str, data: Dict) -> bool:
        patterns = self.field_patterns.get(field_name, [field_name])
        for key in data.keys():
            key_lower = key.lower()
            for pattern in patterns:
                if pattern.lower() in key_lower:
                    return True
        for v in data.values():
            if isinstance(v, dict):
                if self._check_field_in_data(field_name, v):
                    return True
            elif isinstance(v, list) and v:
                for item in v[:3]:
                    if isinstance(item, dict):
                        if self._check_field_in_data(field_name, item):
                            return True
        return False
    
    def audit_artifact(self, artifact_path: str) -> ArtifactCoverage:
        coverage = ArtifactCoverage(path=artifact_path)
        try:
            with open(artifact_path) as f:
                data = json.load(f)
        except Exception as e:
            coverage.present = [f"ERROR: {e}"]
            return coverage
        for field_name in self.canonical_fields:
            field_def = self.schema["fields"][field_name]
            requirement = field_def.get("requirement", "optional")
            if self._check_field_in_data(field_name, data):
                coverage.present.append(field_name)
            else:
                if requirement == "uncomputable":
                    coverage.uncomputable.append(field_name)
                else:
                    coverage.missing.append(field_name)
        coverage.compute_coverage(set(), self.canonical_fields)
        return coverage
    
    def scan_directory(self, directory: str) -> List[str]:
        paths = []
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"__pycache__", "node_modules"}]
            for file in files:
                if file.endswith(".json") and "receipt" not in file.lower():
                    paths.append(os.path.join(root, file))
        return paths
    
    def run_full_audit(self, scan_paths: List[str]) -> AuditReport:
        report = AuditReport()
        report.canonical_fields = list(self.canonical_fields)
        all_artifacts = []
        for scan_path in scan_paths:
            full_path = self.repo_root / scan_path
            if full_path.is_file():
                all_artifacts.append(str(full_path))
            elif full_path.is_dir():
                all_artifacts.extend(self.scan_directory(str(full_path)))
        artifact_reports = []
        coverage_values = []
        for artifact_path in sorted(all_artifacts):
            rel_path = os.path.relpath(artifact_path, self.repo_root)
            coverage = self.audit_artifact(artifact_path)
            artifact_reports.append({
                "path": rel_path,
                "present": sorted(coverage.present),
                "missing": sorted(coverage.missing),
                "uncomputable": sorted(coverage.uncomputable),
                "coverage_fraction": round(coverage.coverage_fraction, 3)
            })
            coverage_values.append(coverage.coverage_fraction)
        report.per_artifact = artifact_reports
        if coverage_values:
            report.summary = {
                "mean_coverage": round(sum(coverage_values) / len(coverage_values), 3),
                "n_artifacts": len(coverage_values),
                "worst_artifacts": self._get_extremes(artifact_reports, 5, False),
                "best_artifacts": self._get_extremes(artifact_reports, 5, True),
                "field_presence_rate": self._compute_field_presence(artifact_reports)
            }
        return report
    
    def _get_extremes(self, reports: List[Dict], n: int, best: bool) -> List[Dict]:
        sorted_reports = sorted(reports, key=lambda r: r["coverage_fraction"], reverse=best)
        return sorted_reports[:n]
    
    def _compute_field_presence(self, reports: List[Dict]) -> Dict[str, float]:
        field_counts = {f: 0 for f in self.canonical_fields}
        total = len(reports) if reports else 1
        for report in reports:
            for field in report["present"]:
                if field in field_counts:
                    field_counts[field] += 1
        return {f: round(field_counts[f] / total, 3) for f in self.canonical_fields}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Audit RAKL experiment telemetry")
    parser.add_argument("--repo-root", default="/home/billy/wt/i524")
    parser.add_argument("--scan-path", action="append", dest="scan_paths")
    parser.add_argument("--output", "-o")
    args = parser.parse_args()
    if not args.scan_paths:
        args.scan_paths = [
            "research/unified_problem_solving_v1/results",
            "research/paper2_closest_parent",
            "research/paper2_a3_a4_matched_empirical_156"
        ]
    auditor = TelemetryAuditor(args.repo_root)
    report = auditor.run_full_audit(args.scan_paths)
    output_data = {
        "schema_version": report.schema_version,
        "grants_scientific_authority": report.grants_scientific_authority,
        "canonical_fields": report.canonical_fields,
        "per_artifact": report.per_artifact,
        "summary": report.summary
    }
    if args.output:
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"Audit report written to {args.output}")
    else:
        print(json.dumps(output_data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
