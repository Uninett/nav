from nav.models.manage import Prefix
from mock import patch
from nav.web.ipam.util import get_available_subnets
from nav.tests.cases import DjangoTransactionTestCase
from IPy import IP, IPSet


class UtilTestCase(DjangoTransactionTestCase):
    fixtures = ["prefixes.xml"]

    def setUp(self):
        super(UtilTestCase, self).setUp()

    def tearDown(self):
        pass


class getAvailableSubnets(UtilTestCase):
    def test_get_available_subnets(self):
        available = get_available_subnets("10.0.160.0/19")
        self.assertTrue(available is not None)
        # only 10.0.160.0/21 should be available
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0], IP("10.0.160.0/21"))
