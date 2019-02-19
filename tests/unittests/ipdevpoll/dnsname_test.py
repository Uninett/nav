from unittest import TestCase
from mock import Mock

from nav.ipdevpoll.shadows import Netbox
from nav.ipdevpoll.storage import ContainerRepository
from nav.ipdevpoll.plugins.dnsname import DnsName


class StrangeDnsResponsesTest(TestCase):
    def test_empty_result_should_not_set_sysname(self):
        containers = ContainerRepository()
        netbox = containers.factory(None, Netbox)
        netbox.sysname = 'original-sw.example.org'

        netbox_in = Mock('NetBox')
        netbox_in.sysname = 'original-sw.example.org'
        netbox_in.ip = '127.0.0.1'

        plugin = DnsName(netbox_in, Mock('agent'), containers)
        plugin._verify_name_change(None)

        self.assertEqual(netbox.sysname, 'original-sw.example.org')

    def test_response_without_ptr_record_should_translate_to_none(self):
        plugin = DnsName(Mock(), Mock(), Mock())
        self.assertTrue(plugin._find_ptr_response([[Mock()]]) is None)
