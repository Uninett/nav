from mock import patch, Mock
import os

from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django_htmx.http import HttpResponseClientRedirect

from nav.web.auth.utils import ACCOUNT_ID_VAR, get_account, set_account
from nav.web.auth.sudo import SUDOER_ID_VAR
from nav.web.auth.middleware import AuthenticationMiddleware
from nav.web.auth.middleware import AuthorizationMiddleware
from nav.web.auth import logout
from nav.models import profiles


PLAIN_ACCOUNT = profiles.Account(id=101, login='tim', password='wizard', locked=False)
ANOTHER_PLAIN_ACCOUNT = profiles.Account(
    id=102, login='tom', password='pa$$w0rd', locked=False
)
SUDO_ACCOUNT = profiles.Account(
    id=1337, login='bofh', password='alakazam', locked=False
)
LOCKED_ACCOUNT = profiles.Account(id=42, login='evil', password='haxxor', locked=True)
DEFAULT_ACCOUNT = profiles.Account(
    id=profiles.Account.DEFAULT_ACCOUNT, login='anonymous', password='bah', locked=False
)


def test_set_account(fake_session):
    r = RequestFactory()
    request = r.get('/')
    request.session = fake_session
    set_account(request, DEFAULT_ACCOUNT)
    assert ACCOUNT_ID_VAR in request.session, 'Account id is not in the session'
    assert hasattr(request, 'account'), 'Account not set'
    assert request.account.id == request.session[ACCOUNT_ID_VAR], 'Correct user not set'
    assert request.user == request.account
    assert request.session[ACCOUNT_ID_VAR] == DEFAULT_ACCOUNT.id


def test_get_account(fake_session):
    r = RequestFactory()
    request = r.get('/')
    request.session = fake_session
    set_account(request, DEFAULT_ACCOUNT)
    session_account = get_account(request)
    assert session_account.id == DEFAULT_ACCOUNT.id


class TestAuthenticationMiddleware(object):
    def test_process_request_logged_in(self, fake_session):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_session[ACCOUNT_ID_VAR] = PLAIN_ACCOUNT.id
        fake_request.session = fake_session
        with patch(
            'nav.web.auth.middleware.ensure_account',
            side_effect=set_account(fake_request, PLAIN_ACCOUNT),
        ):
            AuthenticationMiddleware(lambda x: x).process_request(fake_request)
            assert fake_request.account == PLAIN_ACCOUNT
            assert fake_request.user == PLAIN_ACCOUNT
            assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id

    def test_process_request_set_sudoer(self, fake_session):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_session[ACCOUNT_ID_VAR] = PLAIN_ACCOUNT.id
        fake_session[SUDOER_ID_VAR] = SUDO_ACCOUNT.id
        fake_request.session = fake_session
        with patch(
            'nav.web.auth.middleware.ensure_account',
            side_effect=set_account(fake_request, PLAIN_ACCOUNT),
        ):
            with patch('nav.web.auth.middleware.get_sudoer', return_value=SUDO_ACCOUNT):
                AuthenticationMiddleware(lambda x: x).process_request(fake_request)
                assert (
                    getattr(fake_request.account, 'sudo_operator', None) == SUDO_ACCOUNT
                )

    def test_process_request_not_logged_in(self, fake_session):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = fake_session
        with patch(
            'nav.web.auth.middleware.ensure_account',
            side_effect=set_account(fake_request, DEFAULT_ACCOUNT),
        ):
            with patch('nav.web.auth.remote_user.get_username', return_value=None):
                AuthenticationMiddleware(lambda x: x).process_request(fake_request)
                assert fake_request.account == DEFAULT_ACCOUNT
                assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id

    def test_process_request_log_in_remote_user(self, fake_session):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = fake_session
        with patch(
            'nav.web.auth.middleware.ensure_account',
            side_effect=set_account(fake_request, DEFAULT_ACCOUNT),
        ):
            with patch(
                'nav.web.auth.remote_user.get_username',
                return_value=PLAIN_ACCOUNT.login,
            ):
                with patch(
                    'nav.web.auth.remote_user.login',
                    side_effect=set_account(fake_request, PLAIN_ACCOUNT),
                ):
                    AuthenticationMiddleware(lambda x: x).process_request(fake_request)
                    assert fake_request.account == PLAIN_ACCOUNT
                    assert fake_request.session[ACCOUNT_ID_VAR] == PLAIN_ACCOUNT.id

    def test_process_request_switch_users(self, fake_session):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = fake_session
        with patch(
            'nav.web.auth.middleware.ensure_account',
            side_effect=set_account(fake_request, PLAIN_ACCOUNT),
        ):
            with patch(
                'nav.web.auth.remote_user.get_username',
                return_value=ANOTHER_PLAIN_ACCOUNT.login,
            ):
                with patch(
                    'nav.web.auth.remote_user.login',
                    side_effect=set_account(fake_request, ANOTHER_PLAIN_ACCOUNT),
                ):
                    with patch('nav.web.auth.logout'):
                        AuthenticationMiddleware(lambda x: x).process_request(
                            fake_request
                        )
                        assert fake_request.account == ANOTHER_PLAIN_ACCOUNT
                        assert (
                            ACCOUNT_ID_VAR in fake_request.session
                            and fake_request.session[ACCOUNT_ID_VAR]
                            == ANOTHER_PLAIN_ACCOUNT.id
                        )


class TestAuthorizationMiddleware(object):
    def teardown_method(self, method):
        if 'REMOTE_USER' in os.environ:
            del os.environ['REMOTE_USER']

    def test_process_request_anonymous(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.account = DEFAULT_ACCOUNT
        with patch(
            'nav.web.auth.middleware.authorization_not_required', return_value=True
        ):
            AuthorizationMiddleware(lambda x: x).process_request(fake_request)
            assert 'REMOTE_USER' not in os.environ

    def test_process_request_authorized(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.account = PLAIN_ACCOUNT
        with patch(
            'nav.web.auth.middleware.authorization_not_required', return_value=True
        ):
            AuthorizationMiddleware(lambda x: x).process_request(fake_request)
            assert os.environ.get('REMOTE_USER', None) == PLAIN_ACCOUNT.login

    def test_process_request_not_authorized(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.account = PLAIN_ACCOUNT
        with patch(
            'nav.web.auth.middleware.authorization_not_required', return_value=False
        ):
            with patch('nav.models.profiles.Account.has_perm', return_value=False):
                with patch(
                    'nav.web.auth.middleware.AuthorizationMiddleware.redirect_to_login',
                    return_value='here',
                ):
                    result = AuthorizationMiddleware(lambda x: x).process_request(
                        fake_request
                    )
                    assert result == 'here'
                    assert os.environ.get('REMOTE_USER', None) != PLAIN_ACCOUNT.login


class TestRedirectToLogin:
    """Tests for AuthorizationMiddleware.redirect_to_login"""

    def test_regular_request_should_return_http_redirect(self):
        """A regular unauthenticated request should get a standard HTTP redirect"""
        request = RequestFactory().get('/protected/')
        request.htmx = False

        with patch('nav.web.auth.middleware.is_ajax', return_value=False):
            middleware = AuthorizationMiddleware(lambda x: x)
            response = middleware.redirect_to_login(request)

        assert isinstance(response, HttpResponseRedirect)

    def test_ajax_request_should_return_401(self):
        """An AJAX request should get a 401 response, not a redirect"""
        request = RequestFactory().get('/protected/')
        request.htmx = False

        with patch('nav.web.auth.middleware.is_ajax', return_value=True):
            middleware = AuthorizationMiddleware(lambda x: x)
            response = middleware.redirect_to_login(request)

        assert response.status_code == 401

    def test_htmx_request_should_return_client_redirect(self):
        """An HTMX request should get an HX-Redirect header for full page redirect"""
        request = RequestFactory().get('/protected/')
        request.htmx = Mock()
        request.htmx.current_url_abs_path = '/some/page/'

        with patch('nav.web.auth.middleware.is_ajax', return_value=False):
            middleware = AuthorizationMiddleware(lambda x: x)
            response = middleware.redirect_to_login(request)

        assert isinstance(response, HttpResponseClientRedirect)
        assert 'HX-Redirect' in response

    def test_htmx_request_without_origin_should_return_401(self):
        """An HTMX request without a recoverable origin URL should get a 401"""
        request = RequestFactory().get('/protected/')
        request.htmx = Mock()
        request.htmx.current_url_abs_path = None

        with patch('nav.web.auth.middleware.is_ajax', return_value=False):
            middleware = AuthorizationMiddleware(lambda x: x)
            response = middleware.redirect_to_login(request)

        assert response.status_code == 401


class TestLogout(object):
    def test_logout_before_login(self):
        r = RequestFactory()
        fake_request = r.get('/anyurl')
        with patch('nav.auditlog.models.LogEntry.add_log_entry'):
            result = logout(fake_request)
            assert result is None

    def test_sudo_logout(self, fake_session):
        r = RequestFactory()
        fake_request = r.post('/anyurl', data={'submit_desudo': True})
        fake_session[ACCOUNT_ID_VAR] = PLAIN_ACCOUNT.id
        fake_request.session = fake_session
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.desudo'):
            with patch('nav.web.auth.reverse', return_value='parrot'):
                result = logout(fake_request)
                assert result == 'parrot'
                # Side effects of desudo() tested elsewhere
