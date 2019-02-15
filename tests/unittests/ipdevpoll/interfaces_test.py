from unittest import TestCase
from mock import Mock
from django.utils import six

from nav.ipdevpoll.storage import ContainerRepository
from nav.ipdevpoll.plugins.interfaces import Interfaces


class EncodingTests(TestCase):
    def test_ifalias_should_be_unicode(self):
        netbox = Mock('Netbox')
        agent = Mock('AgentProxy')
        containers = ContainerRepository()
        plugin = Interfaces(netbox, agent, containers)

        row = {
            'ifDescr': 'GigabitEthernet0/1',
            'ifName': 'Gi0/1',
            'ifAlias': 'The Larch',
            }
        required_keys = ('ifType', 'ifSpeed', 'ifSpeed', 'ifHighSpeed',
                         'ifAdminStatus', 'ifOperStatus', 'ifPhysAddress',
                         'ifConnectorPresent')
        for k in required_keys:
            row[k] = None

        interface = plugin._convert_row_to_container(netbox, 1, row)
        self.assertTrue(isinstance(interface.ifalias, six.text_type))
