from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import PermissionDenied

from nav.models.profiles import Account
from nav.web.auth.ldap import NoAnswerError
from nav.web.auth.ldap_auth_backend import LdapBackend


class TestAuthenticate:
    @patch('nav.web.auth.ldap_auth_backend.ldap.available', False)
    def test_given_ldap_not_available_return_none(self, db):
        assert (
            LdapBackend().authenticate(username="username", password="password") is None
        )

    @patch('nav.web.auth.ldap_auth_backend.ldap.available', True)
    def test_given_no_username_and_no_password_return_none(self, db):
        assert LdapBackend().authenticate() is None

    @patch('nav.web.auth.ldap_auth_backend.ldap.available', True)
    def test_given_user_without_ldap_sync_return_none(self, db, non_admin_account):
        assert (
            LdapBackend().authenticate(
                username=non_admin_account.login, password=non_admin_account.password
            )
            is None
        )

    @patch('nav.web.auth.ldap_auth_backend.ldap.available', True)
    @patch('nav.web.auth.ldap_auth_backend.ldap.authenticate')
    def test_given_valid_ldap_user_info_with_linked_nav_account_return_existing_nav_account(  # noqa
        self, mock_authenticate, db, ldap_synced_account, non_admin_ldap_user
    ):
        mock_authenticate.return_value = non_admin_ldap_user
        assert (
            LdapBackend().authenticate(
                username=ldap_synced_account.login,
                password=ldap_synced_account.password,
            )
            == ldap_synced_account
        )

    @patch('nav.web.auth.ldap_auth_backend.ldap.available', True)
    @patch('nav.web.auth.ldap_auth_backend.ldap.authenticate')
    def test_given_valid_ldap_user_info_without_linked_nav_account_create_nav_account(
        self, mock_authenticate, db, non_admin_ldap_user
    ):
        ldap_synced_accounts = list(Account.objects.filter(ext_sync="ldap"))
        mock_authenticate.return_value = non_admin_ldap_user
        new_nav_user = LdapBackend().authenticate(
            username="username",
            password="password",
        )
        assert new_nav_user
        assert new_nav_user not in ldap_synced_accounts
        assert new_nav_user.login == non_admin_ldap_user.username

    @patch('nav.web.auth.ldap_auth_backend.ldap.available', True)
    @patch('nav.web.auth.ldap_auth_backend.ldap.authenticate')
    def test_given_invalid_ldap_user_info_raise_permission_denied_exception(
        self, mock_authenticate, db, ldap_synced_account
    ):
        mock_authenticate.return_value = False

        with pytest.raises(PermissionDenied):
            LdapBackend().authenticate(
                username=ldap_synced_account.login,
                password=ldap_synced_account.password,
            )

    @patch('nav.web.auth.ldap_auth_backend.ldap.available', True)
    @patch('nav.web.auth.ldap_auth_backend.ldap.authenticate')
    def test_given_locked_nav_user_info_raise_permission_denied_exception(
        self, mock_authenticate, db, ldap_synced_account, non_admin_ldap_user
    ):
        mock_authenticate.return_value = non_admin_ldap_user
        ldap_synced_account.locked = True
        ldap_synced_account.save()

        with pytest.raises(PermissionDenied):
            LdapBackend().authenticate(
                username=ldap_synced_account.login,
                password=ldap_synced_account.password,
            )

    @patch('nav.web.auth.ldap_auth_backend.ldap.available', True)
    @patch('nav.web.auth.ldap_auth_backend.ldap.authenticate')
    def test_given_no_response_from_ldap_return_none(
        self,
        mock_authenticate,
        db,
        ldap_synced_account,
    ):
        mock_authenticate.side_effect = NoAnswerError
        assert (
            LdapBackend().authenticate(
                username=ldap_synced_account.login,
                password=ldap_synced_account.password,
            )
            is None
        )


class TestSyncNavAccount:
    def test_given_ldap_user_and_nav_account_updates_nav_account_password(
        self, db, non_admin_ldap_user, ldap_synced_account
    ):
        old_password = ldap_synced_account.password
        LdapBackend._sync_nav_account(
            non_admin_ldap_user, ldap_synced_account, "new_password"
        )
        ldap_synced_account.refresh_from_db()

        assert ldap_synced_account.password != old_password


class TestSyncNavAccountAdminPrivileges:
    def test_given_ldapuser_admin_adds_admin_group_to_nav_account(
        self, db, non_admin_account
    ):
        ldap_user = Mock()
        ldap_user.is_admin.return_value = True

        LdapBackend()._sync_nav_account_admin_privileges_from_ldap(
            ldap_user=ldap_user, nav_account=non_admin_account
        )

        non_admin_account.refresh_from_db()
        assert non_admin_account.is_admin()

    def test_given_ldap_user_not_admin_removes_admin_group_from_nav_account(
        self, db, admin_account
    ):
        ldap_user = Mock()
        ldap_user.is_admin.return_value = False

        LdapBackend()._sync_nav_account_admin_privileges_from_ldap(
            ldap_user=ldap_user, nav_account=admin_account
        )

        admin_account.refresh_from_db()
        assert not admin_account.is_admin()


@pytest.fixture
def ldap_synced_account(db):
    from nav.models.profiles import Account

    account = Account(login="ldap_user", name="LDAP User", ext_sync="ldap")
    account.set_password("password")
    account.save()
    yield account
    account.delete()


@pytest.fixture
def non_admin_ldap_user():
    ldap_user = Mock()
    ldap_user.username = "ldap_user"
    ldap_user.get_real_name.return_value = "LDAP User"
    ldap_user.is_admin.return_value = False

    yield ldap_user
