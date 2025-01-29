from typing import Generator
import pytest
from datetime import datetime, timedelta, timezone

from nav.models.api import JWTRefreshToken


class TestIsActive:
    def test_should_return_false_if_nbf_is_in_the_future(self, token):
        now = datetime.now(tz=timezone.utc)
        token.data['nbf'] = (now + timedelta(hours=1)).timestamp()
        token.data['exp'] = (now + timedelta(hours=1)).timestamp()
        assert not token.is_active()

    def test_should_return_false_if_exp_is_in_the_past(self, token):
        now = datetime.now(tz=timezone.utc)
        token.data['nbf'] = (now - timedelta(hours=1)).timestamp()
        token.data['exp'] = (now - timedelta(hours=1)).timestamp()
        assert not token.is_active()

    def test_should_return_true_if_nbf_is_in_the_past_and_exp_is_in_the_future(
        self, token
    ):
        now = datetime.now(tz=timezone.utc)
        token.data['nbf'] = (now - timedelta(hours=1)).timestamp()
        token.data['exp'] = (now + timedelta(hours=1)).timestamp()
        assert token.is_active()


def test_string_representation_should_match_token(token):
    assert str(token) == token.name


@pytest.fixture()
def token(data) -> Generator[JWTRefreshToken, None, None]:
    refresh_token = JWTRefreshToken(
        name="testtoken",
        description="this is a test token",
        data=data,
        hash="dummyhash",
    )
    refresh_token.save()
    yield refresh_token
    refresh_token.delete()


@pytest.fixture()
def data() -> dict:
    data = {
        "exp": 1516339022,
        "nbf": 1516239022,
        "iat": 1516239022,
        "aud": "nav",
        "iss": "nav",
        "token_type": "refresh_token",
    }
    return data
