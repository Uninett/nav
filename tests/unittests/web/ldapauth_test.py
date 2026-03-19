import importlib.util
import pytest

from nav.config import NAVConfigParser
from nav.web.auth.ldap import LDAPUser, authenticate, open_ldap
from mock import Mock, patch

found = importlib.util.find_spec('ldap')
if not found:
    pytestmark = pytest.mark.skip(reason="ldap module is not available")


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
