from __future__ import with_statement
from unittest import TestCase
from nav.ipdevpoll.neighbor import _get_netbox_macs
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
            self.assertTrue(len(result) > 0,
                            msg="Non-VRRP addresses were ignored")
            self.assertFalse(vrrp1 in result or vrrp2 in result,
                             msg="VRRP addresses are present in result")
