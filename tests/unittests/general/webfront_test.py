# -*- coding: utf-8 -*-
from mock import patch, MagicMock, Mock
from django.test import RequestFactory

from nav.web import auth
from nav.web.auth import remote_user
from nav.web.auth.utils import ACCOUNT_ID_VAR

LDAP_ACCOUNT = auth.Account(login='knight', ext_sync='ldap', password='shrubbery')
PLAIN_ACCOUNT = auth.Account(login='knight', password='shrubbery')
REMOTE_USER_ACCOUNT = auth.Account(
    login='knight', ext_sync='REMOTE_USER', password='shrubbery'
)


@patch("nav.web.auth.Account.save", new=MagicMock(return_value=True))
@patch("nav.web.auth.Account.objects.get", new=MagicMock(return_value=LDAP_ACCOUNT))
class TestLdapAuthenticate(object):
    def test_authenticate_should_return_account_when_ldap_says_yes(self):
        ldap_user = Mock()
        ldap_user.is_admin.return_value = None  # mock to avoid database access
        with patch("nav.web.auth.ldap.available", new=True):
            with patch("nav.web.auth.ldap.get_ldap_user", return_value=ldap_user):
                assert auth.authenticate('knight', 'shrubbery') == LDAP_ACCOUNT

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        with patch("nav.web.auth.ldap.available", new=True):
            with patch("nav.web.auth.ldap.get_ldap_user", return_value=False):
                assert not auth.authenticate('knight', 'shrubbery')

    def test_authenticate_should_fallback_when_ldap_is_disabled(self):
        with patch("nav.web.auth.ldap.available", new=False):
            assert auth.authenticate('knight', 'shrubbery') == LDAP_ACCOUNT


@patch("nav.web.auth.Account.save", new=MagicMock(return_value=True))
@patch("nav.web.auth.Account.objects.get", new=MagicMock(return_value=PLAIN_ACCOUNT))
@patch("nav.web.auth.ldap.available", new=False)
class TestNormalAuthenticate(object):
    def test_authenticate_should_return_account_when_password_is_ok(self):
        with patch("nav.web.auth.Account.check_password", return_value=True):
            assert auth.authenticate('knight', 'shrubbery') == PLAIN_ACCOUNT

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        with patch("nav.web.auth.Account.check_password", return_value=False):
            assert not auth.authenticate('knight', 'rabbit')


class TestRemoteUserAuthenticate(object):
    def test_authenticate_remote_user_should_return_account_if_header_set(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            with patch(
                "nav.web.auth.Account.objects.get",
                new=MagicMock(return_value=REMOTE_USER_ACCOUNT),
            ):
                assert remote_user.authenticate(request) == REMOTE_USER_ACCOUNT

    def test_authenticate_remote_user_should_return_none_if_header_not_set(self):
        r = RequestFactory()
        request = r.get('/')
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            assert remote_user.authenticate(request) == None

    def test_authenticate_remote_user_should_return_false_if_account_locked(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            with patch(
                "nav.web.auth.Account.objects.get", return_value=REMOTE_USER_ACCOUNT
            ):
                with patch("nav.web.auth.LogEntry.add_log_entry"):
                    with patch("nav.web.auth.Account.locked", return_value=True):
                        assert remote_user.authenticate(request) == False


class TestGetStandardUrls(object):
    def test_get_login_url_default(self):
        r = RequestFactory()
        request = r.get('/')
        raw_login_url = auth.LOGIN_URL
        result = auth.get_login_url(request)
        assert result.startswith(raw_login_url)

    def test_get_remote_login_url(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            with patch("nav.web.auth.remote_user._config.get", return_value='foo'):
                result = auth.get_login_url(request)
                assert result == 'foo'

    def test_get_logout_url_default(self):
        r = RequestFactory()
        request = r.get('/')
        result = auth.get_logout_url(request)
        assert result == auth.LOGOUT_URL

    def test_get_remote_logout_url(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            with patch("nav.web.auth.remote_user._config.get", return_value='foo'):
                result = auth.get_logout_url(request)
                assert result == 'foo'


class TestGetRemoteUsername(object):
    def test_no_request(self):
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=False):
            result = remote_user.get_username(None)
            assert result is None

    def test_not_enabled(self):
        r = RequestFactory()
        request = r.get('/')
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=False):
            result = remote_user.get_username(request)
            assert result is None

    def test_enabled_but_remote_user_unset(self):
        r = RequestFactory()
        request = r.get('/')
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            result = remote_user.get_username(request)
            assert result is None

    def test_enabled_and_remote_user_set(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            result = remote_user.get_username(request)
            assert result == 'knight'


class TestLoginRemoteUser(object):
    def test_remote_user_unset(self, fake_session):
        r = RequestFactory()
        request = r.get('/')
        request.session = fake_session
        with patch("nav.web.auth.remote_user.get_username", return_value=False):
            remote_user.login(request)
            assert not getattr(request, 'account', False)
            assert ACCOUNT_ID_VAR not in request.session

    def test_remote_user_set(self, fake_session):
        r = RequestFactory()
        request = r.get('/')
        request.session = fake_session
        with patch("nav.web.auth.remote_user.get_username", return_value=True):
            with patch(
                "nav.web.auth.remote_user.authenticate",
                return_value=REMOTE_USER_ACCOUNT,
            ):
                remote_user.login(request)
                assert hasattr(request, 'account')
                assert request.account == REMOTE_USER_ACCOUNT
                assert ACCOUNT_ID_VAR in request.session
                assert (
                    request.session.get(ACCOUNT_ID_VAR, None) == REMOTE_USER_ACCOUNT.id
                )
