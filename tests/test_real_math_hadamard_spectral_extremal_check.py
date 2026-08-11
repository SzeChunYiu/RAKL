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
    / "hadamard_spectral_extremal_check.py"
)
SPEC = importlib.util.spec_from_file_location("hadamard_spectral_extremal_check", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_exact_walsh_hadamard_gram_identity():
    for t in range(1, 6):
        assert mod.exact_hadamard_identity_check(t)


def test_sign_matrix_matches_odd_inner_product_contract():
    for t in range(1, 5):
        matrix = mod.inner_product_sign_matrix(t)
        n = 1 << t
        for x in range(n):
            for y in range(n):
                expected = 1 if ((x & y).bit_count() & 1) else -1
                assert matrix[x][y] == expected


def test_exact_spectral_ratio_is_sqrt_n():
    for t in range(1, 6):
        n = 1 << t
        numerator_squared, norm_squared = mod.spectral_ratio_squared_from_gram(t)
        assert numerator_squared == n * n
        assert norm_squared == n
        assert numerator_squared // norm_squared == n


def test_c012_bound_and_guards():
    assert mod.c012_cover_upper_bound(1) == 1
    assert mod.c012_cover_upper_bound(5) == 13
    for bad in (0, -1, 1.5, "3"):
        try:
            mod.inner_product_sign_matrix(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid width must fail closed")
