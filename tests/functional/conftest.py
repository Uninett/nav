import os
import pytest
from nav.django.auth import create_session_cookie

USERNAME = 'admin'


@pytest.fixture
def selenium(selenium, base_url):
    selenium.implicitly_wait(10)
    cookie = create_session_cookie(USERNAME)
    selenium.get('{}/400'.format(base_url))
    selenium.add_cookie(cookie)
    selenium.refresh()
    return selenium


@pytest.fixture(scope="session")
def base_url():
    return os.environ.get('TARGETURL', 'http://localhost:8000')
