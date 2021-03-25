from unittest import TestCase
from nav.ipdevpoll.neighbor import _get_netbox_macs
from nav.ipdevpoll.plugins.cdp import CDPNeighbor
from mock import patch, Mock


class IgnoredMacTest(TestCase):
    def test_vrrp_addresses_are_ignored(self):
        with patch('django.db.connection') as cx:
            vrrp1 = '00:00:5e:00:01:28'
            vrrp2 = '00:00:5e:00:02:19'
            my_cursor = Mock()
            my_cursor.fetchall.return_value = [
                ('00:12:34:56:78:9a', 1),
                (vrrp1, 2),
                (vrrp2, 3),
            ]
            cx.cursor.return_value = my_cursor
            result = _get_netbox_macs()
            self.assertTrue(len(result) > 0, msg="Non-VRRP addresses were ignored")
            self.assertFalse(
                vrrp1 in result or vrrp2 in result,
                msg="VRRP addresses are present in result",
            )


class _MockedCDPNeighbor(CDPNeighbor):
    def identify(self):
        # bypass the regular identification routine on instantiation
        pass


class IgnoreCDPSelfLoopsTest(TestCase):
    def test_apparent_cdp_self_loop_should_be_ignored(self):
        test_ip = '10.0.1.41'
        neighbor = _MockedCDPNeighbor(None, test_ip)
        self.assertTrue(neighbor._netbox_from_ip(test_ip) is None)
