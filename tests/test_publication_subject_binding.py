from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "test.yml"


def test_publication_workflow_binds_builds_to_checked_out_subject():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'echo "RAKL_SUBJECT_SHA=$EXPECTED_SHA" >> "$GITHUB_ENV"' in text
    # The current publication workflow builds four exact-subject manuscripts:
    # V2.1, V2.2 framework, Epistemic Mechanics, and the Round-050 chaptered paper.
    assert text.count('--subject-sha "$RAKL_SUBJECT_SHA"') == 4
    assert '--subject-sha "$GITHUB_SHA"' not in text
    assert text.count("$RAKL_SUBJECT_SHA") >= 8
