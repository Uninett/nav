from mock import patch
import os

from django.test import RequestFactory

from nav.web.auth import ACCOUNT_ID_VAR
from nav.web.auth import SUDOER_ID_VAR
from nav.web.auth import AuthenticationMiddleware
from nav.web.auth import AuthorizationMiddleware
from nav.web.auth import logout
from nav.web import auth


PLAIN_ACCOUNT = auth.Account(id=101, login='tim', password='wizard', locked=False)
ANOTHER_PLAIN_ACCOUNT = auth.Account(
    id=102, login='tom', password='pa$$w0rd', locked=False
)
SUDO_ACCOUNT = auth.Account(id=1337, login='bofh', password='alakazam', locked=False)
LOCKED_ACCOUNT = auth.Account(id=42, login='evil', password='haxxor', locked=True)
DEFAULT_ACCOUNT = auth.Account(
    id=auth.Account.DEFAULT_ACCOUNT, login='anonymous', password='bah', locked=False
)


class FakeSession(dict):
    def set_expiry(self, *_):
        pass

    def save(self, *_):
        pass


def test_set_account():
    r = RequestFactory()
    request = r.get('/')
    request.session = FakeSession()
    auth._set_account(request, DEFAULT_ACCOUNT)
    assert ACCOUNT_ID_VAR in request.session, 'Account id is not in the session'
    assert hasattr(request, 'account'), 'Account not set'
    assert request.account.id == request.session[ACCOUNT_ID_VAR], 'Correct user not set'
    assert request.session[ACCOUNT_ID_VAR] == DEFAULT_ACCOUNT.id


class TestEnsureAccount(object):
    def test_account_is_set_if_missing(self):
        r = RequestFactory()
        request = r.get('/')
        request.session = {}
        request.session = FakeSession()
        with patch("nav.web.auth.Account.objects.get", return_value=DEFAULT_ACCOUNT):
            auth.ensure_account(request)
            assert (
                auth.ACCOUNT_ID_VAR in request.session
            ), 'Account id is not in the session'
            assert hasattr(request, 'account'), 'Account not set'
            assert (
                request.account.id == request.session[auth.ACCOUNT_ID_VAR]
            ), 'Correct user not set'

    def test_account_is_switched_to_default_if_locked(self):
        r = RequestFactory()
        request = r.get('/')
        request.session = FakeSession()
        request.session[auth.ACCOUNT_ID_VAR] = LOCKED_ACCOUNT.id
        with patch(
            "nav.web.auth.Account.objects.get",
            side_effect=[LOCKED_ACCOUNT, DEFAULT_ACCOUNT],
        ):
            auth.ensure_account(request)
            assert request.session[auth.ACCOUNT_ID_VAR] == DEFAULT_ACCOUNT.id
            assert request.account == DEFAULT_ACCOUNT, 'Correct user not set'

    def test_account_is_left_alone_if_ok(self):
        r = RequestFactory()
        request = r.get('/')
        request.session = FakeSession()
        request.session[auth.ACCOUNT_ID_VAR] = return_value = PLAIN_ACCOUNT.id
        with patch("nav.web.auth.Account.objects.get", return_value=PLAIN_ACCOUNT):
            auth.ensure_account(request)
            assert request.account == PLAIN_ACCOUNT
            assert request.session[auth.ACCOUNT_ID_VAR] == PLAIN_ACCOUNT.id


class TestAuthenticationMiddleware(object):
    def test_process_request_logged_in(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = FakeSession(ACCOUNT_ID_VAR=PLAIN_ACCOUNT.id)
        with patch(
            'nav.web.auth.ensure_account',
            side_effect=auth._set_account(fake_request, PLAIN_ACCOUNT),
        ):
            AuthenticationMiddleware(lambda x: x).process_request(fake_request)
            assert fake_request.account == PLAIN_ACCOUNT
            assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id

    def test_process_request_set_sudoer(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = FakeSession(
            ACCOUNT_ID_VAR=PLAIN_ACCOUNT.id, SUDOER_ID_VAR=SUDO_ACCOUNT.id
        )
        with patch(
            'nav.web.auth.ensure_account',
            side_effect=auth._set_account(fake_request, PLAIN_ACCOUNT),
        ):
            with patch('nav.web.auth.get_sudoer', return_value=SUDO_ACCOUNT):
                AuthenticationMiddleware(lambda x: x).process_request(fake_request)
                assert (
                    getattr(fake_request.account, 'sudo_operator', None) == SUDO_ACCOUNT
                )

    def test_process_request_not_logged_in(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = FakeSession()
        with patch(
            'nav.web.auth.ensure_account',
            side_effect=auth._set_account(fake_request, DEFAULT_ACCOUNT),
        ):
            with patch('nav.web.auth.get_remote_username', return_value=None):
                AuthenticationMiddleware(lambda x: x).process_request(fake_request)
                assert fake_request.account == DEFAULT_ACCOUNT
                assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id

    def test_process_request_log_in_remote_user(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = FakeSession()
        with patch(
            'nav.web.auth.ensure_account',
            side_effect=auth._set_account(fake_request, DEFAULT_ACCOUNT),
        ):
            with patch(
                'nav.web.auth.get_remote_username', return_value=PLAIN_ACCOUNT.login
            ):
                with patch(
                    'nav.web.auth.login_remote_user',
                    side_effect=auth._set_account(fake_request, PLAIN_ACCOUNT),
                ):
                    AuthenticationMiddleware(lambda x: x).process_request(fake_request)
                    assert fake_request.account == PLAIN_ACCOUNT
                    assert fake_request.session[ACCOUNT_ID_VAR] == PLAIN_ACCOUNT.id

    def test_process_request_switch_users(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = FakeSession()
        with patch(
            'nav.web.auth.ensure_account',
            side_effect=auth._set_account(fake_request, PLAIN_ACCOUNT),
        ):
            with patch(
                'nav.web.auth.get_remote_username',
                return_value=ANOTHER_PLAIN_ACCOUNT.login,
            ):
                with patch(
                    'nav.web.auth.login_remote_user',
                    side_effect=auth._set_account(fake_request, ANOTHER_PLAIN_ACCOUNT),
                ):
                    with patch('nav.web.auth.logout'):
                        AuthenticationMiddleware(lambda x: x).process_request(fake_request)
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
        with patch('nav.web.auth.authorization_not_required', return_value=True):
            AuthorizationMiddleware(lambda x: x).process_request(fake_request)
            assert 'REMOTE_USER' not in os.environ

    def test_process_request_authorized(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.authorization_not_required', return_value=True):
            AuthorizationMiddleware(lambda x: x).process_request(fake_request)
            assert os.environ.get('REMOTE_USER', None) == PLAIN_ACCOUNT.login

    def test_process_request_not_authorized(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.authorization_not_required', return_value=False):
            with patch('nav.web.auth.Account.has_perm', return_value=False):
                with patch(
                    'nav.web.auth.AuthorizationMiddleware.redirect_to_login',
                    return_value='here',
                ):
                    result = AuthorizationMiddleware(lambda x: x).process_request(fake_request)
                    assert result == 'here'
                    assert os.environ.get('REMOTE_USER', None) != PLAIN_ACCOUNT.login


class TestLogout(object):
    def test_logout_before_login(self):
        r = RequestFactory()
        fake_request = r.get('/anyurl')
        with patch('nav.web.auth.LogEntry.add_log_entry'):
            result = logout(fake_request)
            assert result == None

    def test_non_sudo_logout(self):
        r = RequestFactory()
        fake_request = r.get('/anyurl')
        session = FakeSession(**{ACCOUNT_ID_VAR: PLAIN_ACCOUNT.id})
        fake_request.session = session
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.LogEntry.add_log_entry'):
            result = logout(fake_request)
            assert result == '/'
            assert not hasattr(fake_request, 'account')
            assert ACCOUNT_ID_VAR not in fake_request.session

    def test_sudo_logout(self):
        r = RequestFactory()
        fake_request = r.post('/anyurl', data={'submit_desudo': True})
        session = FakeSession(**{ACCOUNT_ID_VAR: PLAIN_ACCOUNT.id})
        fake_request.session = session
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.desudo'):
            with patch('nav.web.auth.reverse', return_value='parrot'):
                result = logout(fake_request)
                assert result == 'parrot'
                # Side effects of desudo() tested elsewhere
