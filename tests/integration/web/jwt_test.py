from mock import patch
import pytest
from typing import Generator
from datetime import datetime, timedelta
from django.urls import reverse

from nav.models.api import JWTRefreshToken


def test_posting_valid_data_to_create_endpoint_should_create_token(db, client):
    """Tests that a token can be created"""
    url = reverse("useradmin-jwt_create")
    response = client.post(
        url,
        data={
            'name': 'mytesttoken',
            'permission': 'read',
        },
        follow=True,
    )

    assert response.status_code == 200
    assert JWTRefreshToken.objects.filter(name='mytesttoken').exists()


def test_posting_existing_token_id_to_delete_endpoint_should_delete_token(
    db, client, token
):
    """Tests that a token can be deleted"""
    url = reverse("useradmin-jwt_delete", args=[token.id])
    response = client.post(url, follow=True)

    assert response.status_code == 200
    assert not JWTRefreshToken.objects.filter(name='mytesttoken').exists()


def test_posting_existing_token_id_to_revoke_endpoint_should_revoke_token(
    db, client, token
):
    """Tests that a token can be revoked"""
    url = reverse("useradmin-jwt_revoke", args=[token.id])
    response = client.post(url, follow=True)

    assert response.status_code == 200
    token.refresh_from_db()
    assert token.revoked is True


def test_recreating_token_should_unrevoke_it(db, client, token):
    token.revoked = True
    token.save()
    url = reverse("useradmin-jwt_recreate", args=[token.id])
    response = client.post(url, follow=True)

    assert response.status_code == 200
    token.refresh_from_db()
    assert not token.revoked


@pytest.fixture()
def token(db) -> Generator[JWTRefreshToken, None, None]:
    """Fixture to create a JWTRefreshToken instance for testing"""
    token = JWTRefreshToken.objects.create(
        name='mytesttoken',
        permission='read',
        expires=datetime.now() + timedelta(days=1),
        activates=datetime.now() - timedelta(hours=1),
    )
    yield token
    if token.id:
        token.delete()


@pytest.fixture(scope="module", autouse=True)
def jwt_private_key_mock(rsa_private_key) -> Generator[str, None, None]:
    """Mocks the JWT_PRIVATE_KEY setting"""
    with patch("nav.web.jwtgen.JWT_PRIVATE_KEY", rsa_private_key):
        yield rsa_private_key


@pytest.fixture(scope="module", autouse=True)
def jwt_name_mock() -> Generator[str, None, None]:
    """Mocks the JWT_NAME setting"""
    with patch("nav.web.jwtgen.JWT_NAME", "localnav"):
        with patch("nav.web.api.v1.views.JWT_NAME", "localnav"):
            yield "localnav"


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
