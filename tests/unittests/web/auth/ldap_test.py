from mock import Mock, MagicMock, patch

import pytest

from nav.config import NAVConfigParser
from nav.models.profiles import Account
from nav.web import auth
from nav.web.auth import ldap


LOCKED_ACCOUNT = auth.Account(
    login='galahad',
    ext_sync='ldap',
    password='shrubbery',
    locked=True,
)
ACTIVE_ACCOUNT = auth.Account(
    login='arthur',
    ext_sync='ldap',
    password='shrubbery',
    locked=False,
)


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


@patch('nav.web.auth.ldap._config', LdapTestConfig())
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

    user = ldap.LDAPUser('zaphod', connection)
    dn, uid = user.search_dn()
    assert dn == u'CN=Zaphod Beeblebr\xf6x,CN=people,DC=example,DC=org'


class LdapOpenTestConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = []
    DEFAULT_CONFIG = u"""
[ldap]
server=ldap.example.org
port=636
encryption=tls
timeout=3
debug=true
"""


@patch('nav.web.auth.ldap._config', LdapOpenTestConfig())
def test_open_ldap_should_run_without_error():
    with patch('ldap.initialize') as initialize:
        assert ldap.open_ldap()


class LdapOpenTestInvalidEncryptionConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = []
    DEFAULT_CONFIG = u"""
[ldap]
server=ldap.example.org
port=636
encryption=invalid
timeout=3
debug=true
"""


@patch('nav.web.auth.ldap._config', LdapOpenTestInvalidEncryptionConfig())
def test_when_encryption_setting_is_invalid_open_ldap_should_run_without_encryption():
    with patch('ldap.initialize') as initialize:
        assert ldap.open_ldap()


class TestLdapUser(object):
    @patch.dict(
        "nav.web.auth.ldap._config._sections",
        {
            'ldap': {
                '__name__': 'ldap',
                'basedn': 'empty',
                'manager': 'empty',
                'manager_password': 'empty',
                'uid_attr': 'sAMAccountName',
                'encoding': 'utf-8',
            },
        },
    )
    def test_search_result_with_referrals_should_be_considered_empty(self):
        """LP#1207737"""
        conn = Mock(
            **{
                'search_s.return_value': [
                    (None, "restaurant"),
                    (None, "at the end of the universe"),
                ]
            }
        )
        u = ldap.LDAPUser("zaphod", conn)
        with pytest.raises(ldap.UserNotFound):
            u.search_dn()

    @patch.dict(
        "nav.web.auth.ldap._config._sections",
        {
            'ldap': {
                '__name__': 'ldap',
                'basedn': 'empty',
                'lookupmethod': 'direct',
                'uid_attr': 'uid',
                'encoding': 'utf-8',
                'suffix': '',
            }
        },
    )
    def test_non_ascii_password_should_work(self):
        """LP#1213818"""
        conn = Mock(
            **{
                'simple_bind_s.side_effect': lambda x, y: (
                    str(x),
                    str(y),
                ),
            }
        )
        u = ldap.LDAPUser(u"zaphod", conn)
        u.bind(u"æøå")

    @patch.dict(
        "nav.web.auth.ldap._config._sections",
        {
            'ldap': {
                '__name__': 'ldap',
                'basedn': 'cn=users,dc=example,dc=org',
                'lookupmethod': 'direct',
                'uid_attr': 'uid',
                'encoding': 'utf-8',
                'group_search': '(member=%%s)',
            },
        },
    )
    def test_is_group_member_for_non_ascii_user_should_not_raise(self):
        """LP#1301794"""

        def fake_search(base, scope, filtr):
            str(base)
            str(filtr)
            return []

        conn = Mock(
            **{
                'search_s.side_effect': fake_search,
            }
        )
        u = ldap.LDAPUser(u"Ægir", conn)
        u.is_group_member('cn=noc-operators,cn=groups,dc=example,dc=com')


@patch.dict(
    "nav.web.auth.ldap._config._sections",
    {
        'ldap': {
            '__name__': 'ldap',
            'basedn': 'cn=users,dc=example,dc=org',
            'lookupmethod': 'direct',
            'uid_attr': 'uid',
            'encoding': 'utf-8',
            'require_entitlement': 'president',
            'admin_entitlement': 'boss',
            'entitlement_attribute': 'eduPersonEntitlement',
        },
    },
)
class TestLdapEntitlements(object):
    def test_required_entitlement_should_be_verified(self, user_zaphod):
        u = ldap.LDAPUser("zaphod", user_zaphod)
        assert u.has_entitlement('president')

    def test_missing_entitlement_should_not_be_verified(self, user_marvin):
        u = ldap.LDAPUser("marvin", user_marvin)
        assert not u.has_entitlement('president')

    def test_admin_entitlement_should_be_verified(self, user_zaphod):
        u = ldap.LDAPUser("zaphod", user_zaphod)
        assert u.is_admin()

    def test_missing_admin_entitlement_should_be_verified(self, user_marvin):
        u = ldap.LDAPUser("marvin", user_marvin)
        assert not u.is_admin()


@patch.dict(
    "nav.web.auth.ldap._config._sections",
    {
        'ldap': {
            '__name__': 'ldap',
            'basedn': 'cn=users,dc=example,dc=org',
            'lookupmethod': 'direct',
            'uid_attr': 'uid',
            'encoding': 'utf-8',
            'require_entitlement': 'president',
            'admin_entitlement': '',
            'entitlement_attribute': 'eduPersonEntitlement',
        },
    },
)
def test_no_admin_entitlement_option_should_make_no_admin_decision(user_zaphod):
    u = ldap.LDAPUser("zaphod", user_zaphod)
    assert u.is_admin() is None


class TestLdapAuthenticate:
    @patch("nav.web.auth.ldap.available", new=False)
    def test_if_ldap_not_available_return_None(self, *_):
        result = ldap.authenticate('foo', 'bar')
        assert result is None

    @patch("nav.web.auth.ldap.available", new=True)
    @patch("nav.web.auth.ldap.get_ldap_user", return_value=False)
    @patch(
        "nav.web.auth.Account.objects.get", new=MagicMock(return_value=LOCKED_ACCOUNT)
    )
    def test_locked_accounts_return_None(self, *_):
        result = ldap.authenticate('foo', 'bar')
        assert result is None

    @patch("nav.web.auth.ldap.available", new=True)
    @patch("nav.web.auth.ldap.get_ldap_user", return_value=False)
    @patch(
        "nav.web.auth.Account.objects.get", new=MagicMock(return_value=ACTIVE_ACCOUNT)
    )
    @patch("nav.web.auth.Account.check_password", return_value=False)
    def test_active_account_with_wrong_password_return_None(self, *_):
        result = ldap.authenticate('foo', 'ni!')
        assert result is None

    @patch("nav.web.auth.ldap.available", new=True)
    @patch("nav.web.auth.ldap.get_ldap_user", return_value=False)
    @patch(
        "nav.web.auth.Account.objects.get", new=MagicMock(return_value=ACTIVE_ACCOUNT)
    )
    @patch("nav.web.auth.Account.check_password", return_value=True)
    @patch("nav.web.auth.ldap.update_ldap_user", return_value=ACTIVE_ACCOUNT)
    def test_active_account_with_correct_password_return_account(self, *_):
        result = ldap.authenticate('foo', 'ni!')
        assert result == ACTIVE_ACCOUNT

    @patch("nav.web.auth.ldap.available", new=True)
    @patch("nav.web.auth.ldap.get_ldap_user", return_value=True)
    @patch("nav.web.auth.Account.objects.get", side_effect=Account.DoesNotExist())
    @patch("nav.web.auth.ldap.autocreate_ldap_user", return_value=ACTIVE_ACCOUNT)
    def test_nonexisting_accounts_are_created(self, *_):
        result = ldap.authenticate('foo', 'ni!')
        assert result == ACTIVE_ACCOUNT


#
# Pytest fixtures
#


@pytest.fixture
def user_zaphod():
    return Mock(
        **{
            'search_s.return_value': [
                (
                    u'uid=zaphod,cn=users,dc=example,dc=org',
                    {u'eduPersonEntitlement': [b'president', b'boss']},
                )
            ]
        }
    )


@pytest.fixture
def user_marvin():
    return Mock(
        **{
            'search_s.return_value': [
                (
                    u'uid=marvin,cn=users,dc=example,dc=org',
                    {u'eduPersonEntitlement': [b'paranoid']},
                )
            ]
        }
    )
