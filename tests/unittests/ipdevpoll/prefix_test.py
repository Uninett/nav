from unittest import TestCase
from minimock import Mock
from IPy import IP

from nav.ipdevpoll.plugins import prefix

class IgnoredPrefixTest(TestCase):
    def test_single_prefix(self):
        config = Mock('ConfigParser')
        config.get = Mock('get', returns = '127.0.0.0/8')

        result = prefix.get_ignored_prefixes(config)
        self.assertEquals(len(result), 1)
        self.assertTrue(result[0] is not None)
        self.assertEquals(result[0], IP('127.0.0.0/8'))

    def test_two_prefixes(self):
        config = Mock('ConfigParser')
        config.get = Mock('get', returns = '127.0.0.0/8, fe80::/16')

        expected = [IP('127.0.0.0/8'), IP('fe80::/16')]
        result = prefix.get_ignored_prefixes(config)

        self.assertEquals(len(result), 2)
        self.assertTrue(result[0] is not None)
        self.assertTrue(result[1] is not None)
        self.assertTrue(result[0] in expected)
        self.assertTrue(result[1] in expected)

    def test_invalid_prefix_shoule_be_silently_ignored(self):
        config = Mock('ConfigParser')
        config.get = Mock('get', returns = '127.0.0.1/8, fe80::/16')

        result = prefix.get_ignored_prefixes(config)
        self.assertEquals(len(result), 1)
        self.assertTrue(result[0] is not None)
        self.assertEquals(result[0], IP('fe80::/16'))


class PrefixPluginTest(TestCase):
    def test_instantiation(self):
        netbox = Mock('Netbox')
        netbox.sysname = 'foo-sw.example.org'
        plugin = prefix.Prefix(netbox, None, None)
