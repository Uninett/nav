from mock import Mock, patch

from nav.web.auth.backends import NAVRemoteUserBackend
from nav.models.profiles import Account


class TestNAVRemoteUserBackend:
    def test_init_sets_create_unknown_user(self):
        expected = 6
        with patch(
            'nav.web.auth.backends.remote_user.will_autocreate_user',
            return_value=expected,
        ):
            backend = NAVRemoteUserBackend()
            assert backend.create_unknown_user == expected

    def test_authenticate_returns_None_if_backend_not_enabled(self):
        backend = NAVRemoteUserBackend()
        with patch(
            'nav.web.auth.backends.remote_user.is_remote_user_enabled',
            return_value=False,
        ):
            result = backend.authenticate(None, None)
            assert result is None

    def test_authenticate_returns_user_if_backend_is_enabled(self):
        expected = 7
        backend = NAVRemoteUserBackend()
        mock_backend = Mock()
        mock_backend.authenticate.return_value = expected
        with patch(
            'nav.web.auth.backends.remote_user.is_remote_user_enabled',
            return_value=True,
        ):
            with patch('builtins.super', return_value=mock_backend):
                result = backend.authenticate(None, expected)
                assert result == expected

    def test_clean_username_golden_path(self):
        # no need to test how clean_username works here‥
        username = 'bob'
        backend = NAVRemoteUserBackend()
        result = backend.clean_username(username)
        assert result == username

    def test_configure_user_when_not_created_returns_user_unchanged(self):
        user = 5
        backend = NAVRemoteUserBackend()
        result = backend.configure_user(None, user, created=False)
        assert result == user

    def test_configure_user_when_created_sets_ext_sync_and_adds_auditlog(self):
        account = Account(login="blbl", password="hgjg", ext_sync='')
        account.save = Mock()
        backend = NAVRemoteUserBackend()
        with patch('nav.web.auth.backends.LogEntry.add_log_entry') as auditlog:
            result = backend.configure_user(None, account, created=True)
            assert result.ext_sync == 'REMOTE_USER'
            assert result.is_active
            auditlog.assert_called_once()
            account.save.assert_called_once()

    def test_user_can_authenticate_if_user_is_active_returns_True(self):
        account = Account(login="blbl", password="hgjg")
        backend = NAVRemoteUserBackend()
        result = backend.user_can_authenticate(account)
        assert result == account.is_active == True  # noqa: E712

    def test_user_can_authenticate_if_user_is_not_active_returns_False_and_adds_auditlog(  # noqa: E501
        self,
    ):
        account = Account(login="blbl", password="!")
        backend = NAVRemoteUserBackend()
        with patch('nav.web.auth.backends.LogEntry.add_log_entry') as auditlog:
            result = backend.user_can_authenticate(account)
            assert result == account.is_active == False  # noqa: E712
            auditlog.assert_called_once()
