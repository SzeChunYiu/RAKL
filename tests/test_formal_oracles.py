from rakl.formal_oracles import (
    DynamicsClock,
    OracleVerdict,
    check_covariance_psd,
    check_local_identifiability,
    check_local_linear_stability,
    check_transition_matrix,
)


def test_local_identifiability_rank_condition():
    passed = check_local_identifiability(((1.0, 0.0), (0.0, 2.0), (1.0, 1.0)), parameter_count=2)
    failed = check_local_identifiability(((1.0, 2.0), (2.0, 4.0), (3.0, 6.0)), parameter_count=2)
    assert passed.verdict is OracleVerdict.PASS
    assert failed.verdict is OracleVerdict.FAIL


def test_continuous_2d_hurwitz_stability():
    stable = check_local_linear_stability(((-2.0, 0.5), (-0.2, -1.0)), clock=DynamicsClock.CONTINUOUS)
    unstable = check_local_linear_stability(((1.0, 0.0), (0.0, -1.0)), clock=DynamicsClock.CONTINUOUS)
    assert stable.verdict is OracleVerdict.PASS
    assert unstable.verdict is OracleVerdict.FAIL


def test_discrete_2d_jury_stability():
    stable = check_local_linear_stability(((0.5, 0.0), (0.0, 0.2)), clock=DynamicsClock.DISCRETE)
    unstable = check_local_linear_stability(((1.2, 0.0), (0.0, 0.2)), clock=DynamicsClock.DISCRETE)
    assert stable.verdict is OracleVerdict.PASS
    assert unstable.verdict is OracleVerdict.FAIL


def test_covariance_psd_and_transition_validity():
    assert check_covariance_psd(((1.0, 0.5), (0.5, 1.0))).verdict is OracleVerdict.PASS
    assert check_covariance_psd(((1.0, 2.0), (2.0, 1.0))).verdict is OracleVerdict.FAIL
    assert check_transition_matrix(((0.8, 0.2), (0.1, 0.9))).verdict is OracleVerdict.PASS
    assert check_transition_matrix(((0.8, 0.3), (0.1, 0.9))).verdict is OracleVerdict.FAIL
