from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import shlex
import subprocess

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from paper.build_epistemic_mechanics import build_epistemic_mechanics_source
from review.paper1.external_solicitation.validate_response import validate_response_contract


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "review" / "paper1" / "external_solicitation"
MANIFEST_PATH = PACKET / "PACKET_MANIFEST.json"
SCHEMA_PATH = ROOT / "schemas" / "paper1-external-review-response.schema.json"
PACKET_SCHEMA_PATH = PACKET / "SCHEMA.json"
TEMPLATE_PATH = PACKET / "RESPONSE_TEMPLATE.json"

SUBJECT_SHA = "118b74c17606637a916fc0e1fea8db6508adb847"
SOURCE_SHA256 = "76c20f20e642939c10d6582a1a87233f172cbf7ee6a45f2dbdcdc4db35bee871"
BUILDER_SHA256 = "d52c1715b4e1519443a7cef6e26ff2d03f5a8e000bc6a2ae2db0f03ed13b981b"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _frozen_response() -> dict:
    response = deepcopy(_load(TEMPLATE_PATH))
    response["response_status"] = "frozen-external-reviewer-response"
    response["response_id"] = "P1-EXT-RESP-X001-R01"
    response["review_round"] = 1
    response["packet_manifest_sha256"] = _sha256(MANIFEST_PATH)
    reviewer = response["reviewer"]
    reviewer["pseudonymous_id"] = "P1-REVIEWER-X001"
    reviewer["concern_code"] = "X001"
    reviewer["expertise_summary"] = "Relevant formal-methods expertise"
    reviewer["affiliation_disclosure"] = "Privately verified by coordinator"
    reviewer["independence_basis"] = "No authorship, project role, or disclosed conflict"
    reviewer["independent_of_authors_and_project"] = True
    reviewer["conflicts"] = []
    reviewer["conflicts_disclosed"] = True
    reviewer["financial_interests_disclosed"] = True
    reviewer["prior_collaboration_disclosed"] = True
    reviewer["reviewer_asserts_independence_eligibility"] = True
    response["attestations"] = {key: True for key in response["attestations"]}
    response["chronology"]["author_response_first_accessed_at_utc"] = None
    response["chronology"]["other_reviewer_response_first_accessed_at_utc"] = None
    response["concerns"][0]["concern_id"] = "P1-EXT-FORMAL-X001-R01-001"
    response["concerns"][0]["exact_location"] = {
        "page": 1,
        "section": "Abstract",
        "locator_type": "paragraph",
        "locator": "paragraph 1",
        "quoted_anchor": "Epistemic Mechanics is introduced as an evidence governance method",
    }
    response["concerns"][0]["finding"] = "A concrete reviewer finding"
    response["concerns"][0]["requested_evidence_or_correction"] = "A concrete correction"
    response["overall_assessment"]["summary"] = "A concrete assessment"
    response["overall_assessment"]["strongest_contribution"] = "A concrete contribution"
    response["overall_assessment"]["most_serious_limitation"] = "A concrete limitation"
    response["review_evidence"] = {
        "claims_checked": ["Canonical state and authority transition contract"],
        "counterexample_search_summary": "Checked missing evidence, chronology reversal, and validator failure states.",
        "executable_correspondence_checked": True,
    }
    response["declaration"]["external_reviewer_response"] = True
    response["declaration"]["information_accurate_to_best_of_knowledge"] = True
    return response


def test_packet_is_explicitly_a_solicitation_and_closes_no_review_gate() -> None:
    manifest = _load(MANIFEST_PATH)

    assert manifest["artifact_status"] == "external-review-solicitation-only"
    assert manifest["claim_state"] == {
        "external_responses_received": 0,
        "independent_formal_review_completed": False,
        "independent_nearest_work_novelty_review_completed": False,
        "external_editorial_or_peer_review_completed": False,
        "accepted_or_published": False,
    }
    assert manifest["open_parent_concern_ids"] == ["P1-R50-INDEPENDENCE"]
    assert manifest["governance"]["solicitation_is_not_a_review"] is True
    assert manifest["governance"]["same_session_review_is_independent"] is False
    assert manifest["governance"]["response_implies_peer_review_acceptance"] is False

    readme = (PACKET / "README.md").read_text(encoding="utf-8").lower()
    assert "solicitation" in readme
    assert "not a completed review" in readme
    assert "not peer-review acceptance" in readme


def test_manifest_binds_exact_subject_source_builder_and_built_artifacts() -> None:
    manifest = _load(MANIFEST_PATH)
    subject = manifest["subject"]

    assert subject["git_sha"] == SUBJECT_SHA
    assert subject["source"] == {
        "path": "paper/epistemic_mechanics_round050/main.tex",
        "sha256": SOURCE_SHA256,
    }
    assert subject["builder"] == {
        "path": "paper/build_epistemic_mechanics.py",
        "sha256": BUILDER_SHA256,
        "entry_point": "build_epistemic_mechanics_source",
    }
    assert subject["build_parameters"] == {
        "subject_sha": SUBJECT_SHA,
        "software_tests": 840,
    }

    assert _sha256(ROOT / subject["source"]["path"]) == SOURCE_SHA256
    assert _sha256(ROOT / subject["builder"]["path"]) == BUILDER_SHA256

    staged = ROOT / subject["staged_source"]["path"]
    pdf = ROOT / subject["pdf"]["path"]
    assert _sha256(staged) == subject["staged_source"]["sha256"]
    assert _sha256(pdf) == subject["pdf"]["sha256"]
    assert pdf.read_bytes().startswith(b"%PDF-")
    assert subject["pdf"]["pages"] >= 20
    if shutil.which("pdfinfo"):
        info = subprocess.run(
            ["pdfinfo", str(pdf)], check=True, capture_output=True, text=True
        ).stdout
        pages = int(re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE).group(1))
        assert pages == subject["pdf"]["pages"]

    expected = build_epistemic_mechanics_source(
        subject_sha=SUBJECT_SHA,
        software_tests=840,
    )
    assert staged.read_text(encoding="utf-8") == expected


def test_rebase_and_build_receipts_record_observed_main_movement() -> None:
    manifest = _load(MANIFEST_PATH)
    observation = _load(PACKET / "BRANCH_OBSERVATION.json")
    build = _load(PACKET / "BUILD_RECEIPT.json")

    assert observation["worktree_creation_parent_sha"] == (
        "16c602245cdba89ff1109792b3ccd0b72a6ced93"
    )
    assert observation["schema_version"] == "paper1-branch-observation-v5"
    assert observation["latest_origin_main_sha"] == SUBJECT_SHA
    assert [item["observed_origin_main_sha"] for item in observation["observations"]] == [
        "69cadfd8cba5bd55cab52caab09c40c60c283a1b",
        "3f530a3311d2962362788508dae14e3ef84bd0fb",
        "9a44c5eee59dd95cec133dc8a99c1ba33ee3bddd",
        "f4cee8313ec64d02873b87f92c51c35c113cd70d",
        SUBJECT_SHA,
    ]
    assert observation["observations"][-1]["content_tree_changed"] is True
    assert observation["latest_diff_from_previous_base_was_empty"] is False
    assert observation["branch_moved_since_worktree_creation"] is True
    assert observation["post_rebase_head_matches_origin_main"] is True
    assert manifest["subject"]["branch_moved_before_packet_build"] is True
    assert build["subject_sha"] == SUBJECT_SHA
    assert build["software_test_evidence"]["passed"] == 840
    assert build["software_test_evidence"]["skipped"] == 4
    assert build["staged_source"]["sha256"] == manifest["subject"]["staged_source"][
        "sha256"
    ]
    assert build["render"]["pdf_sha256"] == manifest["subject"]["pdf"]["sha256"]
    assert build["reproducibility_boundary"]["byte_identical_pdf_rebuild_promised"] is False


def test_build_receipt_command_relationally_matches_manifest_parameters() -> None:
    manifest = _load(MANIFEST_PATH)
    build = _load(PACKET / "BUILD_RECEIPT.json")
    command = shlex.split(build["builder"]["command"])
    subject = manifest["subject"]
    parameters = subject["build_parameters"]

    assert build["source"] == subject["source"]
    assert {key: build["builder"][key] for key in ("path", "sha256")} == {
        key: subject["builder"][key] for key in ("path", "sha256")
    }
    assert command[:2] == ["python", subject["builder"]["path"]]
    assert command[command.index("--subject-sha") + 1] == parameters["subject_sha"]
    assert int(command[command.index("--software-tests") + 1]) == parameters["software_tests"]
    assert command[command.index("--output") + 1] == subject["staged_source"]["path"]
    assert build["software_test_evidence"]["passed"] == parameters["software_tests"]
    assert {key: build["staged_source"][key] for key in ("path", "sha256")} == subject[
        "staged_source"
    ]
    assert {
        "path": build["render"]["pdf_path"],
        "sha256": build["render"]["pdf_sha256"],
        "pages": build["render"]["pages"],
        "page_size": build["render"]["page_size"],
    } == subject["pdf"]


def test_manifest_inventory_is_content_bound_and_excludes_self_reference() -> None:
    manifest = _load(MANIFEST_PATH)
    inventory = manifest["packet_inventory"]
    paths = [item["path"] for item in inventory]

    assert "review/paper1/external_solicitation/PACKET_MANIFEST.json" not in paths
    assert len(paths) == len(set(paths))
    assert {
        "review/paper1/external_solicitation/README.md",
        "review/paper1/external_solicitation/FORMAL_METHODS_REVIEW.md",
        "review/paper1/external_solicitation/NOVELTY_PRIOR_ART_REVIEW.md",
        "review/paper1/external_solicitation/EDITORIAL_SIGNIFICANCE_REVIEW.md",
        "review/paper1/external_solicitation/RESPONSE_TEMPLATE.json",
        "review/paper1/external_solicitation/SCHEMA.json",
        "review/paper1/external_solicitation/validate_response.py",
        "review/paper1/external_solicitation/BUILD_RECEIPT.json",
        "review/paper1/external_solicitation/BRANCH_OBSERVATION.json",
        "review/paper1/external_solicitation/artifacts/main.tex",
        "review/paper1/external_solicitation/artifacts/main.pdf",
        "schemas/paper1-external-review-response.schema.json",
    } == set(paths)
    for item in inventory:
        assert _sha256(ROOT / item["path"]) == item["sha256"]
    assert PACKET_SCHEMA_PATH.read_bytes() == SCHEMA_PATH.read_bytes()


@pytest.mark.parametrize(
    ("filename", "lens", "namespace"),
    [
        ("FORMAL_METHODS_REVIEW.md", "formal_methods", "P1-EXT-FORMAL-"),
        ("NOVELTY_PRIOR_ART_REVIEW.md", "novelty_prior_art", "P1-EXT-NOVELTY-"),
        ("EDITORIAL_SIGNIFICANCE_REVIEW.md", "editorial_significance", "P1-EXT-EDITORIAL-"),
    ],
)
def test_review_forms_are_separate_solicitations_with_stable_ids(
    filename: str, lens: str, namespace: str
) -> None:
    manifest = _load(MANIFEST_PATH)
    form = (PACKET / filename).read_text(encoding="utf-8")
    lower = form.lower()

    assert any(
        track["lens"] == lens
        and track["form_path"] == f"review/paper1/external_solicitation/{filename}"
        and track["concern_namespace"] == namespace
        for track in manifest["requested_review_tracks"]
    )
    assert "solicitation" in lower
    assert "not a completed review" in lower
    assert "independence" in lower
    assert "conflict of interest" in lower
    assert "chronology" in lower
    assert "exact location" in lower
    assert namespace in form
    assert "P1-EXT-ARTIFACT-" in form
    assert re.search(rf"{re.escape(namespace)}[A-Z0-9]{{4}}-R\d{{2}}-\d{{3}}", form)
    assert "independent review completed" not in lower
    assert "peer review completed" not in lower


def test_response_template_validates_and_binds_review_chronology() -> None:
    response = _load(TEMPLATE_PATH)
    _validator().validate(response)
    manifest = _load(MANIFEST_PATH)

    assert response["packet_id"] == manifest["packet_id"]
    assert response["response_status"] == "template-example-not-submitted"
    assert response["packet_manifest_sha256"] == "0" * 64
    assert manifest["template_placeholders"]["packet_manifest_sha256"] == (
        "replace_zero_hash_with_sha256_of_final_packet_manifest"
    )
    assert response["artifact_binding"]["manuscript_subject_sha"] == SUBJECT_SHA
    assert response["artifact_binding"]["staged_source_sha256"] == manifest["subject"][
        "staged_source"
    ]["sha256"]
    assert response["artifact_binding"]["pdf_sha256"] == manifest["subject"]["pdf"][
        "sha256"
    ]
    assert response["attestations"]["no_author_response_access_before_freeze"] is False
    assert response["declaration"]["external_reviewer_response"] is False
    assert response["declaration"]["peer_review_acceptance"] is False

    chronology = response["chronology"]
    accessed = datetime.fromisoformat(chronology["artifact_accessed_at_utc"].replace("Z", "+00:00"))
    frozen = datetime.fromisoformat(chronology["response_frozen_at_utc"].replace("Z", "+00:00"))
    signed = datetime.fromisoformat(chronology["attestation_signed_at_utc"].replace("Z", "+00:00"))
    assert accessed <= frozen <= signed


def test_frozen_response_cannot_reuse_template_placeholders() -> None:
    response = deepcopy(_load(TEMPLATE_PATH))
    response["response_status"] = "frozen-external-reviewer-response"

    errors = list(_validator().iter_errors(response))
    assert errors
    messages = "\n".join(error.message for error in errors)
    assert "0000000000000000000000000000000000000000000000000000000000000000" in messages
    assert "EXAMPLE ONLY" in messages


@pytest.mark.parametrize("conflict_mode", ["not_independent", "conflict_listed"])
def test_independence_eligibility_self_attestation_is_internally_consistent(
    conflict_mode: str,
) -> None:
    response = _frozen_response()
    if conflict_mode == "not_independent":
        response["reviewer"]["independent_of_authors_and_project"] = False
    else:
        response["reviewer"]["conflicts"] = ["Disclosed authorship conflict"]

    errors = validate_response_contract(response, require_frozen=True)
    assert errors
    assert any("independence" in error for error in errors)


def test_runtime_rejects_reversed_chronology_and_postfreeze_access_before_freeze() -> None:
    response = _frozen_response()
    response["chronology"]["artifact_accessed_at_utc"] = "2026-08-10T11:00:00Z"
    response["chronology"]["response_frozen_at_utc"] = "2026-08-10T10:00:00Z"
    response["chronology"]["author_response_first_accessed_at_utc"] = "2026-08-10T09:00:00Z"

    errors = validate_response_contract(response, require_frozen=True)
    assert any("accessed <= frozen <= signed" in error for error in errors)
    assert any("author response access" in error for error in errors)


def test_runtime_accepts_correctly_bound_frozen_response_without_minting_authority() -> None:
    response = _frozen_response()
    _validator().validate(response)

    assert validate_response_contract(response, require_frozen=True) == []


@pytest.mark.parametrize(
    "mutation", ["arbitrary_manifest_hash", "arbitrary_artifact_hash", "lens_role_mismatch", "reviewer_code_mismatch"]
)
def test_runtime_rejects_packet_artifact_role_and_reviewer_binding_mutations(
    mutation: str,
) -> None:
    response = _frozen_response()
    if mutation == "arbitrary_manifest_hash":
        response["packet_manifest_sha256"] = "b" * 64
    elif mutation == "arbitrary_artifact_hash":
        response["artifact_binding"]["staged_source_sha256"] = "c" * 64
    elif mutation == "lens_role_mismatch":
        response["reviewer"]["role"] = "novelty_prior_art_reviewer"
    else:
        response["reviewer"]["pseudonymous_id"] = "P1-REVIEWER-Z999"

    errors = validate_response_contract(response, require_frozen=True)
    assert errors
    assert any("binding" in error or "role" in error or "pseudonymous" in error for error in errors)


@pytest.mark.parametrize("mode", ["duplicate", "dangling", "omitted"])
def test_runtime_rejects_invalid_concern_relationships(mode: str) -> None:
    response = _frozen_response()
    concern = deepcopy(response["concerns"][0])
    concern["severity"] = "blocking"
    response["concerns"][0] = concern
    response["overall_assessment"]["blocking_concern_ids"] = [concern["concern_id"]]
    if mode == "duplicate":
        duplicate = deepcopy(concern)
        duplicate["finding"] = "Different body with same identifier"
        response["concerns"].append(duplicate)
    elif mode == "dangling":
        response["overall_assessment"]["blocking_concern_ids"].append(
            "P1-EXT-FORMAL-X001-R01-999"
        )
    else:
        response["overall_assessment"]["blocking_concern_ids"] = []

    errors = validate_response_contract(response, require_frozen=True)
    assert errors
    assert any("concern" in error or "blocking" in error for error in errors)


@pytest.mark.parametrize(
    ("mutation", "expected_fragment"),
    [
        ("missing_artifact_binding", "artifact_binding"),
        ("missing_coi_attestation", "conflicts_disclosed"),
        ("author_response_visible", "True was expected"),
        ("missing_concern_location", "too short"),
        ("wrong_lens_namespace", "does not match"),
    ],
)
def test_response_schema_fails_closed_on_missing_evidence(
    mutation: str, expected_fragment: str
) -> None:
    response = _frozen_response()
    _validator().validate(response)
    if mutation == "missing_artifact_binding":
        del response["artifact_binding"]
    elif mutation == "missing_coi_attestation":
        del response["attestations"]["conflicts_disclosed"]
    elif mutation == "author_response_visible":
        response["attestations"]["no_author_response_access_before_freeze"] = False
    elif mutation == "missing_concern_location":
        response["concerns"][0]["exact_location"]["quoted_anchor"] = ""
    elif mutation == "wrong_lens_namespace":
        response["concerns"][0]["concern_id"] = "P1-EXT-EDITORIAL-X001-R01-001"
    else:  # pragma: no cover - protects the parametrization itself
        raise AssertionError(mutation)

    errors = sorted(_validator().iter_errors(response), key=lambda error: list(error.path))
    assert errors
    assert expected_fragment in "\n".join(error.message for error in errors)
