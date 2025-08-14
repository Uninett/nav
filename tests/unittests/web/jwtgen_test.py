from datetime import datetime, timedelta
from typing import Any, Generator
from unittest.mock import patch

import jwt
import pytest
from nav.web.jwtgen import (
    decode_token,
    generate_access_token,
    generate_refresh_token,
    hash_token,
    is_active,
)


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


class TestHashToken:
    def test_should_return_correct_hash(self, token_string, token_hash):
        assert hash_token(token_string) == token_hash


class TestDecodeToken:
    def test_should_return_expected_data(self, token_string, token_data):
        assert decode_token(token_string) == token_data


@pytest.fixture(scope="module", autouse=True)
def jwt_private_key_mock(rsa_private_key) -> Generator[str, None, None]:
    """Mocks the JWT_PRIVATE_KEY setting"""
    with patch("nav.web.jwtgen.JWT_PRIVATE_KEY", rsa_private_key):
        yield rsa_private_key


@pytest.fixture(scope="module", autouse=True)
def jwt_name_mock(nav_name) -> Generator[str, None, None]:
    """Mocks the JWT_NAME setting"""
    with patch("nav.web.jwtgen.JWT_NAME", nav_name):
        yield nav_name


@pytest.fixture(scope="module", autouse=True)
def jwt_access_token_lifetime_mock() -> Generator[timedelta, None, None]:
    """Mocks the JWT_ACCESS_TOKEN_LIFETIME setting"""
    lifetime = timedelta(hours=1)
    with patch("nav.web.jwtgen.JWT_ACCESS_TOKEN_LIFETIME", lifetime):
        yield lifetime


@pytest.fixture(scope="module", autouse=True)
def jwt_refresh_token_lifetime_mock() -> Generator[timedelta, None, None]:
    """Mocks the JWT_REFRESH_TOKEN_LIFETIME setting"""
    lifetime = timedelta(days=1)
    with patch("nav.web.jwtgen.JWT_REFRESH_TOKEN_LIFETIME", lifetime):
        yield lifetime


@pytest.fixture(scope="module")
def nav_name() -> str:
    yield "nav"


@pytest.fixture(scope="module")
def token_string() -> str:
    """String representation of a token. Matching data is in `token_data`
    and expected hash is in `token_hash`
    """
    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQ"
        "iOjE3NDA0Nzg4NTQsImV4cCI6MTc0MDU2NTI1NH0.2GbcpbwzVOAV7"
        "nv4lAS_ISrw-g9WKvhKKnpN9dhSL6s"
    )
    return token


@pytest.fixture(scope="module")
def token_hash() -> str:
    """SHA256 hash of a token. Matching data is in `token_data`
    and the actual token string is in `token_string`
    """
    return "91d0d189dde6a7423b884f8bb285b17f9706d21e6d0ce45aac028a22b3067395"


@pytest.fixture(scope="module")
def token_data() -> dict[str, Any]:
    """Payload of a token. The actual token string is in `token_string`
    and hash of the token in `token_hash`
    """
    return {
        "iat": 1740478854,
        "exp": 1740565254,
    }
