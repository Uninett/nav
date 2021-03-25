from nav.config import NAVConfigParser
from nav.web.ldapauth import LDAPUser
from mock import Mock, patch


class LdapTestConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = []
    DEFAULT_CONFIG = u"""
[ldap]
basedn=cn=people,dc=example,dc=org
uid_attr=samAccountName
name_attr=cn
manager=
manager_password=
encoding=utf-8
"""


@patch('nav.web.ldapauth._config', LdapTestConfig())
def test_ldapuser_search_dn_decode_regression():
    """Verifies that LDAPUser.search_dn() returns user's DN untouched"""
    connection = Mock()
    connection.search_s.return_value = [
        (
            u'CN=Zaphod Beeblebr\xf6x,CN=people,DC=example,DC=org',
            {
                u'cn': b'Zaphod Beeblebr\xc3\xb6x',
                u'displayName': b'Zaphod Beeblebr\xc3\xb6x',
            },
        )
    ]

    user = LDAPUser('zaphod', connection)
    dn, uid = user.search_dn()
    assert dn == u'CN=Zaphod Beeblebr\xf6x,CN=people,DC=example,DC=org'
