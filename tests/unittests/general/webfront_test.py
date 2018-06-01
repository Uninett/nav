# -*- coding: utf-8 -*-
from unittest import TestCase
from mock import patch, Mock
from django.utils import six

import nav.web.ldapauth
from nav.web import auth


class LdapAuthenticateTest(TestCase):
    def setUp(self):
        self.ldap_available = nav.web.ldapauth.available
        nav.web.ldapauth.available = True

        self.patched_save = patch("nav.web.auth.Account.save",
                                  return_value=True)
        self.patched_save.start()

        self.mock_account = auth.Account(login='knight', ext_sync='ldap',
                                         password='shrubbery')
        self.patched_get = patch("nav.web.auth.Account.objects.get",
                                 return_value=self.mock_account)
        self.patched_get.start()

    def tearDown(self):
        nav.web.ldapauth.available = self.ldap_available
        self.patched_save.stop()
        self.patched_get.stop()

    def test_authenticate_should_return_account_when_ldap_says_yes(self):
        with patch("nav.web.ldapauth.authenticate", return_value=True):
            self.assertEquals(auth.authenticate('knight', 'shrubbery'),
                              self.mock_account)

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        with patch("nav.web.ldapauth.authenticate", return_value=False):
            self.assertFalse(auth.authenticate('knight', 'shrubbery'))

    def test_authenticate_should_fallback_when_ldap_is_disabled(self):
        nav.web.ldapauth.available = False
        self.assertEquals(auth.authenticate('knight', 'shrubbery'),
                          self.mock_account)


class NormalAuthenticateTest(TestCase):
    def setUp(self):
        self.ldap_available = nav.web.ldapauth.available
        nav.web.ldapauth.available = False
        self.patched_save = patch("nav.web.auth.Account.save",
                                  return_value=True)
        self.patched_save.start()

        self.mock_account = auth.Account(login='knight', password='shrubbery')
        self.patched_get = patch("nav.web.auth.Account.objects.get",
                                 return_value=self.mock_account)
        self.patched_get.start()

    def tearDown(self):
        nav.web.ldapauth.available = self.ldap_available
        self.patched_save.stop()
        self.patched_get.stop()

    def test_authenticate_should_return_account_when_password_is_ok(self):
        with patch("nav.web.auth.Account.check_password", return_value=True):
            self.assertEquals(auth.authenticate('knight', 'shrubbery'),
                              self.mock_account)

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        with patch("nav.web.auth.Account.check_password", return_value=False):
            self.assertFalse(auth.authenticate('knight', 'rabbit'))


class LdapUserTestCase(TestCase):
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
        self.assertRaises(nav.web.ldapauth.UserNotFound, u.search_dn)

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
