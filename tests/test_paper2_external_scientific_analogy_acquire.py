import csv
from io import StringIO
import json

from scripts.paper2_external_scientific_analogy_acquire import (
    MISSING_EVIDENCE_N,
    build_manifests,
    git_blob_sha,
)


def scar_fixture(n=14):
    rows=[]
    for i in range(1,n+1):
        rows.append(json.dumps({
            "id": i,
            "lang": "en",
            "system_a": f"A{i}",
            "system_b": f"B{i}",
            "mappings": [[f"a{i}",f"b{i}"]],
            "system_a_background": f"source a{i} mechanism",
            "system_b_background": f"target b{i} mechanism",
        }, sort_keys=True))
    return ("\n".join(rows)+"\n").encode()


def propara_fixture(n=70):
    out=StringIO()
    fields=[
        "source_paragraph","target_paragraph","relations",
        "distractor_target_paragraph","random_target_paragraph",
    ]
    writer=csv.DictWriter(out,fieldnames=fields)
    writer.writeheader()
    for i in range(n):
        writer.writerow({
            "source_paragraph": f"source process {i}",
            "target_paragraph": f"true target process {i}",
            "relations": f"(s{i},r,o{i}) like (t{i},r,u{i})",
            "distractor_target_paragraph": f"challenging distractor {i}",
            "random_target_paragraph": f"random target {i}",
        })
    return out.getvalue().encode()


def build_fixture():
    scar=scar_fixture()
    pro=propara_fixture()
    return build_manifests(
        scar,pro,
        expected_scar_blob=git_blob_sha(scar),
        expected_propara_blob=git_blob_sha(pro),
    )


def test_acquisition_applies_preview_quarantine_and_expands_paired_blocks():
    binding, public, gold=build_fixture()
    # SCAR ids 1..10 are quarantined: 4 remain. ProPara row indices 0..10
    # are quarantined: 59 remain; each expands true/challenging/random + 50 CC.
    assert binding["sources"]["SCAR"]["usable_rows"] == 4
    assert binding["sources"]["PROPARA_LOGY"]["usable_rows"] == 59
    assert len(public) == len(gold) == 4 + 59*3 + MISSING_EVIDENCE_N
    assert binding["cases"]["public_n"] == len(public)
    assert binding["cases"]["protected_n"] == len(gold)


def test_public_manifest_contains_no_gold_role_or_mapping_fields():
    _, public, gold=build_fixture()
    assert all(set(row)=={"case_id","source_text","target_text"} for row in public)
    assert any("gold_decision" in row for row in gold)
    assert any(row.get("gold_mappings") for row in gold if row["corpus"]=="SCAR")
    public_ids=[row["case_id"] for row in public]
    gold_ids=[row["case_id"] for row in gold]
    assert public_ids==gold_ids


def test_roles_are_balanced_by_construction_and_missing_evidence_is_protected():
    _, _, gold=build_fixture()
    roles={}
    for row in gold:
        roles[row["role"]]=roles.get(row["role"],0)+1
    assert roles["TRUE"]==59
    assert roles["CHALLENGING"]==59
    assert roles["RANDOM"]==59
    assert roles["MISSING_EVIDENCE"]==50
    assert all(row["gold_decision"]=="CANNOT_CHECK" for row in gold if row["role"]=="MISSING_EVIDENCE")


def test_exact_git_blob_identity_is_required():
    scar=scar_fixture(); pro=propara_fixture()
    try:
        build_manifests(
            scar,pro,
            expected_scar_blob="0"*40,
            expected_propara_blob=git_blob_sha(pro),
        )
    except ValueError as exc:
        assert "SCAR Git blob mismatch" in str(exc)
    else:
        raise AssertionError("mismatched source blob must fail closed")


def test_propara_schema_mismatch_fails_closed():
    scar=scar_fixture(); bad=b"wrong,columns\n1,2\n"
    try:
        build_manifests(
            scar,bad,
            expected_scar_blob=git_blob_sha(scar),
            expected_propara_blob=git_blob_sha(bad),
        )
    except ValueError as exc:
        assert "schema mismatch" in str(exc)
    else:
        raise AssertionError("schema mismatch must fail closed")


def test_case_order_and_hashes_are_deterministic():
    b1,p1,g1=build_fixture(); b2,p2,g2=build_fixture()
    assert p1==p2 and g1==g2
    assert b1["cases"]["public_manifest_sha256"]==b2["cases"]["public_manifest_sha256"]
    assert b1["cases"]["protected_gold_manifest_sha256"]==b2["cases"]["protected_gold_manifest_sha256"]
    assert b1["grants_scientific_authority"] is False
