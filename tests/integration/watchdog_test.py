from nav.watchdog.util import get_statuses


def test_get_status_cache_does_not_raise():
    """Regression test for issue where pickle cache is poisoned from
    cross-environment testing - get_statuses() cache handling was bad
    """
    assert get_statuses()
