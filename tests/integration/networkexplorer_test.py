from unittest import TestCase
from nav.web.networkexplorer import search
from django.db import transaction

class NetworkExplorerSearchTest(TestCase):
    """Tests that the various network explorer search functions don't raise
    database exceptions.

    Will not cover all code paths on an empty database.

    """
    def setUp(self):
        transaction.enter_transaction_management()
        transaction.managed(True)

    def tearDown(self):
        transaction.rollback()
        transaction.leave_transaction_management()

    def test_search_expand_swport(self):
        search.search_expand_swport(1)

    def test_search_expand_netbox(self):
        search.search_expand_netbox(1)

    def test_search_expand_sysname(self):
        search.search_expand_sysname('foo-gw.example.org')

    def test_search_expand_mac(self):
        search.search_expand_mac('00:12:34:56:78:90')

    def test_sysname_search(self):
        search.sysname_search('foo-gw.example.org')

    def test_ip_search(self):
        search.ip_search('10.0.1')

    def test_ip_search_exact(self):
        search.ip_search('10.0.1.0', exact=True)

    def test_portname_search(self):
        search.portname_search('KX182')

    def test_portname_search_exact(self):
        search.portname_search('KX182', exact=True)

    def test_room_search(self):
        search.room_search('myroom')

    def test_room_search_exact(self):
        search.room_search('myroom', exact=True)

    def test_mac_search(self):
        search.mac_search('00:12:34:56:78:90')

    def test_vlan_search(self):
        search.vlan_search('20')

    def test_vlan_search_exact(self):
        search.vlan_search('20', exact=True)
