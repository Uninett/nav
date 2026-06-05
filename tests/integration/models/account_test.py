import pytest
from django.db.utils import IntegrityError


def test_is_admin_should_return_true_when_user_is_admin(db, admin_account):
    assert admin_account.is_admin()


def test_is_admin_should_return_false_when_user_is_default_user(db, default_account):
    assert not default_account.is_admin()


def test_when_setting_is_active_true_for_default_account_then_it_should_fail(
    db, default_account
):
    default_account.is_active = True
    with pytest.raises(IntegrityError):
        default_account.save()
