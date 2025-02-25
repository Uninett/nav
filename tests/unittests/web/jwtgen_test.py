import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

import jwt

from nav.web.jwtgen import generate_access_token, generate_refresh_token, is_active


class TestTokenGeneration:
    """
    Tests behaviour that should be identical for both access and refresh token
    generation
    """

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


class TestIsActive:
    def test_when_nbf_is_in_the_future_it_should_return_false(self):
        now = datetime.now()
        nbf = now + timedelta(hours=1)
        exp = now + timedelta(hours=1)
        assert not is_active(exp.timestamp(), nbf.timestamp())

    def test_when_exp_is_in_the_past_it_should_return_false(self):
        now = datetime.now()
        nbf = now - timedelta(hours=1)
        exp = now - timedelta(hours=1)
        assert not is_active(exp.timestamp(), nbf.timestamp())

    def test_when_nbf_is_in_the_past_and_exp_is_in_the_future_it_should_return_true(
        self,
    ):
        now = datetime.now()
        nbf = now - timedelta(hours=1)
        exp = now + timedelta(hours=1)
        assert is_active(exp.timestamp(), nbf.timestamp())

    def test_when_nbf_is_now_and_exp_is_in_the_future_it_should_return_true(self):
        now = datetime.now()
        exp = now + timedelta(hours=1)
        # Make sure the value we use for `nbf` here matches the `now` value in
        # jwtgen.is_active
        with patch('nav.web.jwtgen.get_now', return_value=now):
            assert is_active(exp.timestamp(), now.timestamp())


@pytest.fixture(scope="module", autouse=True)
def jwtconf_mock(rsa_private_key, nav_name) -> str:
    """Mocks the get_nav_name and get_nav_private_key functions for
    the JWTConf class
    """
    with patch("nav.web.jwtgen.JWTConf") as _jwtconf_mock:
        instance = _jwtconf_mock.return_value
        instance.get_nav_name = Mock(return_value=nav_name)
        instance.get_nav_private_key = Mock(return_value=rsa_private_key)
        instance.get_access_token_lifetime = Mock(return_value=timedelta(hours=1))
        instance.get_refresh_token_lifetime = Mock(return_value=timedelta(days=1))
        yield _jwtconf_mock


@pytest.fixture(scope="module")
def nav_name() -> str:
    yield "nav"
