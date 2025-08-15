from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import hashlib

import jwt

from nav.django.settings import (
    JWT_PRIVATE_KEY,
    JWT_NAME,
    JWT_ACCESS_TOKEN_LIFETIME,
    JWT_REFRESH_TOKEN_LIFETIME,
)

# Alias for datetime.now for mocking purposes
get_now = datetime.now


def generate_access_token(token_data: Optional[dict[str, Any]] = None) -> str:
    """Generates and returns an access token in JWT format.
    Will use `token_data` as a basis for claims in the the new token,
    but the following claims will be overridden: `exp`, `nbf`, `iat`, `aud`, `iss`,
    `token_type`
    """
    return _generate_token(token_data, JWT_ACCESS_TOKEN_LIFETIME, "access_token")


def generate_refresh_token(token_data: Optional[dict[str, Any]] = None) -> str:
    """Generates and returns a refresh token in JWT format.
    Will use `token_data` as a basis for claims in the the new token,
    but the following claims will be overridden: `exp`, `nbf`, `iat`, `aud`, `iss`,
    `token_type`
    """
    return _generate_token(token_data, JWT_REFRESH_TOKEN_LIFETIME, "refresh_token")


def _generate_token(
    token_data: Optional[dict[str, Any]], expiry_delta: timedelta, token_type: str
) -> str:
    """Generates and returns a token in JWT format.
    Will use `token_data` as a basis for claims in the the new token,
    but the following claims will be overridden: `exp`, `nbf`, `iat`, `aud`, `iss`,
    `token_type`
    """
    if token_data is None:
        new_token = dict()
    else:
        new_token = dict(token_data)

    now = get_now(timezone.utc)
    updated_claims = {
        'exp': (now + expiry_delta).timestamp(),
        'nbf': now.timestamp(),
        'iat': now.timestamp(),
        'aud': JWT_NAME,
        'iss': JWT_NAME,
        'token_type': token_type,
    }
    new_token.update(updated_claims)
    encoded_token = jwt.encode(new_token, JWT_PRIVATE_KEY, algorithm="RS256")
    return encoded_token


def is_active(exp: float, nbf: float) -> bool:
    """
    Takes `exp` (expiration time) and `nbf` (not before time) as POSIX timestamps.
    These represent the claims of a JWT token. `exp` should be the expiration
    time of the token and `nbf` should be the time when the token becomes active.

    Returns True if `exp` is in the future and `nbf` is in the past or matches
    the current time.
    """
    now = get_now()
    expires = datetime.fromtimestamp(exp)
    activates = datetime.fromtimestamp(nbf)
    return now >= activates and now < expires


def hash_token(token: str) -> str:
    """Hashes a token with SHA256"""
    hash_object = hashlib.sha256(token.encode('utf-8'))
    hex_dig = hash_object.hexdigest()
    return hex_dig


def decode_token(token: str) -> dict[str, Any]:
    """Decodes a token in JWT format and returns the data of the decoded token"""
    return jwt.decode(token, options={'verify_signature': False})
