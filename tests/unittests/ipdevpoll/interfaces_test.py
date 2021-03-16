from unittest import TestCase
from mock import Mock
from django.utils import six

import pytest

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


class TestExtractInterfaceSpeed:
    def test_should_use_highspeed_value_when_speed_is_maxed_out(self):
        assert Interfaces._extract_interface_speed(4294967295, 10000) == pytest.approx(
            10000.0
        )

    def test_should_use_speed_value_when_not_maxed_out(self):
        assert Interfaces._extract_interface_speed(1073741824, 0) == pytest.approx(
            1073.741824
        )

    def test_should_use_highspeed_value_when_equal_to_speed(self):
        """Tests the behavior when agent implementation is buggy"""
        assert Interfaces._extract_interface_speed(1000, 1000) == pytest.approx(1000.0)
