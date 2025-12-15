from mock import patch

from nav.web.auth.remote_user import (
    _workaround_feide_oidc,
    fake_password,
    get_remote_url,
    get_remote_user_varname,
)


def test_workaround_feide_oidc_returns_colonless_username():
    username = 'a:b'
    result = _workaround_feide_oidc(username)
    assert result == 'b'


def test_fake_password_returns_string_longer_than_given_length():
    length = 12
    result = fake_password(length)
    print(result)
    assert len(result) > length


def test_get_remote_url_for_nonexistent_urltype_returns_None():
    with patch('nav.web.auth.remote_user.is_remote_user_enabled', return_value=True):
        result = get_remote_url(None, 'nonexistent urltype')
        assert result is None


def test_get_remote_user_varname_should_fallback_to_REMOTE_USER_if_missing_config():
    with patch('nav.web.auth.remote_user._config.get', side_effect=ValueError):
        result = get_remote_user_varname()
        assert result == 'REMOTE_USER'
