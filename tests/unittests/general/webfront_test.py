# -*- coding: utf-8 -*-
from mock import patch, MagicMock, Mock
from django.test import RequestFactory

try:
    import ldap
except ImportError:
    ldap = None

import pytest

import nav.web.auth.ldap
from nav.web import auth
from nav.web.auth import remote_user
from nav.web.auth.utils import ACCOUNT_ID_VAR, get_account
from nav.models import profiles

LDAP_ACCOUNT = profiles.Account(login='knight', ext_sync='ldap', password='shrubbery')
PLAIN_ACCOUNT = profiles.Account(login='knight', password='shrubbery')
REMOTE_USER_ACCOUNT = profiles.Account(
    login='knight', ext_sync='REMOTE_USER', password='shrubbery'
)


@patch("nav.models.profiles.Account.save", new=MagicMock(return_value=True))
@patch(
    "nav.models.profiles.Account.objects.get", new=MagicMock(return_value=LDAP_ACCOUNT)
)
class TestLdapAuthenticate(object):
    def test_authenticate_should_return_account_when_ldap_says_yes(self):
        ldap_user = Mock()
        ldap_user.is_admin.return_value = None  # mock to avoid database access
        with patch("nav.web.auth.ldap.available", new=True):
            with patch("nav.web.auth.ldap.authenticate", return_value=ldap_user):
                assert auth.authenticate('knight', 'shrubbery') == LDAP_ACCOUNT

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        with patch("nav.web.auth.ldap.available", new=True):
            with patch("nav.web.auth.ldap.authenticate", return_value=False):
                assert not auth.authenticate('knight', 'shrubbery')

    def test_authenticate_should_fallback_when_ldap_is_disabled(self):
        with patch("nav.web.auth.ldap.available", new=False):
            assert auth.authenticate('knight', 'shrubbery') == LDAP_ACCOUNT


@patch("nav.models.profiles.Account.save", new=MagicMock(return_value=True))
@patch(
    "nav.models.profiles.Account.objects.get", new=MagicMock(return_value=PLAIN_ACCOUNT)
)
@patch("nav.web.auth.ldap.available", new=False)
class TestNormalAuthenticate(object):
    def test_authenticate_should_return_account_when_password_is_ok(self):
        with patch("nav.web.auth.Account.check_password", return_value=True):
            assert auth.authenticate('knight', 'shrubbery') == PLAIN_ACCOUNT

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        with patch("nav.web.auth.Account.check_password", return_value=False):
            assert not auth.authenticate('knight', 'rabbit')


class TestRemoteUserAuthenticate(object):
    def test_authenticate_remote_user_should_return_account_if_header_set(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            with patch(
                "nav.models.profiles.Account.objects.get",
                new=MagicMock(return_value=REMOTE_USER_ACCOUNT),
            ):
                assert remote_user.authenticate(request) == REMOTE_USER_ACCOUNT

    def test_authenticate_remote_user_should_return_none_if_header_not_set(self):
        r = RequestFactory()
        request = r.get('/')
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            assert remote_user.authenticate(request) is None

    def test_authenticate_remote_user_should_return_false_if_account_locked(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            with patch(
                "nav.models.profiles.Account.objects.get",
                return_value=REMOTE_USER_ACCOUNT,
            ):
                with patch("nav.auditlog.models.LogEntry.add_log_entry"):
                    with patch("nav.models.profiles.Account.locked", return_value=True):
                        assert remote_user.authenticate(request) is False


class TestGetStandardUrls(object):
    def test_get_login_url_default(self):
        r = RequestFactory()
        request = r.get('/')
        raw_login_url = auth.LOGIN_URL
        result = auth.get_login_url(request)
        assert result.startswith(raw_login_url)

    def test_get_remote_login_url(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            with patch("nav.web.auth.remote_user._config.get", return_value='foo'):
                result = auth.get_login_url(request)
                assert result == 'foo'

    def test_get_logout_url_default(self):
        r = RequestFactory()
        request = r.get('/')
        result = auth.get_logout_url(request)
        assert result == auth.LOGOUT_URL

    def test_get_remote_logout_url(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            with patch("nav.web.auth.remote_user._config.get", return_value='foo'):
                result = auth.get_logout_url(request)
                assert result == 'foo'


class TestGetRemoteUsername(object):
    def test_no_request(self):
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=False):
            result = remote_user.get_username(None)
            assert result is None

    def test_not_enabled(self):
        r = RequestFactory()
        request = r.get('/')
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=False):
            result = remote_user.get_username(request)
            assert result is None

    def test_enabled_but_remote_user_unset(self):
        r = RequestFactory()
        request = r.get('/')
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            result = remote_user.get_username(request)
            assert result is None

    def test_enabled_and_remote_user_set(self):
        r = RequestFactory()
        request = r.get('/')
        request.META['REMOTE_USER'] = 'knight'
        with patch("nav.web.auth.remote_user._config.getboolean", return_value=True):
            result = remote_user.get_username(request)
            assert result == 'knight'


class TestLoginRemoteUser(object):
    def test_remote_user_unset(self, fake_session):
        r = RequestFactory()
        request = r.get('/')
        request.session = fake_session
        with patch("nav.web.auth.remote_user.get_username", return_value=False):
            remote_user.login(request)
            assert not getattr(request, 'account', False)
            assert ACCOUNT_ID_VAR not in request.session

    def test_remote_user_set(self, fake_session):
        r = RequestFactory()
        request = r.get('/')
        request.session = fake_session
        with patch("nav.web.auth.remote_user.get_username", return_value=True):
            with patch(
                "nav.web.auth.remote_user.authenticate",
                return_value=REMOTE_USER_ACCOUNT,
            ):
                remote_user.login(request)
                assert hasattr(request, 'account')
                account = get_account(request)
                assert account == REMOTE_USER_ACCOUNT
                assert ACCOUNT_ID_VAR in request.session
                assert (
                    request.session.get(ACCOUNT_ID_VAR, None) == REMOTE_USER_ACCOUNT.id
                )


@pytest.mark.skipif(not ldap, reason="ldap module is not available")
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
        u = nav.web.auth.ldap.LDAPUser("zaphod", conn)
        with pytest.raises(nav.web.auth.ldap.UserNotFound):
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
        u = nav.web.auth.ldap.LDAPUser("zaphod", conn)
        u.bind("æøå")

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
        u = nav.web.auth.ldap.LDAPUser("Ægir", conn)
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
@pytest.mark.skipif(not ldap, reason="ldap module is not available")
class TestLdapEntitlements(object):
    def test_required_entitlement_should_be_verified(self, user_zaphod):
        u = nav.web.auth.ldap.LDAPUser("zaphod", user_zaphod)
        assert u.has_entitlement('president')

    def test_missing_entitlement_should_not_be_verified(self, user_marvin):
        u = nav.web.auth.ldap.LDAPUser("marvin", user_marvin)
        assert not u.has_entitlement('president')

    def test_admin_entitlement_should_be_verified(self, user_zaphod):
        u = nav.web.auth.ldap.LDAPUser("zaphod", user_zaphod)
        assert u.is_admin()

    def test_missing_admin_entitlement_should_be_verified(self, user_marvin):
        u = nav.web.auth.ldap.LDAPUser("marvin", user_marvin)
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
    u = nav.web.auth.ldap.LDAPUser("zaphod", user_zaphod)
    assert u.is_admin() is None


#
# Pytest fixtures
#


@pytest.fixture
def user_zaphod():
    return Mock(
        **{
            'search_s.return_value': [
                (
                    'uid=zaphod,cn=users,dc=example,dc=org',
                    {'eduPersonEntitlement': [b'president', b'boss']},
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
                    'uid=marvin,cn=users,dc=example,dc=org',
                    {'eduPersonEntitlement': [b'paranoid']},
                )
            ]
        }
    )
