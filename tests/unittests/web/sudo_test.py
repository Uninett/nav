from mock import patch
import os

import pytest

from nav.web.auth import ACCOUNT_ID_VAR
from nav.web.auth.sudo import SUDOER_ID_VAR
from nav.web import auth
from nav.web.auth.sudo import sudo, desudo
from nav.web.auth.sudo import SudoRecursionError, SudoNotAdminError


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


class TestSudo(object):

    def test_sudo_already(self):
        fake_request = FakeRequest(session={SUDOER_ID_VAR: True})
        with pytest.raises(SudoRecursionError):
            sudo(fake_request, None)

    def test_sudo_not_admin(self):
        fake_request = FakeRequest()
        with pytest.raises(SudoNotAdminError):
            with patch('nav.web.auth.sudo.is_admin', return_value=False):
                with patch('nav.web.auth.sudo.get_account', return_value=None):
                    sudo(fake_request, None)

    def test_sudo_ok(self):
        fake_request = FakeRequest(
            session={ACCOUNT_ID_VAR: PLAIN_ACCOUNT.id}
        )
        fake_request.account = PLAIN_ACCOUNT
        with patch('nav.web.auth.sudo.is_admin', return_value=True):
            with patch('nav.web.auth.sudo.get_account', return_value=None):
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
        with patch('nav.web.auth.Account.objects.get', return_value=PLAIN_ACCOUNT):
            desudo(fake_request)
            assert fake_request.account == PLAIN_ACCOUNT
            assert fake_request.session[ACCOUNT_ID_VAR] == PLAIN_ACCOUNT.id
            assert SUDOER_ID_VAR not in fake_request.session
