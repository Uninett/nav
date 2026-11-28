import importlib.util
import pytest

from nav.config import NAVConfigParser
from nav.web.auth.ldap import (
    LDAPConfigError,
    LDAPUser,
    NoAnswerError,
    NoStartTlsError,
    TimeoutError as LdapTimeoutError,
    UserNotFound,
    authenticate,
    open_ldap,
)
from mock import Mock, patch

found = importlib.util.find_spec('ldap')
if not found:
    pytestmark = pytest.mark.skip(reason="ldap module is not available")

ldap = pytest.importorskip("ldap")


class LdapTestConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = []
    DEFAULT_CONFIG = """
[ldap]
basedn=cn=people,dc=example,dc=org
uid_attr=samAccountName
name_attr=cn
manager=
manager_password=
encoding=utf-8
"""


@patch('nav.web.auth.ldap._config', LdapTestConfig())
def test_ldapuser_search_dn_decode_regression():
    """Verifies that LDAPUser.search_dn() returns user's DN untouched"""
    connection = Mock()
    connection.search_s.return_value = [
        (
            'CN=Zaphod Beeblebr\xf6x,CN=people,DC=example,DC=org',
            {
                'cn': b'Zaphod Beeblebr\xc3\xb6x',
                'displayName': b'Zaphod Beeblebr\xc3\xb6x',
            },
        )
    ]

    user = LDAPUser('zaphod', connection)
    dn, uid = user.search_dn()
    assert dn == 'CN=Zaphod Beeblebr\xf6x,CN=people,DC=example,DC=org'


class LdapOpenTestConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = []
    DEFAULT_CONFIG = """
[ldap]
server=ldap.example.org
port=636
encryption=tls
timeout=3
debug=true
"""


@patch('nav.web.auth.ldap._config', LdapOpenTestConfig())
def test_open_ldap_should_run_without_error():
    with patch('ldap.initialize'):
        assert open_ldap()


class LdapOpenTestInvalidEncryptionConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = []
    DEFAULT_CONFIG = """
[ldap]
server=ldap.example.org
port=636
encryption=invalid
timeout=3
debug=true
"""


@patch('nav.web.auth.ldap._config', LdapOpenTestInvalidEncryptionConfig())
def test_when_encryption_setting_is_invalid_open_ldap_should_run_without_encryption():
    with patch('ldap.initialize'):
        assert open_ldap()


class LdapGroupTestConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = []
    DEFAULT_CONFIG = """
[ldap]
server=ldap.example.org
port=389
encryption=none
basedn=cn=people,dc=example,dc=org
uid_attr=sAMAccountName
name_attr=cn
manager=cn=admin,dc=example,dc=org
manager_password=secret
encoding=utf-8
lookupmethod=search
require_group=cn=navusers,cn=groups,dc=example,dc=org
timeout=2
debug=no
suffix=
group_search=(member=%%s)
require_entitlement=
admin_entitlement=
entitlement_attribute=eduPersonEntitlement
"""


class TestAuthenticate:
    @patch('nav.web.auth.ldap._config', LdapGroupTestConfig())
    @patch('nav.web.auth.ldap.open_ldap')
    def test_when_user_not_found_during_group_check_it_should_return_false(  # noqa: E501
        self, open_ldap_mock
    ):
        """A UserNotFound during group membership verification should not crash"""
        connection = open_ldap_mock.return_value
        # bind succeeds (user authenticates)
        connection.simple_bind_s.return_value = None
        # But DN search during group check returns no results
        connection.search_s.return_value = []

        result = authenticate('rudolf', 'secret')
        assert result is False


BASE_DN = "cn=people,dc=example,dc=org"
USER_DN = f"uid=rudolf,{BASE_DN}"
GROUP_DN = "cn=navusers,cn=groups,dc=example,dc=org"
ENTITLEMENT_ATTR = "eduPersonEntitlement"

DEFAULT_LDAP_OPTIONS = {
    "server": "ldap.example.org",
    "port": "389",
    "encryption": "none",
    "timeout": "2",
    "debug": "no",
    "basedn": BASE_DN,
    "uid_attr": "uid",
    "name_attr": "cn",
    "manager": "",
    "manager_password": "",
    "encoding": "utf-8",
    "lookupmethod": "direct",
    "suffix": "",
    "require_group": "",
    "group_search": "(member=%%s)",
    "require_entitlement": "",
    "admin_entitlement": "",
    "entitlement_attribute": ENTITLEMENT_ATTR,
}


def make_ldap_config(**options):
    """Builds a NAVConfigParser with an [ldap] section from default test options,
    overridden by the given options.
    """
    merged = {**DEFAULT_LDAP_OPTIONS, **options}
    body = "\n".join(f"{key}={value}" for key, value in merged.items())

    class _Config(NAVConfigParser):
        DEFAULT_CONFIG_FILES = []
        DEFAULT_CONFIG = f"[ldap]\n{body}\n"

    return _Config()


@pytest.fixture
def configure_ldap(monkeypatch):
    """Returns a function that replaces the LDAP module's config for one test"""

    def _configure(**options):
        monkeypatch.setattr('nav.web.auth.ldap._config', make_ldap_config(**options))

    return _configure


@pytest.fixture
def connection():
    """A mock LDAP connection object"""
    return Mock()


def entitlement_result(*entitlements, dn=USER_DN):
    return [(dn, {ENTITLEMENT_ATTR: [e.encode() for e in entitlements]})]


class TestOpenLdap:
    def test_when_encryption_is_ssl_it_should_use_the_ldaps_scheme(
        self, configure_ldap
    ):
        configure_ldap(encryption="ssl", port="636")
        with patch('ldap.initialize') as initialize:
            open_ldap()
        initialize.assert_called_once_with(
            "ldaps://ldap.example.org:636", bytes_mode=False
        )

    def test_when_encryption_is_tls_it_should_start_tls(self, configure_ldap):
        configure_ldap(encryption="tls")
        with patch('ldap.initialize') as initialize:
            conn = open_ldap()
        initialize.assert_called_once_with(
            "ldap://ldap.example.org:389", bytes_mode=False
        )
        conn.start_tls_s.assert_called_once_with()

    def test_when_server_lacks_starttls_it_should_raise_no_starttls_error(
        self, configure_ldap
    ):
        configure_ldap(encryption="tls")
        with patch('ldap.initialize') as initialize:
            initialize.return_value.start_tls_s.side_effect = ldap.PROTOCOL_ERROR
            with pytest.raises(NoStartTlsError):
                open_ldap()

    @pytest.mark.parametrize("error", [ldap.SERVER_DOWN, ldap.CONNECT_ERROR])
    def test_when_server_is_down_during_starttls_it_should_raise_no_answer_error(
        self, configure_ldap, error
    ):
        configure_ldap(encryption="tls")
        with patch('ldap.initialize') as initialize:
            initialize.return_value.start_tls_s.side_effect = error
            with pytest.raises(NoAnswerError):
                open_ldap()

    def test_it_should_disable_referrals_and_apply_the_configured_timeout(
        self, configure_ldap
    ):
        configure_ldap(timeout="7")
        with patch('ldap.initialize'):
            conn = open_ldap()
        assert conn.timeout == 7.0
        conn.set_option.assert_called_with(ldap.OPT_REFERRALS, 0)


class TestAuthenticateOutcomes:
    @pytest.fixture(autouse=True)
    def mock_open_ldap(self, connection):
        with patch('nav.web.auth.ldap.open_ldap', return_value=connection):
            yield

    def test_when_bind_succeeds_without_restrictions_it_should_return_the_user(
        self, configure_ldap, connection
    ):
        configure_ldap()
        user = authenticate('rudolf', 'secret')
        assert isinstance(user, LDAPUser)
        connection.simple_bind_s.assert_called_once_with(USER_DN, 'secret')

    def test_when_credentials_are_invalid_it_should_return_false(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.simple_bind_s.side_effect = ldap.INVALID_CREDENTIALS
        assert authenticate('rudolf', 'wrong') is False

    @pytest.mark.parametrize("error", [ldap.SERVER_DOWN, ldap.CONNECT_ERROR])
    def test_when_server_is_down_it_should_raise_no_answer_error(
        self, configure_ldap, connection, error
    ):
        configure_ldap()
        connection.simple_bind_s.side_effect = error
        with pytest.raises(NoAnswerError):
            authenticate('rudolf', 'secret')

    def test_when_bind_times_out_it_should_raise_timeout_error(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.simple_bind_s.side_effect = ldap.TIMEOUT
        with pytest.raises(LdapTimeoutError):
            authenticate('rudolf', 'secret')

    def test_when_an_unexpected_ldap_error_occurs_it_should_return_false(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.simple_bind_s.side_effect = ldap.LDAPError
        assert authenticate('rudolf', 'secret') is False

    def test_when_user_is_not_found_during_search_it_should_return_false(
        self, configure_ldap, connection
    ):
        configure_ldap(lookupmethod="search")
        connection.search_s.return_value = []
        assert authenticate('rudolf', 'secret') is False

    def test_when_user_vanishes_during_group_check_it_should_return_false(
        self, configure_ldap, connection
    ):
        # With a suffix the bind needs no DN lookup, so the lookup first happens
        # (and fails) while verifying the group membership
        configure_ldap(
            suffix="@example.org", lookupmethod="search", require_group=GROUP_DN
        )
        connection.search_s.return_value = []
        assert authenticate('rudolf', 'secret') is False

    def test_when_user_is_member_of_required_group_it_should_return_the_user(
        self, configure_ldap, connection
    ):
        configure_ldap(require_group=GROUP_DN)
        connection.search_s.return_value = [(GROUP_DN, {})]
        assert isinstance(authenticate('rudolf', 'secret'), LDAPUser)

    def test_when_user_is_not_member_of_required_group_it_should_return_false(
        self, configure_ldap, connection
    ):
        configure_ldap(require_group=GROUP_DN)
        connection.search_s.return_value = []
        assert authenticate('rudolf', 'secret') is False

    def test_when_user_has_required_entitlement_it_should_return_the_user(
        self, configure_ldap, connection
    ):
        configure_ldap(require_entitlement="urn:nav:user")
        connection.search_s.return_value = entitlement_result("urn:nav:user")
        assert isinstance(authenticate('rudolf', 'secret'), LDAPUser)

    def test_when_user_lacks_required_entitlement_it_should_return_false(
        self, configure_ldap, connection
    ):
        configure_ldap(require_entitlement="urn:nav:user")
        connection.search_s.return_value = entitlement_result("urn:other")
        assert authenticate('rudolf', 'secret') is False


class TestLdapUserBind:
    def test_without_suffix_it_should_bind_as_the_constructed_dn(
        self, configure_ldap, connection
    ):
        configure_ldap()
        LDAPUser('rudolf', connection).bind('secret')
        connection.simple_bind_s.assert_called_once_with(USER_DN, 'secret')

    def test_with_suffix_it_should_bind_as_username_plus_suffix(
        self, configure_ldap, connection
    ):
        configure_ldap(suffix="@example.org")
        LDAPUser('rudolf', connection).bind('secret')
        connection.simple_bind_s.assert_called_once_with('rudolf@example.org', 'secret')


class TestLdapUserDn:
    def test_direct_lookup_should_construct_the_dn_from_config(
        self, configure_ldap, connection
    ):
        configure_ldap(lookupmethod="direct")
        assert LDAPUser('rudolf', connection).get_user_dn() == USER_DN
        connection.search_s.assert_not_called()

    def test_search_lookup_should_use_dn_and_username_from_the_directory(
        self, configure_ldap, connection
    ):
        configure_ldap(lookupmethod="search")
        connection.search_s.return_value = [
            ('uid=Rudolf,' + BASE_DN, {'uid': [b'Rudolf']})
        ]
        user = LDAPUser('rudolf', connection)
        assert user.get_user_dn() == 'uid=Rudolf,' + BASE_DN
        assert user.username == 'Rudolf'

    def test_dn_should_only_be_looked_up_once(self, configure_ldap, connection):
        configure_ldap(lookupmethod="search")
        connection.search_s.return_value = [(USER_DN, {})]
        user = LDAPUser('rudolf', connection)
        user.get_user_dn()
        user.get_user_dn()
        assert connection.search_s.call_count == 1

    def test_when_lookup_method_is_invalid_it_should_raise_config_error(
        self, configure_ldap, connection
    ):
        configure_ldap(lookupmethod="bogus")
        with pytest.raises(LDAPConfigError):
            LDAPUser('rudolf', connection).get_user_dn()

    def test_search_should_keep_username_when_uid_attribute_is_missing(
        self, configure_ldap, connection
    ):
        configure_ldap(lookupmethod="search")
        connection.search_s.return_value = [(USER_DN, {'cn': [b'Rudolf']})]
        dn, uid = LDAPUser('rudolf', connection).search_dn()
        assert (dn, uid) == (USER_DN, 'rudolf')

    def test_search_should_bind_as_manager_when_one_is_configured(
        self, configure_ldap, connection
    ):
        configure_ldap(
            lookupmethod="search",
            manager="cn=admin,dc=example,dc=org",
            manager_password="managerpw",
        )
        connection.search_s.return_value = [(USER_DN, {})]
        LDAPUser('rudolf', connection).search_dn()
        connection.simple_bind_s.assert_called_once_with(
            "cn=admin,dc=example,dc=org", "managerpw"
        )

    def test_search_should_escape_special_characters_in_the_username(
        self, configure_ldap, connection
    ):
        configure_ldap(lookupmethod="search")
        connection.search_s.return_value = [(USER_DN, {})]
        LDAPUser('rudolf)(uid=*', connection).search_dn()
        filter_ = connection.search_s.call_args[0][2]
        assert filter_ == r"(uid=rudolf\29\28uid=\2a)"

    @pytest.mark.parametrize("result", [[], [None], [(None, {})]])
    def test_search_should_raise_user_not_found_for_empty_results(
        self, configure_ldap, connection, result
    ):
        configure_ldap(lookupmethod="search")
        connection.search_s.return_value = result
        with pytest.raises(UserNotFound):
            LDAPUser('rudolf', connection).search_dn()


class TestLdapUserAttributes:
    def test_get_real_name_should_return_the_decoded_name_attribute(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.return_value = [(USER_DN, {'cn': ['Rudolf Räv'.encode()]})]
        assert LDAPUser('rudolf', connection).get_real_name() == 'Rudolf Räv'

    def test_get_real_name_should_return_none_on_ldap_errors(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.side_effect = ldap.LDAPError
        assert LDAPUser('rudolf', connection).get_real_name() is None

    def test_is_group_member_should_match_group_of_names_first(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.return_value = [(GROUP_DN, {})]
        assert LDAPUser('rudolf', connection).is_group_member(GROUP_DN) is True
        assert connection.search_s.call_count == 1

    def test_is_group_member_should_fall_back_to_posix_group_matching(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.side_effect = [[], [(GROUP_DN, {})]]
        assert LDAPUser('rudolf', connection).is_group_member(GROUP_DN) is True
        assert connection.search_s.call_args[0][2] == "(memberUid=rudolf)"

    def test_is_group_member_should_be_false_when_nothing_matches(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.return_value = []
        assert LDAPUser('rudolf', connection).is_group_member(GROUP_DN) is False

    def test_is_group_member_should_raise_timeout_error_on_timeout(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.side_effect = ldap.TIMEOUT
        with pytest.raises(LdapTimeoutError):
            LDAPUser('rudolf', connection).is_group_member(GROUP_DN)

    def test_get_entitlements_should_return_the_decoded_entitlements(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.return_value = entitlement_result("urn:a", "urn:b")
        assert LDAPUser('rudolf', connection).get_entitlements() == ["urn:a", "urn:b"]

    def test_get_entitlements_should_be_empty_without_a_result(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.return_value = []
        assert LDAPUser('rudolf', connection).get_entitlements() == []

    def test_get_entitlements_should_ignore_results_for_other_dns(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.return_value = entitlement_result(
            "urn:a", dn="uid=someone-else," + BASE_DN
        )
        assert LDAPUser('rudolf', connection).get_entitlements() == []

    def test_get_entitlements_should_be_empty_when_attribute_is_missing(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.return_value = [(USER_DN, {})]
        assert LDAPUser('rudolf', connection).get_entitlements() == []

    def test_get_entitlements_should_raise_timeout_error_on_timeout(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.side_effect = ldap.TIMEOUT
        with pytest.raises(LdapTimeoutError):
            LDAPUser('rudolf', connection).get_entitlements()

    def test_has_entitlement_should_check_the_users_entitlements(
        self, configure_ldap, connection
    ):
        configure_ldap()
        connection.search_s.return_value = entitlement_result("urn:a")
        user = LDAPUser('rudolf', connection)
        assert user.has_entitlement("urn:a")
        assert not user.has_entitlement("urn:b")

    def test_is_admin_should_be_none_without_an_admin_entitlement_configured(
        self, configure_ldap, connection
    ):
        configure_ldap(admin_entitlement="")
        assert LDAPUser('rudolf', connection).is_admin() is None

    @pytest.mark.parametrize(
        "granted, expected", [("urn:admin", True), ("urn:user", False)]
    )
    def test_is_admin_should_reflect_the_admin_entitlement(
        self, configure_ldap, connection, granted, expected
    ):
        configure_ldap(admin_entitlement="urn:admin")
        connection.search_s.return_value = entitlement_result(granted)
        assert LDAPUser('rudolf', connection).is_admin() is expected
