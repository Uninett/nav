from mock import patch
import os

from django.test import RequestFactory

from nav.web.auth import ACCOUNT_ID_VAR
from nav.web.auth import SUDOER_ID_VAR
from nav.web.auth import AuthenticationMiddleware
from nav.web.auth import AuthorizationMiddleware
from nav.web.auth import logout
from nav.web import auth


PLAIN_ACCOUNT = auth.Account(id=101, login='tim', password='wizard')
SUDO_ACCOUNT = auth.Account(id=1337, login='bofh', password='alakazam')
DEFAULT_ACCOUNT = auth.Account(id=0, login='anonymous', password='bah')


class TestAuthenticationMiddleware(object):

    @classmethod
    def set_request(cls, request, account):
        request.account = account
        request.session[ACCOUNT_ID_VAR] = account.id

    def test_process_request_logged_in(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = {ACCOUNT_ID_VAR: 101}
        with patch('nav.web.auth.Account.objects.get', return_value=PLAIN_ACCOUNT):
            AuthenticationMiddleware().process_request(fake_request)
            assert fake_request.account == PLAIN_ACCOUNT
            assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id

    def test_process_request_set_sudoer(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = {
            ACCOUNT_ID_VAR: 101,
            SUDOER_ID_VAR: True,
        }
        with patch('nav.web.auth.Account.objects.get'):
            with patch('nav.web.auth.get_sudoer', return_value='foo'):
                AuthenticationMiddleware().process_request(fake_request)
                assert getattr(fake_request.account, 'sudo_operator', None) == 'foo'

    def test_process_request_not_logged_in(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = {}
        with patch('nav.web.auth.login_remote_user', return_value=None):
            with patch('nav.web.auth.get_remote_username', return_value=None):
                with patch('nav.web.auth.Account.objects.get', return_value=DEFAULT_ACCOUNT):
                    AuthenticationMiddleware().process_request(fake_request)
                    assert fake_request.account == DEFAULT_ACCOUNT
                    assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id

    def test_process_request_log_in_remote_user(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = {}
        with patch('nav.web.auth.login_remote_user', side_effect=self.set_request(fake_request, PLAIN_ACCOUNT)):
            with patch('nav.web.auth.get_remote_username', return_value=PLAIN_ACCOUNT.login):
                AuthenticationMiddleware().process_request(fake_request)
                assert fake_request.account == PLAIN_ACCOUNT
                assert fake_request.session[ACCOUNT_ID_VAR] == PLAIN_ACCOUNT.id

    def test_process_request_switch_users(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = {ACCOUNT_ID_VAR: PLAIN_ACCOUNT.id}
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.get_remote_username', return_value=SUDO_ACCOUNT.login):
            with patch('nav.web.auth.login_remote_user', side_effect=self.set_request(fake_request, SUDO_ACCOUNT)):
                with patch('nav.web.auth.logout'):
                    AuthenticationMiddleware().process_request(fake_request)
                    assert fake_request.account == SUDO_ACCOUNT
                    assert ACCOUNT_ID_VAR in fake_request.session and fake_request.session[ACCOUNT_ID_VAR] == SUDO_ACCOUNT.id


class TestAuthorizationMiddleware(object):

    def teardown_method(self, method):
        if 'REMOTE_USER' in os.environ:
            del os.environ['REMOTE_USER']

    def test_process_request_anonymous(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.account = DEFAULT_ACCOUNT
        with patch('nav.web.auth.authorization_not_required', return_value=True):
            AuthorizationMiddleware().process_request(fake_request)
            assert 'REMOTE_USER' not in os.environ

    def test_process_request_authorized(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.authorization_not_required', return_value=True):
            AuthorizationMiddleware().process_request(fake_request)
            assert os.environ.get('REMOTE_USER', None) == PLAIN_ACCOUNT.login

    def test_process_request_not_authorized(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.authorization_not_required', return_value=False):
            with patch('nav.web.auth.Account.has_perm', return_value=False):
                with patch('nav.web.auth.AuthorizationMiddleware.redirect_to_login', return_value='here'):
                    result = AuthorizationMiddleware().process_request(fake_request)
                    assert result == 'here'
                    assert os.environ.get('REMOTE_USER', None) != PLAIN_ACCOUNT.login


class TestLogout(object):
    class FakeSession(dict):

        def set_expiry(self, *_):
            pass

        def save(self, *_):
            pass

    def test_logout_before_login(self):
        r = RequestFactory()
        fake_request = r.get('/anyurl')
        with patch('nav.web.auth.LogEntry.add_log_entry'):
            result = logout(fake_request)
            assert result == None

    def test_non_sudo_logout(self):
        r = RequestFactory()
        fake_request = r.get('/anyurl')
        session = self.FakeSession(**{ACCOUNT_ID_VAR: PLAIN_ACCOUNT.id})
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
        session = self.FakeSession(**{ACCOUNT_ID_VAR: PLAIN_ACCOUNT.id})
        fake_request.session = session
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.desudo'):
            with patch('nav.web.auth.reverse', return_value='parrot'):
                result = logout(fake_request)
                assert result == 'parrot'
                # Side effects of desudo() tested elsewhere
