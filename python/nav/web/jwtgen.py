from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt

from nav.jwtconf import JWTConf, ACCESS_TOKEN_EXPIRE_DELTA, REFRESH_TOKEN_EXPIRE_DELTA


def generate_access_token(token_data: Optional[dict[str, Any]] = None) -> str:
    """Generates and returns an access token in JWT format.
    Will use `token_data` as a basis for claims in the the new token,
    but the following claims will be overridden: `exp`, `nbf`, `iat`, `aud`, `iss`, `token_type`
    """
    return _generate_token(token_data, ACCESS_TOKEN_EXPIRE_DELTA, "access_token")


def generate_refresh_token(token_data: Optional[dict[str, Any]] = None) -> str:
    """Generates and returns a refresh token in JWT format.
    Will use `token_data` as a basis for claims in the the new token,
    but the following claims will be overridden: `exp`, `nbf`, `iat`, `aud`, `iss`, `token_type`
    """
    return _generate_token(token_data, REFRESH_TOKEN_EXPIRE_DELTA, "refresh_token")


def _generate_token(
    token_data: Optional[dict[str, Any]], expiry_delta: timedelta, token_type: str
) -> str:
    """Generates and returns a token in JWT format.
    Will use `token_data` as a basis for claims in the the new token,
    but the following claims will be overridden: `exp`, `nbf`, `iat`, `aud`, `iss`, `token_type`
    """
    if token_data is None:
        new_token = dict()
    else:
        new_token = dict(token_data)

    now = datetime.now(timezone.utc)
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
