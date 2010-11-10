from unittest import TestCase
from minimock import Mock

from nav.ipdevpoll.storage import ContainerRepository
from nav.ipdevpoll.plugins.interfaces import Interfaces, decode_to_unicode

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
        self.assertTrue(isinstance(interface.ifalias, unicode))

    def test_latin1_encoded_ifalias_should_be_properly_decoded(self):
        result = decode_to_unicode('A m\xf8\xf8se once bit my sister')
        expected = u'A m\xf8\xf8se once bit my sister'
        self.assertEquals(result, expected)

    def test_utf_8_encoded_ifalias_should_be_properly_decoded(self):
        result = decode_to_unicode('A m\xc3\xb8\xc3\xb8se once bit my sister')
        expected = u'A m\xf8\xf8se once bit my sister'
        self.assertEquals(result, expected)

    def test_none_should_be_returned_unchanged(self):
        result = decode_to_unicode(None)
        self.assertTrue(result is None)

    def test_unknown_encoding_should_not_raise_error(self):
        result = decode_to_unicode('A m\x9b\x9bse once bit my sister')
        self.assertTrue(isinstance(result, unicode))

    def test_number_should_be_encoded(self):
        result = decode_to_unicode(42)
        self.assertEquals(result, "42")
