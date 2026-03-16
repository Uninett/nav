import warnings

from django.core.checks import ERROR
from django.core.checks import run_checks


def test_django_check_should_not_produce_errors():
    """Verify that Django's system checks pass without errors.

    Issues below ERROR are emitted as Python warnings so they remain visible in the
    pytest warning summary.
    """
    issues = run_checks()
    for issue in issues:
        if issue.level < ERROR:
            warnings.warn(str(issue), stacklevel=1)
    errors = [i for i in issues if i.level >= ERROR]
    assert not errors, f"Django system check errors: {errors}"
