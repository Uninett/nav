import pytest
from django.db.utils import IntegrityError

from nav.models.profiles import Account, AccountGroup, PrivilegeType


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


class TestHasPermWebAccess:
    @pytest.fixture
    def account_in_group(self, db):
        """An account whose only web access is what these tests grant it

        New accounts are automatically added to the "Everyone" and "Authenticated
        users" groups by a database trigger, and those grant web access to a range
        of URLs. Removing them keeps these tests from passing or failing on
        inherited privileges.
        """
        group = AccountGroup.objects.create(name="privilege test group")
        account = Account.objects.create(login="privilegetester", name="Privilege")
        account.groups.set([group])
        return account, group

    def _grant(self, group, privilege_name, target):
        group.privileges.create(
            type=PrivilegeType.objects.get(name=privilege_name), target=target
        )

    def test_when_a_target_is_an_invalid_regexp_it_should_not_raise_error(
        self, account_in_group
    ):
        """A malformed target must not make every page fail for the user"""
        account, group = account_in_group
        self._grant(group, "web_access", "*")
        # just see that it doesnt raise an error
        account.has_perm("web_access", "/portadmin/")

    def test_when_a_target_is_an_invalid_regexp_it_should_be_skipped(
        self, account_in_group
    ):
        """One broken grant must not stop the remaining ones from being evaluated"""
        account, group = account_in_group
        self._grant(group, "web_access", "*")
        self._grant(group, "web_access", r"^/(portadmin)/?")

        assert account.has_perm("web_access", "/portadmin/") is True

    def test_when_another_privilege_target_matches_everything_it_should_not_give_access(
        self, account_in_group
    ):
        """
        A non-web_access target must never be able to grant web access.
        This is tested because there was a bug where all privileges
        could give web access.
        """
        account, group = account_in_group
        self._grant(group, "alert_by", ".*")

        assert account.has_perm("web_access", "/useradmin/") is False

    def test_when_web_access_matches_it_should_give_access(self, account_in_group):
        account, group = account_in_group
        self._grant(group, "web_access", r"^/status/")

        assert account.has_perm("web_access", "/status/") is True

    def test_when_web_access_does_not_match_it_should_not_give_access(
        self, account_in_group
    ):
        account, group = account_in_group
        self._grant(group, "web_access", r"^/status/")

        assert account.has_perm("web_access", "/useradmin/") is False
