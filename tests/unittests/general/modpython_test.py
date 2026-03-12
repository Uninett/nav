from unittest.mock import patch

from django.test import RequestFactory

from nav.models import profiles
from nav.web.modpython import ModPythonAuthorizationMiddleware


PLAIN_ACCOUNT = profiles.Account(id=101, login='tim', password='wizard', locked=False)


class TestModPythonAuthorizationMiddleware:
    def test_process_request_authorized(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.user = PLAIN_ACCOUNT
        with patch('nav.web.modpython.authorize_request', return_value=True):
            result = ModPythonAuthorizationMiddleware(lambda x: x).process_request(
                fake_request
            )
            assert result is None

    def test_process_request_not_authorized(self):
        r = RequestFactory()
        fake_request = r.get('/')
        fake_request.user = PLAIN_ACCOUNT
        with patch('nav.web.modpython.authorize_request', return_value=False):
            with patch(
                'nav.web.modpython.redirect_to_login',
                return_value='here',
            ):
                result = ModPythonAuthorizationMiddleware(lambda x: x).process_request(
                    fake_request
                )
                assert result == 'here'
