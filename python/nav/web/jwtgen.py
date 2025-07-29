from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt

from nav.jwtconf import JWTConf

# Alias for datetime.now for mocking purposes
get_now = datetime.now


def generate_access_token(token_data: Optional[dict[str, Any]] = None) -> str:
    """Generates and returns an access token in JWT format.
    Will use `token_data` as a basis for claims in the the new token,
    but the following claims will be overridden: `exp`, `nbf`, `iat`, `aud`, `iss`,
    `token_type`
    """
    expiry_delta = JWTConf().get_access_token_lifetime()
    return _generate_token(token_data, expiry_delta, "access_token")


def generate_refresh_token(token_data: Optional[dict[str, Any]] = None) -> str:
    """Generates and returns a refresh token in JWT format.
    Will use `token_data` as a basis for claims in the the new token,
    but the following claims will be overridden: `exp`, `nbf`, `iat`, `aud`, `iss`,
    `token_type`
    """
    expiry_delta = JWTConf().get_refresh_token_lifetime()
    return _generate_token(token_data, expiry_delta, "refresh_token")


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
    name = JWTConf().get_nav_name()
    updated_claims = {
        'exp': (now + expiry_delta).timestamp(),
        'nbf': now.timestamp(),
        'iat': now.timestamp(),
        'aud': name,
        'iss': name,
        'token_type': token_type,
    }
    new_token.update(updated_claims)
    encoded_token = jwt.encode(
        new_token, JWTConf().get_nav_private_key(), algorithm="RS256"
    )
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
