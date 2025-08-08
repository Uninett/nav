import hashlib
from datetime import datetime, timedelta, timezone
from typing import Generator
from unittest.mock import MagicMock, Mock, patch

import jwt
import pytest
from django.urls import reverse
from nav.models.api import JWTRefreshToken


def test_token_not_in_database_should_be_rejected(db, api_client, url, active_token):
    token_hash = hashlib.sha256(active_token.encode('utf-8')).hexdigest()
    assert not JWTRefreshToken.objects.filter(hash=token_hash).exists()
    response = api_client.post(
        url,
        follow=True,
        data={
            'refresh_token': active_token,
        },
    )
    assert response.status_code == 403


def test_inactive_token_should_be_rejected(db, api_client, url, inactive_token):
    now = datetime.now()
    token_hash = hashlib.sha256(inactive_token.encode('utf-8')).hexdigest()
    db_token = JWTRefreshToken(
        name="testtoken",
        hash=token_hash,
        expires=now - timedelta(hours=1),
        activates=now - timedelta(hours=2),
    )
    db_token.save()

    response = api_client.post(
        url,
        follow=True,
        data={
            'refresh_token': inactive_token,
        },
    )

    assert response.status_code == 403


def test_revoked_token_should_be_rejected(db, api_client, url, active_token):
    token_hash = hashlib.sha256(active_token.encode('utf-8')).hexdigest()
    data = jwt.decode(active_token, options={'verify_signature': False})
    db_token = JWTRefreshToken(
        name="testtoken",
        hash=token_hash,
        expires=datetime.fromtimestamp(data['exp']),
        activates=datetime.fromtimestamp(data['nbf']),
        revoked=True,
    )
    db_token.save()
    response = api_client.post(
        url,
        follow=True,
        data={
            'refresh_token': active_token,
        },
    )
    assert response.status_code == 403


def test_valid_token_should_be_accepted(db, api_client, url, active_token):
    data = jwt.decode(active_token, options={'verify_signature': False})
    token_hash = token_hash = hashlib.sha256(active_token.encode('utf-8')).hexdigest()
    db_token = JWTRefreshToken(
        name="testtoken",
        hash=token_hash,
        expires=datetime.fromtimestamp(data['exp']),
        activates=datetime.fromtimestamp(data['nbf']),
    )
    db_token.save()
    response = api_client.post(
        url,
        follow=True,
        data={
            'refresh_token': active_token,
        },
    )
    assert response.status_code == 200


def test_valid_token_should_be_replaced_by_new_token_in_db(
    db, api_client, url, active_token
):
    token_hash = token_hash = hashlib.sha256(active_token.encode('utf-8')).hexdigest()
    data = jwt.decode(active_token, options={'verify_signature': False})
    db_token = JWTRefreshToken(
        name="testtoken",
        hash=token_hash,
        expires=datetime.fromtimestamp(data['exp']),
        activates=datetime.fromtimestamp(data['nbf']),
    )
    db_token.save()
    response = api_client.post(
        url,
        follow=True,
        data={
            'refresh_token': active_token,
        },
    )
    assert response.status_code == 200
    assert not JWTRefreshToken.objects.filter(hash=token_hash).exists()
    new_token = response.data.get("refresh_token")
    new_hash = hashlib.sha256(new_token.encode('utf-8')).hexdigest()
    assert JWTRefreshToken.objects.filter(hash=new_hash).exists()


def test_should_include_access_and_refresh_token_in_response(
    db, api_client, url, active_token
):
    token_hash = hashlib.sha256(active_token.encode('utf-8')).hexdigest()
    data = jwt.decode(active_token, options={'verify_signature': False})
    db_token = JWTRefreshToken(
        name="testtoken",
        hash=token_hash,
        expires=datetime.fromtimestamp(data['exp']),
        activates=datetime.fromtimestamp(data['nbf']),
    )
    db_token.save()
    response = api_client.post(
        url,
        follow=True,
        data={
            'refresh_token': active_token,
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.data
    assert "refresh_token" in response.data


def test_last_used_should_be_updated_after_token_is_used(
    db, api_client, url, active_token
):
    token_hash = hashlib.sha256(active_token.encode('utf-8')).hexdigest()
    data = jwt.decode(active_token, options={'verify_signature': False})
    db_token = JWTRefreshToken(
        name="testtoken",
        hash=token_hash,
        expires=datetime.fromtimestamp(data['exp']),
        activates=datetime.fromtimestamp(data['nbf']),
    )
    db_token.save()
    assert db_token.last_used is None
    response = api_client.post(
        url,
        follow=True,
        data={
            'refresh_token': active_token,
        },
    )
    assert response.status_code == 200
    new_token = response.data.get("refresh_token")
    new_hash = hashlib.sha256(new_token.encode('utf-8')).hexdigest()
    assert JWTRefreshToken.objects.get(hash=new_hash).last_used is not None


@pytest.fixture()
def inactive_token(nav_name, rsa_private_key) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        'exp': (now - timedelta(hours=1)).timestamp(),
        'nbf': (now - timedelta(hours=2)).timestamp(),
        'iat': (now - timedelta(hours=2)).timestamp(),
        'aud': nav_name,
        'iss': nav_name,
        'token_type': 'refresh_token',
    }
    token = jwt.encode(claims, rsa_private_key, algorithm="RS256")
    return token


@pytest.fixture()
def active_token(nav_name, rsa_private_key) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        'exp': (now + timedelta(hours=1)).timestamp(),
        'nbf': now.timestamp(),
        'iat': now.timestamp(),
        'aud': nav_name,
        'iss': nav_name,
        'token_type': 'refresh_token',
    }
    token = jwt.encode(claims, rsa_private_key, algorithm="RS256")
    return token


@pytest.fixture()
def url():
    return reverse('api:1:jwt-refresh')


@pytest.fixture(scope="module", autouse=True)
def jwtconf_mock(rsa_private_key, nav_name) -> Generator[MagicMock, None, None]:
    """Mocks functions forthe JWTConf class"""
    with patch("nav.web.jwtgen.JWTConf") as _jwtconf_mock:
        instance = _jwtconf_mock.return_value
        instance.get_nav_name = Mock(return_value=nav_name)
        instance.get_nav_private_key = Mock(return_value=rsa_private_key)
        instance.get_access_token_lifetime = Mock(return_value=timedelta(hours=1))
        instance.get_refresh_token_lifetime = Mock(return_value=timedelta(days=1))
        yield _jwtconf_mock


@pytest.fixture(scope="module")
def nav_name() -> str:
    return "nav"
