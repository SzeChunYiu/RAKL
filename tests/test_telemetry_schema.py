import sys
"""
Tests for telemetry schema and audit tool.

Schema version: orion-telemetry-audit-v1
grants_scientific_authority: false
"""

import json
import pytest
import tempfile
import os
from pathlib import Path

# Add tools to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))


class TestTelemetrySchema:
    """Test telemetry schema module."""
    
    def test_schema_loads(self):
        """Test that the schema module loads and exports correctly."""
        from telemetry_schema import get_schema_dict, CANONICAL_FIELDS
        
        schema = get_schema_dict()
        assert schema["schema_version"] == "orion-telemetry-v1"
        assert schema["grants_scientific_authority"] is False
        assert "fields" in schema
        assert len(schema["fields"]) >= 20  # Should have at least 20 canonical fields
        
        # Check specific required fields
        assert "verified_success" in schema["fields"]
        assert "wall_time_s" in schema["fields"]
        assert "tokens_in" in schema["fields"]
        assert "construction_cost" in schema["fields"]
    
    def test_schema_json_export_exists(self):
        """Test that the JSON schema export exists and is valid."""
        schema_path = Path(__file__).parent.parent / "research/unified_problem_solving_v1/results/TELEMETRY_SCHEMA.json"
        assert schema_path.exists()
        
        with open(schema_path) as f:
            schema = json.load(f)
        
        assert schema["schema_version"] == "orion-telemetry-v1"
        assert "fields" in schema
        assert len(schema["fields"]) >= 20
    
    def test_field_requirements(self):
        """Test that fields have proper requirement levels."""
        from telemetry_schema import get_schema_dict, FieldRequirement
        
        schema = get_schema_dict()
        fields = schema["fields"]
        
        # Check required fields
        assert fields["schema_version"]["requirement"] == "required"
        assert fields["grants_scientific_authority"]["requirement"] == "required"
        
        # Check uncomputable fields
        assert fields["cpu_time_s"]["requirement"] == "uncomputable"
        assert fields["gpu_time_s"]["requirement"] == "uncomputable"
        assert fields["ram_peak_mb"]["requirement"] == "uncomputable"
        assert fields["vram_peak_mb"]["requirement"] == "uncomputable"
        
        # Check optional fields
        assert fields["wall_time_s"]["requirement"] == "optional"
        assert fields["tokens_in"]["requirement"] == "optional"


class TestTelemetryAudit:
    """Test telemetry audit tool."""
    
    def test_auditor_instantiation(self):
        """Test that auditor can be instantiated."""
        from telemetry_audit import TelemetryAuditor
        
        repo_root = Path(__file__).parent.parent
        auditor = TelemetryAuditor(str(repo_root))
        
        assert auditor.schema is not None
        assert len(auditor.canonical_fields) >= 20
        assert "wall_time_s" in auditor.canonical_fields
    
    def test_auditor_detects_fields(self):
        """Test that auditor can detect fields in a simple artifact."""
        from telemetry_audit import TelemetryAuditor
        
        # Create a temporary artifact with known fields
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_data = {
                "schema_version": "test-v1",
                "grants_scientific_authority": False,
                "wall_time": 12.5,
                "construction_cost": {"mean": 0.12}
            }
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            repo_root = Path(__file__).parent.parent
            auditor = TelemetryAuditor(str(repo_root))
            coverage = auditor.audit_artifact(temp_path)
            
            # Should detect wall_time_s and construction_cost
            assert "wall_time_s" in coverage.present
            assert "construction_cost" in coverage.present
            assert "schema_version" in coverage.present
            assert "grants_scientific_authority" in coverage.present
            assert coverage.coverage_fraction > 0
        finally:
            os.unlink(temp_path)
    
    def test_auditor_handles_empty_artifact(self):
        """Test that auditor handles an empty/minimal artifact."""
        from telemetry_audit import TelemetryAuditor
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_data = {}
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            repo_root = Path(__file__).parent.parent
            auditor = TelemetryAuditor(str(repo_root))
            coverage = auditor.audit_artifact(temp_path)
            
            # Should have minimal coverage
            assert coverage.coverage_fraction < 0.2  # Less than 20% for empty artifact
        finally:
            os.unlink(temp_path)
    
    def test_auditor_detects_uncomputable_fields(self):
        """Test that auditor correctly categorizes uncomputable fields."""
        from telemetry_audit import TelemetryAuditor
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_data = {
                "schema_version": "test-v1",
                "grants_scientific_authority": False,
                "wall_time": 12.5
            }
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            repo_root = Path(__file__).parent.parent
            auditor = TelemetryAuditor(str(repo_root))
            coverage = auditor.audit_artifact(temp_path)
            
            # Uncomputable fields should be in that category
            assert "cpu_time_s" in coverage.uncomputable
            assert "gpu_time_s" in coverage.uncomputable
            assert "ram_peak_mb" in coverage.uncomputable
            assert "vram_peak_mb" in coverage.uncomputable
        finally:
            os.unlink(temp_path)


class TestAuditReport:
    """Test the complete audit report generation."""
    
    def test_audit_report_structure(self):
        """Test that audit report has expected structure."""
        from telemetry_audit import TelemetryAuditor
        
        repo_root = Path(__file__).parent.parent
        auditor = TelemetryAuditor(str(repo_root))
        
        # Run audit on a small subset
        test_path = repo_root / "research/unified_problem_solving_v1/results/TELEMETRY_SCHEMA.json"
        report = auditor.run_full_audit([str(test_path)])
        
        assert report.schema_version == "orion-telemetry-audit-v1"
        assert report.grants_scientific_authority is False
        assert len(report.canonical_fields) >= 20
        assert isinstance(report.per_artifact, list)
        assert "summary" in report.__dict__
    
    def test_known_good_artifact_scores_high(self):
        """Test that a known-good artifact (TELEMETRY_SCHEMA.json) scores high coverage."""
        from telemetry_audit import TelemetryAuditor
        
        repo_root = Path(__file__).parent.parent
        auditor = TelemetryAuditor(str(repo_root))
        
        test_path = repo_root / "research/unified_problem_solving_v1/results/TELEMETRY_SCHEMA.json"
        report = auditor.run_full_audit([str(test_path)])
        
        # TELEMETRY_SCHEMA.json should have high coverage (it defines all fields)
        assert len(report.per_artifact) == 1
        assert report.per_artifact[0]["coverage_fraction"] > 0.8  # At least 80%
        assert report.summary["mean_coverage"] > 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
