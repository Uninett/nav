from mock import patch
import os

import pytest

from nav.django.auth import ACCOUNT_ID_VAR, SUDOER_ID_VAR
from nav.django.auth import AuthenticationMiddleware
from nav.django.auth import AuthorizationMiddleware
from nav.django.auth import sudo, desudo
from nav.django.auth import SudoRecursionError, SudoNotAdminError
from nav.web import auth


PLAIN_ACCOUNT = auth.Account(id=101, login='tim', password='wizard')
DEFAULT_ACCOUNT = auth.Account(id=0, login='anonymous', password='bah')


class FakeRequest(object):

    class _FakeSession(dict):

        def save(*_):
            return

    def __init__(self, session=None, META=None, full_path=''):
        self.session = self._FakeSession()
        if session:
            self.session.update(**session)
        self.META = META if META else {}
        self.full_path = full_path

    def get_full_path(self):
        return self.full_path


class TestAuthenticationMiddleware(object):

    def test_process_request_logged_in(self):
        fake_request = FakeRequest(session={ACCOUNT_ID_VAR: 101})
        with patch('nav.django.auth.Account.objects.get', return_value=PLAIN_ACCOUNT):
            AuthenticationMiddleware().process_request(fake_request)
            assert fake_request.account == PLAIN_ACCOUNT
            assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id

    def test_process_request_set_sudoer(self):
        fake_request = FakeRequest(
            session={
                ACCOUNT_ID_VAR: 101,
                SUDOER_ID_VAR: True,
            }
        )
        with patch('nav.django.auth.Account.objects.get'):
            with patch('nav.django.auth.get_sudoer', return_value='foo'):
                AuthenticationMiddleware().process_request(fake_request)
                assert getattr(fake_request.account, 'sudo_operator', None) == 'foo'

    def test_process_request_not_logged_in(self):
        fake_request = FakeRequest(session={})
        with patch('nav.web.auth.Account.objects.get', return_value=DEFAULT_ACCOUNT):
            AuthenticationMiddleware().process_request(fake_request)
            assert fake_request.account == DEFAULT_ACCOUNT
            assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id

    def test_process_request_logged_in_remote_user(self):
        fake_request = FakeRequest(
            META={'REMOTE_USER': 'tim'}
        )
        with patch.dict('nav.django.auth.NAV_CONFIG', {'AUTH_SUPPORT_REMOTE_USER': True}):
            with patch('nav.django.auth.authenticate_remote_user', return_value=PLAIN_ACCOUNT):
                AuthenticationMiddleware().process_request(fake_request)
                assert fake_request.account == PLAIN_ACCOUNT
                assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id


class TestAuthorizationMiddleware(object):

    def teardown_method(self, method):
        if 'REMOTE_USER' in os.environ:
            del os.environ['REMOTE_USER']

    def test_process_request_anonymous(self):
        fake_request = FakeRequest()
        fake_request.account = DEFAULT_ACCOUNT
        with patch('nav.django.auth.authorization_not_required', return_value=True):
            AuthorizationMiddleware().process_request(fake_request)
            assert 'REMOTE_USER' not in os.environ

    def test_process_request_authorized(self):
        fake_request = FakeRequest()
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.django.auth.authorization_not_required', return_value=True):
            AuthorizationMiddleware().process_request(fake_request)
            assert os.environ.get('REMOTE_USER', None) == PLAIN_ACCOUNT.login

    def test_process_request_not_authorized(self):
        fake_request = FakeRequest()
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.django.auth.authorization_not_required', return_value=False):
            with patch('nav.django.auth.Account.has_perm', return_value=False):
                with patch('nav.django.auth.AuthorizationMiddleware.redirect_to_login', return_value='here'):
                    result = AuthorizationMiddleware().process_request(fake_request)
                    assert result == 'here'
                    assert os.environ.get('REMOTE_USER', None) != PLAIN_ACCOUNT.login


class TestSudo(object):

    def test_sudo_already(self):
        fake_request = FakeRequest(session={SUDOER_ID_VAR: True})
        with pytest.raises(SudoRecursionError):
            sudo(fake_request, None)

    def test_sudo_not_admin(self):
        fake_request = FakeRequest()
        with pytest.raises(SudoNotAdminError):
            with patch('nav.django.auth.is_admin', return_value=False):
                with patch('nav.django.auth.get_account', return_value=None):
                    sudo(fake_request, None)

    def test_sudo_ok(self):
        fake_request = FakeRequest(
            session={ACCOUNT_ID_VAR: PLAIN_ACCOUNT.id}
        )
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.django.auth.is_admin', return_value=True):
            with patch('nav.django.auth.get_account', return_value=None):
                sudo(fake_request, DEFAULT_ACCOUNT)
                assert fake_request.account == DEFAULT_ACCOUNT
                assert fake_request.session[ACCOUNT_ID_VAR] == DEFAULT_ACCOUNT.id
                assert fake_request.session[SUDOER_ID_VAR] == PLAIN_ACCOUNT.id


class TestDesudo(object):

    def test_desudo(self):
        fake_request = FakeRequest(
            session={
                SUDOER_ID_VAR: PLAIN_ACCOUNT.id,
                ACCOUNT_ID_VAR: DEFAULT_ACCOUNT.id,
            }
        )
        fake_request.account = DEFAULT_ACCOUNT
        with patch('nav.django.auth.Account.objects.get', return_value=PLAIN_ACCOUNT):
            desudo(fake_request)
            assert fake_request.account == PLAIN_ACCOUNT
            assert fake_request.session[ACCOUNT_ID_VAR] == PLAIN_ACCOUNT.id
            assert SUDOER_ID_VAR not in fake_request.session
