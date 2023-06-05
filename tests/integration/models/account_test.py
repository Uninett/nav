from nav.models.profiles import Account

import pytest


def test_is_admin_returns_true_if_administrator(admin_user):
    assert admin_user.is_admin()


def test_is_admin_returns_false_if_default_account(default_user):
    assert not default_user.is_admin()


@pytest.fixture
def admin_user(postgresql):
    yield Account.objects.get(pk=Account.ADMIN_ACCOUNT)


@pytest.fixture
def default_user(postgresql):
    yield Account.objects.get(pk=Account.DEFAULT_ACCOUNT)
