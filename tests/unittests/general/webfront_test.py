from unittest import TestCase
from mock import patch

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
