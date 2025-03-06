from datetime import datetime, timedelta
from unittest.mock import patch

from nav.models.api import JWTRefreshToken


class TestIsActive:
    def test_should_return_false_if_token_activates_in_the_future(self):
        now = datetime.now()
        token = JWTRefreshToken(
            name="testtoken",
            hash="dummyhash",
            expires=now + timedelta(hours=1),
            activates=now + timedelta(hours=1),
        )
        assert not token.is_active()

    def test_should_return_false_if_token_expired_in_the_past(self):
        now = datetime.now()
        token = JWTRefreshToken(
            name="testtoken",
            hash="dummyhash",
            expires=now - timedelta(hours=1),
            activates=now - timedelta(hours=1),
        )
        assert not token.is_active()

    def test_should_return_true_if_token_activated_in_the_past_and_expires_in_the_future(
        self,
    ):
        now = datetime.now()
        token = JWTRefreshToken(
            name="testtoken",
            hash="dummyhash",
            expires=now + timedelta(hours=1),
            activates=now - timedelta(hours=1),
        )
        assert token.is_active()

    def test_should_return_true_if_token_activates_now_and_expires_in_the_future(self):
        now = datetime.now()
        token = JWTRefreshToken(
            name="testtoken",
            hash="dummyhash",
            expires=now + timedelta(hours=1),
            activates=now,
        )
        # Make sure the value we use for `activates` here matches
        # the `now` value in jwtgen.is_active
        with patch('nav.web.jwtgen.get_now', return_value=now):
            assert token.is_active()


def test_string_representation_should_match_name():
    now = datetime.now()
    token = JWTRefreshToken(
        name="testtoken",
        hash="dummyhash",
        expires=now + timedelta(hours=1),
        activates=now - timedelta(hours=1),
    )
    assert str(token) == token.name
