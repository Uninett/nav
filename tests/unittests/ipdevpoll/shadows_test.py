from unittest import TestCase
from nav.ipdevpoll.storage import ContainerRepository
from nav.ipdevpoll.shadows import Vlan, Prefix, Netbox
from mock import patch

class MixedNetTypeTest(TestCase):
    """Tests for guesstimation of net_type on Vlan's with mixed prefixes"""

    def setUp(self):
        repo = ContainerRepository()
        netbox = repo.factory(None, Netbox)
        netbox.id = 1
        vlan = repo.factory('20', Vlan)

        for addr in ('2001:700:1::/64', '10.0.1.0/30', 'fe80::/64'):
            prefix = repo.factory(addr, Prefix)
            prefix.vlan = vlan
            prefix.net_address = addr

        self.vlan = vlan
        self.repo = repo

    def test_link_net_with_big_ipv6_addr(self):
        with patch.object(self.vlan, '_get_router_count_for_prefix') as rcount:
            rcount.return_value = 2
            net_type = self.vlan._guesstimate_net_type(self.repo)
            self.assertIsNotNone(net_type)
            self.assertEqual("link", net_type.id)

    def test_elink_net_with_big_ipv6_addr(self):
        with patch.object(self.vlan, '_get_router_count_for_prefix') as rcount:
            rcount.return_value = 1
            net_type = self.vlan._guesstimate_net_type(self.repo)
            self.assertIsNotNone(net_type)
            self.assertEqual("elink", net_type.id)
