import pytest

from nav.web.security import WebSecurityConfigParser


class TestGetSecureProxySslHeader:
    @pytest.mark.parametrize("security_config", [""], indirect=True)
    def test_when_proxy_tls_terminated_is_unset_then_it_should_return_none(
        self, security_config
    ):
        assert security_config.get_secure_proxy_ssl_header() is None

    @pytest.mark.parametrize(
        "security_config", ["proxy_tls_terminated = no"], indirect=True
    )
    def test_when_proxy_tls_terminated_is_no_then_it_should_return_none(
        self, security_config
    ):
        assert security_config.get_secure_proxy_ssl_header() is None

    @pytest.mark.parametrize(
        "security_config", ["proxy_tls_terminated = yes"], indirect=True
    )
    def test_when_proxy_tls_terminated_is_yes_then_it_should_return_forwarded_proto_header(  # noqa: E501
        self, security_config
    ):
        assert security_config.get_secure_proxy_ssl_header() == (
            'HTTP_X_FORWARDED_PROTO',
            'https',
        )


class TestGetCsrfTrustedOrigins:
    @pytest.mark.parametrize(
        "security_config", ["csrf_trusted_origins ="], indirect=True
    )
    def test_when_csrf_trusted_origins_is_empty_then_it_should_return_empty_list(
        self, security_config
    ):
        assert security_config.get_csrf_trusted_origins() == []

    @pytest.mark.parametrize(
        "security_config",
        ["csrf_trusted_origins = https://a.example.org https://b.example.org"],
        indirect=True,
    )
    def test_when_csrf_trusted_origins_has_several_origins_then_it_should_return_each_origin(  # noqa: E501
        self, security_config
    ):
        assert security_config.get_csrf_trusted_origins() == [
            'https://a.example.org',
            'https://b.example.org',
        ]


@pytest.fixture
def security_config(request, monkeypatch):
    """Returns a WebSecurityConfigParser with request.param as the contents of
    its [security] section, ignoring any installed webfront.conf
    """
    monkeypatch.setattr(WebSecurityConfigParser, 'DEFAULT_CONFIG_FILES', ())
    parser = WebSecurityConfigParser()
    parser.parser.read_string(f"[security]\n{request.param}")
    return parser
