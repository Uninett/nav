import importlib.util
import pytest

from nav.config import NAVConfigParser
from nav.web.auth.ldap import LDAPUser, open_ldap
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
