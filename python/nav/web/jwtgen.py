from datetime import datetime, timedelta
from typing import Dict, Any
import jwt
from nav.jwtconf import JWTConf


def generate_access_token(token_data: Dict[str, Any] = {}) -> str:
    """Generates and returns an access token in JWT format.
    Will use `token_data` as a basis for the new token,
    but certain claims will be overridden.
    """
    return _generate_token(token_data, JWTConf.ACCESS_EXPIRE_DELTA, "access_token")


def generate_refresh_token(token_data: Dict[str, Any] = {}) -> str:
    """Generates and returns a refresh token in JWT format.
    Will use `token_data` as a basis for the new token,
    but certain claims will be overridden.
    """
    return _generate_token(token_data, JWTConf.REFRESH_EXPIRE_DELTA, "refresh_token")


def _generate_token(
    token_data: Dict[str, Any], expiry_delta: timedelta, token_type: str
) -> str:
    """Generates and returns a token in JWT format. Will use `token_data` as a basis
    for the new token, but certain claims will be overridden
    """
    new_token = dict(token_data)
    now = datetime.now()
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
