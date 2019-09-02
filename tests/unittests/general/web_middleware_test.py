from mock import patch

from django.test import RequestFactory

from nav.django.auth import ACCOUNT_ID_VAR
from nav.django.auth import SUDOER_ID_VAR
from nav.django.auth import AuthenticationMiddleware
from nav.django import auth


PLAIN_ACCOUNT = auth.Account(id=101, login='tim', password='wizard', locked=False)
DEFAULT_ACCOUNT = auth.Account(id=auth.Account.DEFAULT_ACCOUNT,
                               login='anonymous', password='bah',
                               locked=False)


class TestAuthenticationMiddleware(object):

    def test_process_request_logged_in(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = {ACCOUNT_ID_VAR: PLAIN_ACCOUNT.id}
        with patch('nav.django.auth.Account.objects.get', return_value=PLAIN_ACCOUNT):
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
        with patch('nav.django.auth.Account.objects.get', return_value=PLAIN_ACCOUNT):
            with patch('nav.django.auth.get_sudoer', return_value='foo'):
                AuthenticationMiddleware().process_request(fake_request)
                assert getattr(fake_request.account, 'sudo_operator', None) == 'foo'

    def test_process_request_not_logged_in(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.session = {}
        with patch('nav.django.auth.Account.objects.get', return_value=DEFAULT_ACCOUNT):
            AuthenticationMiddleware().process_request(fake_request)
            assert fake_request.account == DEFAULT_ACCOUNT
            assert fake_request.session[ACCOUNT_ID_VAR] == fake_request.account.id
