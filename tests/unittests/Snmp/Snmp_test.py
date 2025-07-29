# ruff: noqa: F401 - importing to test availability

import unittest
from mock import Mock, patch
import pytest
import sys


class SnmpTestCase(unittest.TestCase):
    def _patch_cleaning(self, patched_sys_modules_to_modify):
        for module in ('nav.Snmp.pynetsnmp', 'nav.Snmp.errors', 'nav.Snmp'):
            if module in patched_sys_modules_to_modify:
                del patched_sys_modules_to_modify[module]

    def _import(self, implementation):
        return __import__(
            'nav.Snmp.' + implementation, globals(), locals(), ['Snmp']
        ).Snmp


class SnmpTestPynetsnmp(SnmpTestCase):
    def setUp(self):
        self.pynetsnmp = Mock(name='pynetsnmp')
        self.modules = {
            'pynetsnmp': self.pynetsnmp,
            'pynetsnmp.netsnmp': self.pynetsnmp.netsnmp,
        }
        self.patcher = patch.dict(sys.modules, self.modules)
        self.patcher.start()
        self._patch_cleaning(sys.modules)

    def tearDown(self):
        for name, module in self.modules.items():
            assert sys.modules[name] == module
        self.patcher.stop()

    def test_load_pynetsnmp_if_available_as_first_choice(self):
        # This import should be fine
        import nav.Snmp.pynetsnmp as _

        # wrapper should also be fine to import
        from nav.Snmp import Snmp

        # should be of nav.Snmp.pynetsnmp ...
        assert Snmp == self._import('pynetsnmp')


class OtherSnmpTests(SnmpTestCase):
    def test_raise_no_supported_snmp_backend_found_raised_if_no_snmp_libraries_are_available(  # noqa: E501
        self,
    ):
        modules = {
            'pynetsnmp': None,
        }

        with patch.dict(sys.modules, modules):
            self._patch_cleaning(sys.modules)
            with pytest.raises(ImportError):
                import pynetsnmp

            with pytest.raises(ImportError):
                import nav.Snmp.pynetsnmp

            try:
                from nav.Snmp import Snmp

                pytest.fail("Should never happen")
            except ImportError as foo:
                assert str(foo) == 'No supported SNMP backend was found'
