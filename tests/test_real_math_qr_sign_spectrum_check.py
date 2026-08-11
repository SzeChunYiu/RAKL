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
    / "qr_sign_spectrum_check.py"
)
SPEC = importlib.util.spec_from_file_location("qr_sign_spectrum_check", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_exact_character_and_qr_gram_identities_on_small_primes():
    for p in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31):
        assert mod.exact_identity_check(p)


def test_qr_sign_matrix_matches_edge_contract():
    for p in (3, 5, 7, 11, 13):
        matrix = mod.qr_sign_matrix(p)
        for x in range(p):
            for y in range(p):
                d = (y - x) % p
                expected = 1 if d != 0 and mod.quadratic_character(d, p) == 1 else -1
                assert matrix[x][y] == expected


def test_operator_norm_formula_branch_is_bound_to_prime_mod_four():
    for p in (3, 7, 11, 19, 23, 31):
        assert mod.predicted_operator_norm_squared(p) == ("integer", p + 1)
    for p in (5, 13, 17, 29):
        assert mod.predicted_operator_norm_squared(p) == ("sqrt_plus_one", p)


def test_nonprime_and_even_modulus_fail_closed():
    for p in (0, 1, 2, 9, 15, 21):
        try:
            mod.quadratic_character(1, p)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid modulus must fail closed")
