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
    / "quadratic_residue_polylog_upper.py"
)
SPEC = importlib.util.spec_from_file_location("quadratic_residue_polylog_upper", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_euler_predicate_matches_quadratic_residue_relation_exhaustively():
    for p in (3, 5, 7, 11, 19, 43, 59):
        assert mod.exhaustive_relation_check(p)


def test_zero_difference_is_not_an_edge():
    for p in (3, 11, 19, 43, 59):
        for x in range(p):
            assert not mod.qr_relation_via_euler(p, x, x)


def test_schedule_has_cubic_block_accounting_shape():
    for p in (3, 11, 19, 43, 59):
        schedule = mod.arithmetic_schedule(p)
        n = schedule.bit_width
        assert schedule.modular_add_calls_per_multiply_upper == 2 * n
        assert schedule.modular_multiply_calls_per_power_upper == 2 * n
        assert schedule.modular_add_calls_per_power_upper == 4 * n * n
