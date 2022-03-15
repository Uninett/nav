from unittest import TestCase
from mock import Mock
from IPy import IP
from random import randint

from nav.ipdevpoll.plugins import prefix


class IgnoredPrefixConfigTest(TestCase):
    def test_single_prefix(self):
        config = Mock()
        config.get.return_value = '127.0.0.0/8'

        result = prefix.get_ignored_prefixes(config)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0] is not None)
        self.assertEqual(result[0], IP('127.0.0.0/8'))

    def test_two_prefixes(self):
        config = Mock()
        config.get.return_value = '127.0.0.0/8, fe80::/16'

        expected = [IP('127.0.0.0/8'), IP('fe80::/16')]
        result = prefix.get_ignored_prefixes(config)

        self.assertEqual(len(result), 2)
        self.assertTrue(result[0] is not None)
        self.assertTrue(result[1] is not None)
        self.assertTrue(result[0] in expected)
        self.assertTrue(result[1] in expected)

    def test_invalid_prefix_should_be_silently_ignored(self):
        config = Mock()
        config.get.return_value = '127.0.0.1/8, fe80::/16'

        result = prefix.get_ignored_prefixes(config)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0] is not None)
        self.assertEqual(result[0], IP('fe80::/16'))

    def test_prefix_with_match_specifier_should_parse(self):
        config = Mock()
        config.get.return_value = '=10.0.0.0/23'

        result = prefix.get_ignored_prefixes(config)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], IP('10.0.0.0/23'))

    def test_prefix_with_match_specifier_should_parse2(self):
        config = Mock()
        config.get.return_value = '=10.0.0.0/23, <<=10.1.0.0/23'

        expected = [IP('10.0.0.0/23'), IP('10.1.0.0/23')]
        result = prefix.get_ignored_prefixes(config)
        self.assertEqual(len(result), 2)
        self.assertIn(result[0], expected)
        self.assertIn(result[1], expected)


class IgnoredPrefixTest(TestCase):
    def test_contained_in_default_match(self):
        pfx = prefix.IgnoredPrefix('192.168.1.0/24')
        self.assertTrue(pfx.matches('192.168.1.128/25'))
        self.assertFalse(pfx.matches('192.168.2.128/25'))

    def test_contained_in_operator_match(self):
        pfx = prefix.IgnoredPrefix('<<=192.168.1.0/24')
        self.assertTrue(pfx.matches('192.168.1.128/25'))
        self.assertFalse(pfx.matches('192.168.2.128/25'))

    def test_contained_in_equals_match(self):
        pfx = prefix.IgnoredPrefix('=192.168.1.0/24')
        self.assertTrue(pfx.matches('192.168.1.0/24'))
        self.assertFalse(pfx.matches('192.168.1.128/25'))


class PrefixPluginTest(TestCase):
    def test_instantiation(self):
        netbox = Mock('Netbox')
        netbox.sysname = 'foo-sw.example.org'
        plugin = prefix.Prefix(netbox, None, None)


class VlanPatternTest(TestCase):
    def setUp(self):
        self.vlan = str(randint(0, 4096))

    def test_cisco_long_names_should_match(self):
        match = prefix.VLAN_PATTERN.match("VLAN" + self.vlan)
        self.assertEqual(match.group('vlan'), self.vlan)

    def test_cisco_short_names_should_match(self):
        match = prefix.VLAN_PATTERN.match("Vl" + self.vlan)
        self.assertEqual(match.group('vlan'), self.vlan)

    def test_juniper_irb_names_should_match(self):
        match = prefix.VLAN_PATTERN.match("irb." + self.vlan)

    def test_juniper_reth_names_should_match(self):
        match = prefix.VLAN_PATTERN.match("reth0." + self.vlan)
        self.assertEqual(match.group('vlan'), self.vlan)
