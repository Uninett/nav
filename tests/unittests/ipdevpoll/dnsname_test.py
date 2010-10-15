from unittest import TestCase
from minimock import Mock

from nav.ipdevpoll.shadows import Netbox
from nav.ipdevpoll.storage import ContainerRepository
from nav.ipdevpoll.plugins.dnsname import DnsName

class StrangeDnsResponsesTest(TestCase):
    def test_result_with_no_ptr_should_not_set_sysname(self):
        containers = ContainerRepository()
        netbox = containers.factory(None, Netbox)
        netbox.sysname = 'original-sw.example.org'

        netbox_in = Mock('NetBox')
        netbox_in.sysname = 'original-sw.example.org'
        netbox_in.ip = '127.0.0.1'

        plugin = DnsName(netbox_in, Mock('agent'), containers)
        name = plugin._handle_result([[Mock('record')]])

        self.assertEquals(netbox.sysname, 'original-sw.example.org')
