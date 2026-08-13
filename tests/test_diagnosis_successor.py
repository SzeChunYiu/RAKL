"""Tests for diagnosis_active_successor experiment."""

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULT_FILE = ROOT / "research" / "unified_problem_solving_v1" / "results" / "diagnosis_active_successor.json"


def test_result_file_exists():
    assert RESULT_FILE.exists()


def test_leakage_free_design():
    with open(RESULT_FILE) as f:
        data = json.load(f)
    assert data["design"]["leakage_free"] is True


def test_abstention_supported():
    with open(RESULT_FILE) as f:
        data = json.load(f)
    assert data["design"]["abstention_supported"] is True


def test_honest_status_reported():
    with open(RESULT_FILE) as f:
        data = json.load(f)
    assert "status" in data
    assert data["status"] in ["SUPPORTED", "PARTIAL", "NEGATIVE"]
