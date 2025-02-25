import pytest
from unittest.mock import Mock, patch
from datetime import datetime

import jwt

from nav.web.jwtgen import generate_access_token, generate_refresh_token


class TestTokenGeneration:
    """Tests behaviour that should be identical for both access and refresh token generation"""

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_nbf_should_be_in_the_past(self, func):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['nbf'] < datetime.now().timestamp()

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_exp_should_be_in_the_future(self, func):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['exp'] > datetime.now().timestamp()

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_iat_should_be_in_the_past(self, func):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['iat'] < datetime.now().timestamp()

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_aud_should_match_name_from_jwt_conf(self, func, nav_name):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['aud'] == nav_name

    @pytest.mark.parametrize("func", [generate_access_token, generate_refresh_token])
    def test_iss_should_match_name_from_jwt_conf(self, func, nav_name):
        encoded_token = func()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['iss'] == nav_name


class TestGenerateAccessToken:
    def test_token_type_should_be_access_token(self):
        encoded_token = generate_access_token()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['token_type'] == "access_token"


class TestGenerateRefreshToken:
    def test_token_type_should_be_refresh_token(self):
        encoded_token = generate_refresh_token()
        data = jwt.decode(encoded_token, options={'verify_signature': False})
        assert data['token_type'] == "refresh_token"


@pytest.fixture(scope="module", autouse=True)
def jwtconf_mock(rsa_private_key, nav_name) -> str:
    """Mocks the get_nav_name and get_nav_private_key functions for
    the JWTConf class
    """
    with patch("nav.web.jwtgen.JWTConf") as _jwtconf_mock:
        instance = _jwtconf_mock.return_value
        instance.get_nav_name = Mock(return_value=nav_name)
        instance.get_nav_private_key = Mock(return_value=rsa_private_key)
        yield _jwtconf_mock


@pytest.fixture(scope="module")
def nav_name() -> str:
    yield "nav"
