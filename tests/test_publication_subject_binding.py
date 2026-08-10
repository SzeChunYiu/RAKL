from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "test.yml"


def test_publication_workflow_binds_builds_to_checked_out_subject():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'echo "RAKL_SUBJECT_SHA=$EXPECTED_SHA" >> "$GITHUB_ENV"' in text
    assert text.count('--subject-sha "$RAKL_SUBJECT_SHA"') == 3
    assert '--subject-sha "$GITHUB_SHA"' not in text
    assert r'\newcommand{\ImplementationSHA}{\texttt{$RAKL_SUBJECT_SHA}}' in text
