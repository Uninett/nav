import unittest
from nav.models.profiles import Account


class AccountTest(unittest.TestCase):
    def setUp(self):
        self.admin_user = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
        self.default_user = Account.objects.get(pk=Account.DEFAULT_ACCOUNT)

    def test_is_admin_returns_true_if_administrator(self):
        self.assertTrue(self.admin_user.is_admin())

    def test_is_admin_returns_false_if_default_account(self):
        self.assertFalse(self.default_user.is_admin())
