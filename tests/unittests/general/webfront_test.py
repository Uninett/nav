from unittest import TestCase
from minimock import mock, Mock, restore

import nav.web.ldapAuth
from nav.web import auth

class LdapAuthenticateTest(TestCase):
    def setUp(self):
        self.ldap_available = nav.web.ldapAuth.available
        nav.web.ldapAuth.available = True
        mock("nav.web.auth.Account.save", returns=True)

    def tearDown(self):
        nav.web.ldapAuth.available = self.ldap_available
        restore()

    def test_authenticate_should_return_account_when_ldap_says_yes(self):
        mock("nav.web.ldapAuth.authenticate", returns=True)
        mock_account = auth.Account(login='knight', ext_sync='ldap',
                                    password='shrubbery')
        mock("nav.web.auth.Account.objects.get", returns=mock_account)

        self.assertEquals(auth.authenticate('knight', 'shrubbery'), mock_account)

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        mock("nav.web.ldapAuth.authenticate", returns=False)
        mock_account = auth.Account(login='knight', ext_sync='ldap',
                                    password='shrubbery')
        mock("nav.web.auth.Account.objects.get", returns=mock_account)

        self.assertFalse(auth.authenticate('knight', 'shrubbery'))

    def test_authenticate_should_fallback_when_ldap_is_disabled(self):
        nav.web.ldapAuth.available = False
        mock_account = auth.Account(login='knight', ext_sync='ldap',
                                    password='shrubbery')
        mock("nav.web.auth.Account.objects.get", returns=mock_account)

        self.assertEquals(auth.authenticate('knight', 'shrubbery'),
                          mock_account)


class NormalAuthenticateTest(TestCase):
    def setUp(self):
        self.ldap_available = nav.web.ldapAuth.available
        nav.web.ldapAuth.available = False
        mock("nav.web.auth.Account.save", returns=True)

    def tearDown(self):
        nav.web.ldapAuth.available = self.ldap_available
        restore()

    def test_authenticate_should_return_account_when_password_is_ok(self):
        mock("nav.web.auth.Account.check_password", returns=True)
        mock_account = auth.Account(login='knight', password='shrubbery')
        mock("nav.web.auth.Account.objects.get", returns=mock_account)

        self.assertEquals(auth.authenticate('knight', 'shrubbery'),
                          mock_account)

    def test_authenticate_should_return_false_when_ldap_says_no(self):
        mock("nav.web.auth.Account.check_password", returns=False)
        mock_account = auth.Account(login='knight', password='shrubbery')
        mock("nav.web.auth.Account.objects.get", returns=mock_account)

        self.assertFalse(auth.authenticate('knight', 'rabbit'))
