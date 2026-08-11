from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "research"
    / "real_math"
    / "millennium"
    / "p_vs_np"
    / "05_falsification"
    / "jacobi_cover_spec.py"
)
SPEC = importlib.util.spec_from_file_location("jacobi_cover_spec", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_jacobi_matches_direct_qr_relation_exhaustively_on_small_primes():
    for p in (3, 5, 7, 11, 19, 43, 59):
        assert mod.exhaustive_relation_check(p)


def test_zero_difference_is_rejected():
    for p in (3, 5, 7, 11, 19, 43, 59):
        for x in range(p):
            assert mod.jacobi_symbol(0, p) == 0
            assert not mod.qr_relation_via_jacobi(p, x, x)


def test_jacobi_known_values_and_non_coprime_case():
    assert mod.jacobi_symbol(2, 3) == -1
    assert mod.jacobi_symbol(2, 7) == 1
    assert mod.jacobi_symbol(5, 11) == 1
    assert mod.jacobi_symbol(3, 9) == 0


def test_invalid_label_contract_fails_closed():
    for args in ((5, -1, 0), (5, 0, 5), (5, 5, 0)):
        try:
            mod.qr_relation_via_jacobi(*args)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid graph labels must fail closed")
