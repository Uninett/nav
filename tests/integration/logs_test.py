from nav.logs import reopen_log_files


def test_reopen_log_files_runs_without_error():
    """tests syntax regressions, not actual functionality"""
    assert reopen_log_files() is None
