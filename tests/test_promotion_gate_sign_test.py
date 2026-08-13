"""Sign-test promotion-gate evaluator: proves the six_family_law candidate is judged
on its OWN registered evidence (a binomial sign test), never by distorting it into a
fake net-metric CI.

Cases (a)-(g) prove the evaluator does not cry wolf:
  ALARM    = PROMOTE_TO_MECHANIC only when count-met AND p<alpha
  NO-ALARM = KEEP_PROPOSAL_ONLY when evidence is present but insufficient (never REJECT)
  CANNOT_CHECK when the artifact is missing or fails the mandatory authority disclaimer

The real research tree is never touched: every case writes its artifact under a
repo-local temp dir (the gate computes art.relative_to(ROOT), so the artifact must
live under ROOT; the temp dir is created and removed per-test).
"""
import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from promotion_gate import verdict_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

SIX_SPEC_TEMPLATE = {
    "artifact": None,  # filled per-test
    "net_keys": ["sign_test_p", "signs_positive"],  # parity with the real candidate
    "sign_test": {
        "p_keys": ["sign_test_p", "sign_test_p_two_sided"],
        "count_keys": ["all_six_positive", "n_positive"],
        "alpha": 0.05,
        "required_count": 6,
    },
    "cost_charged": True,
    "note": "cross-family generalization; sign test across >=6 families",
}


@pytest.fixture
def repo_tmp():
    """A per-test temp dir UNDER the repo root (cleaned up after the test).

    The gate calls art.relative_to(ROOT), so an out-of-tree tmp_path (pytest default
    /tmp/...) would crash; this keeps artifacts under ROOT without touching research/.
    """
    d = Path(tempfile.mkdtemp(prefix="gatetest_", dir=str(ROOT)))
    yield d
    shutil.rmtree(str(d), ignore_errors=True)


def _spec(repo_tmp: Path) -> dict:
    spec = copy.deepcopy(SIX_SPEC_TEMPLATE)
    spec["artifact"] = repo_tmp / "artifact.json"
    return spec


def _write(repo_tmp: Path, payload: dict) -> dict:
    spec = _spec(repo_tmp)
    spec["artifact"].write_text(json.dumps(payload))
    return spec


def _v(spec):
    return verdict_for("six_family_law", spec)


# (a) ALARM/PROMOTE: all six positive, p<alpha => PROMOTE_TO_MECHANIC
def test_a_promote_all_six_p_under_alpha(repo_tmp):
    spec = _write(repo_tmp, {
        "grants_scientific_authority": False,
        "all_six_positive": True,
        "n_positive": 6,
        "sign_test_p": 0.03125,
        "sign_test_p_two_sided": 0.03125,
    })
    v = _v(spec)
    assert v["verdict"] == "PROMOTE_TO_MECHANIC", v


# (b) NO-ALARM (count fails): 5/6 signs, tiny p => must NOT promote
def test_b_no_promote_count_fails(repo_tmp):
    spec = _write(repo_tmp, {
        "grants_scientific_authority": False,
        "all_six_positive": False,
        "n_positive": 5,
        "sign_test_p": 0.03125,
    })
    v = _v(spec)
    assert v["verdict"] == "KEEP_PROPOSAL_ONLY", v
    assert v["verdict"] != "REJECT", "non-significant sign test is weak evidence, not refutation"


# (c) NO-ALARM (p fails): all six positive but p>=alpha => must NOT promote
def test_c_no_promote_p_fails(repo_tmp):
    spec = _write(repo_tmp, {
        "grants_scientific_authority": False,
        "all_six_positive": True,
        "n_positive": 6,
        "sign_test_p": 0.125,
    })
    v = _v(spec)
    assert v["verdict"] == "KEEP_PROPOSAL_ONLY", v
    assert v["verdict"] != "REJECT", v


# (d) CANNOT_CHECK: artifact missing
def test_d_cannot_check_artifact_missing(repo_tmp):
    spec = _spec(repo_tmp)  # never written
    v = _v(spec)
    assert v["verdict"] == "CANNOT_CHECK", v
    assert v["reason"] == "evidence_artifact_missing", v


# (e) CANNOT_CHECK: authority disclaimer absent/true is mandatory
def test_e_cannot_check_authority_not_disclaimed(repo_tmp):
    spec = _write(repo_tmp, {
        # grants_scientific_authority omitted
        "all_six_positive": True,
        "n_positive": 6,
        "sign_test_p": 0.03125,
    })
    v = _v(spec)
    assert v["verdict"] == "CANNOT_CHECK", v
    assert v["reason"] == "artifact_does_not_disclaim_authority", v

    spec2 = _write(repo_tmp, {
        "grants_scientific_authority": True,
        "all_six_positive": True,
        "n_positive": 6,
        "sign_test_p": 0.03125,
    })
    v2 = _v(spec2)
    assert v2["verdict"] == "CANNOT_CHECK", v2


# (f) p under alpha, count read from n_positive=6 (bool absent) => PROMOTE (int path)
def test_f_promote_count_from_int_path(repo_tmp):
    spec = _write(repo_tmp, {
        "grants_scientific_authority": False,
        # all_six_positive intentionally absent: count must come from n_positive
        "n_positive": 6,
        "sign_test_p": 0.03125,
    })
    v = _v(spec)
    assert v["verdict"] == "PROMOTE_TO_MECHANIC", v


# (g) Extra guard: p unreadable => CANNOT_CHECK (never a fake pass)
def test_g_cannot_check_p_unreadable(repo_tmp):
    spec = _write(repo_tmp, {
        "grants_scientific_authority": False,
        "all_six_positive": True,
        "n_positive": 6,
        # no sign_test_p key at all
    })
    v = _v(spec)
    assert v["verdict"] == "CANNOT_CHECK", v
    assert v["reason"].startswith("sign_test_unreadable"), v
