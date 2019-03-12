# -*- coding: utf-8 -*-
from mock import patch, MagicMock, Mock
from django.utils import six

import pytest

import nav.web.ldapauth
from nav.web import auth

LDAP_ACCOUNT = auth.Account(login='knight', ext_sync='ldap',
                            password='shrubbery')
PLAIN_ACCOUNT = auth.Account(login='knight', password='shrubbery')
REMOTE_USER_ACCOUNT = auth.Account(login='knight', ext_sync='REMOTE_USER',
                                   password='shrubbery')


@patch("nav.web.auth.Account.save", new=MagicMock(return_value=True))
@patch("nav.web.auth.Account.objects.get",
       new=MagicMock(return_value=LDAP_ACCOUNT))
class TestLdapAuthenticate(object):
    def test_authenticate_should_return_account_when_ldap_says_yes(self):
        with patch("nav.web.ldapauth.available", new=True):
            with patch("nav.web.ldapauth.authenticate", return_value=True):
                assert auth.authenticate('knight', 'shrubbery') == LDAP_ACCOUNT

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        with patch("nav.web.ldapauth.available", new=True):
            with patch("nav.web.ldapauth.authenticate", return_value=False):
                assert not auth.authenticate('knight', 'shrubbery')

    def test_authenticate_should_fallback_when_ldap_is_disabled(self):
        with patch("nav.web.ldapauth.available", new=False):
            assert auth.authenticate('knight', 'shrubbery') == LDAP_ACCOUNT


@patch("nav.web.auth.Account.save", new=MagicMock(return_value=True))
@patch("nav.web.auth.Account.objects.get",
       new=MagicMock(return_value=PLAIN_ACCOUNT))
@patch("nav.web.ldapauth.available", new=False)
class TestNormalAuthenticate(object):
    def test_authenticate_should_return_account_when_password_is_ok(self):
        with patch("nav.web.auth.Account.check_password", return_value=True):
            assert auth.authenticate('knight', 'shrubbery') == PLAIN_ACCOUNT

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        with patch("nav.web.auth.Account.check_password", return_value=False):
            assert not auth.authenticate('knight', 'rabbit')


class TestRemoteUserAuthenticate(object):
    class FakeRequest(object):

        def __init__(self, **kwargs):
            self.META = {}
            self.META.update(**kwargs)

    def test_authenticate_remote_user_should_return_account_if_header_set(self):
        request = self.FakeRequest(REMOTE_USER='knight')
        with patch.dict("nav.web.auth.NAV_CONFIG", {'AUTH_SUPPORT_REMOTE_USER': True}):
            with patch("nav.web.auth.Account.objects.get",
                       new=MagicMock(return_value=REMOTE_USER_ACCOUNT)):
                assert auth.authenticate_remote_user(request) == REMOTE_USER_ACCOUNT

    def test_authenticate_remote_user_should_return_none_if_header_not_set(self):
        request = self.FakeRequest()
        with patch.dict("nav.web.auth.NAV_CONFIG", {'AUTH_SUPPORT_REMOTE_USER': True}):
            assert auth.authenticate_remote_user(request) == None

    def test_authenticate_remote_user_should_return_false_if_account_locked(self):
        request = self.FakeRequest(REMOTE_USER='knight')
        with patch.dict("nav.web.auth.NAV_CONFIG", {'AUTH_SUPPORT_REMOTE_USER': True}):
            with patch("nav.web.auth.Account.objects.get",
                       new=MagicMock(return_value=REMOTE_USER_ACCOUNT)):
                with patch("nav.web.auth.Account.locked", return_value=True):
                    assert auth.authenticate_remote_user(request) == False


class TestLdapUser(object):
    @patch.dict("nav.web.ldapauth._config._sections",
                {'ldap': {'__name__': 'ldap',
                          'basedn': 'empty',
                          'manager': 'empty',
                          'manager_password': 'empty',
                          'uid_attr': 'sAMAccountName',
                          'encoding': 'utf-8'},
                 })
    def test_search_result_with_referrals_should_be_considered_empty(self):
        """LP#1207737"""
        conn = Mock(**{
            'search_s.return_value': [(None, "restaurant"),
                                      (None, "at the end of the universe")]
        })
        u = nav.web.ldapauth.LDAPUser("zaphod", conn)
        with pytest.raises(nav.web.ldapauth.UserNotFound):
            u.search_dn()

    @patch.dict("nav.web.ldapauth._config._sections",
                {'ldap': {'__name__': 'ldap',
                          'basedn': 'empty',
                          'lookupmethod': 'direct',
                          'uid_attr': 'uid',
                          'encoding': 'utf-8',
                          'suffix': ''}
                 })
    def test_non_ascii_password_should_work(self):
        """LP#1213818"""
        conn = Mock(**{
            'simple_bind_s.side_effect': lambda x, y: (six.text_type(x), six.text_type(y)),
        })
        u = nav.web.ldapauth.LDAPUser(u"zaphod", conn)
        u.bind(u"æøå")

    @patch.dict("nav.web.ldapauth._config._sections",
                {'ldap': {'__name__': 'ldap',
                          'basedn': 'cn=users,dc=example,dc=org',
                          'lookupmethod': 'direct',
                          'uid_attr': 'uid',
                          'encoding': 'utf-8',
                          'group_search': '(member=%%s)' },
                 })
    def test_is_group_member_for_non_ascii_user_should_not_raise(self):
        """LP#1301794"""
        def fake_search(base, scope, filtr):
            six.text_type(base)
            six.text_type(filtr)
            return []

        conn = Mock(**{
            'search_s.side_effect': fake_search,
        })
        u = nav.web.ldapauth.LDAPUser(u"Ægir", conn)
        u.is_group_member('cn=noc-operators,cn=groups,dc=example,dc=com')
