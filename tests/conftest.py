import pytest


@pytest.fixture(autouse=True)
def _reset_issued_root_cause_certificate_registry():
    """Isolate root-cause certificate collision registry across tests."""
    from rakl.search_policy_learning import _ISSUED_ROOT_CAUSE_RECORDS

    _ISSUED_ROOT_CAUSE_RECORDS.clear()
    yield
    _ISSUED_ROOT_CAUSE_RECORDS.clear()
