import unittest
from mock import Mock, patch
import pytest
import sys

class SnmpTestCase(unittest.TestCase):

    def _patch_cleaning(self, patched_sys_modules_to_modify):
        for module in (
        'nav.Snmp.pynetsnmp', 'nav.Snmp.pysnmp_se', 'nav.Snmp.pysnmp_v2',
        'nav.Snmp.errors', 'nav.Snmp'):
            if module in patched_sys_modules_to_modify:
                del patched_sys_modules_to_modify[module]

    def _import(self, implementation):
        return __import__('nav.Snmp.'+implementation, globals(), locals(),
                          ['Snmp']).Snmp



    def test_load_pynetsnmp_if_available_as_first_choice(self):
        pynetsnmp = Mock()

        modules = {
            'pynetsnmp': pynetsnmp,
            'pynetsnmp.netsnmp' : pynetsnmp.netsnmp,
        }

        with patch.dict(sys.modules, modules):
            self._patch_cleaning(sys.modules)

            # This import should be fine
            from nav.Snmp.pynetsnmp import *

            # wrapper should also be fine to import
            from nav.Snmp import Snmp

            # should be of nav.Snmp.pynetsnmp ...
            assert Snmp == self._import('pynetsnmp')


    def test_load_pysnmp_se_if_pynetsnmp_is_not_available(self):
        pysnmp = Mock()

        modules = {
            'pynetsnmp.netsnmp': None,
            'pynetsnmp': None,
            'pysnmp': pysnmp,
            'pysnmp.asn1': pysnmp.asn1,
            'pysnmp.asn1.oid': pysnmp.asn1.oid,
            'pysnmp.mapping': pysnmp.mapping,
            'pysnmp.mapping.udp': pysnmp.mapping.udp,
            'pysnmp.mapping.udp.role': pysnmp.mapping.udp.role,
            'pysnmp.proto': pysnmp.proto,
            'pysnmp.proto.api': pysnmp.proto.api
        }



        with patch.dict(sys.modules, modules):
            self._patch_cleaning(sys.modules)

            pytest.raises(ImportError, 'import pynetsnmp')
            pytest.raises(ImportError, 'from pynetsnmp import netsnmp')

            # Should not fail.
            from nav.Snmp.pysnmp_se import *

            from nav.Snmp import Snmp

            assert Snmp == self._import('pysnmp_se')

    def raise_pysnmp_error(self, *args):
        raise Exception()

    def test_load_pysnmp_se_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_satisfy(self):
        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.return_value = True
        modules = {
            'pynetsnmp': None,
            'pysnmp': pysnmp,
            'pysnmp.asn1': pysnmp.asn1,
            'pysnmp.asn1.oid': pysnmp.asn1.oid,
            'pysnmp.mapping': pysnmp.mapping,
            'pysnmp.mapping.udp': pysnmp.mapping.udp,
            'pysnmp.mapping.udp.role': pysnmp.mapping.role,
            'pysnmp.proto': pysnmp.proto,
            'pysnmp.proto.api': pysnmp.proto.api
            }



        with patch.dict('sys.modules', modules):
            self._patch_cleaning(sys.modules)

            # Ensure pynetsnmp is unavailable
            pytest.raises(ImportError, 'import pynetsnmp')
            pytest.raises(ImportError, 'from nav.Snmp.pynetsnmp import Snmp')

            # pysnmp version is available
            from pysnmp import version


            from nav.Snmp import Snmp

            assert Snmp == self._import('pysnmp_se')


    def test_load_pysnmp_v2_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_throws_exception__but_doesnt_have_majorVersionId_attribute(self):
        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.side_effect = self.raise_pysnmp_error
        del pysnmp.majorVersionId
        modules = {
            'pynetsnmp': None,
            'pysnmp': pysnmp,
            'pysnmp.asn1': pysnmp.asn1,
            'pysnmp.asn1.oid': pysnmp.asn1.oid,
            'pysnmp.mapping': pysnmp.mapping,
            'pysnmp.mapping.udp': pysnmp.mapping.udp,
            'pysnmp.mapping.udp.role': pysnmp.mapping.role,
            'pysnmp.proto': pysnmp.proto,
            'pysnmp.proto.api': pysnmp.proto.api
            }



        with patch.dict('sys.modules', modules):
            self._patch_cleaning(sys.modules)
            assert not hasattr(pysnmp, 'majorVersionId')


            # Ensure pynetsnmp is unavailable
            pytest.raises(ImportError, 'import pynetsnmp')
            pytest.raises(ImportError, 'from nav.Snmp.pynetsnmp import Snmp')

            # pysnmp version is available
            from pysnmp import version

            from nav.Snmp import Snmp

            assert Snmp == self._import('pysnmp_v2')


    def test_raise_unsupported_pysnmp_backend_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_throws_exception(self):
        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.side_effect = self.raise_pysnmp_error
        pysnmp.majorVersionId = '4'

        modules = {
            'pynetsnmp': None,
            'pysnmp': pysnmp,
            'pysnmp.asn1': pysnmp.asn1,
            'pysnmp.asn1.oid': pysnmp.asn1.oid,
            'pysnmp.mapping': pysnmp.mapping,
            'pysnmp.mapping.udp': pysnmp.mapping.udp,
            'pysnmp.mapping.udp.role': pysnmp.mapping.role,
            'pysnmp.proto': pysnmp.proto,
            'pysnmp.proto.api': pysnmp.proto.api
            }



        with patch.dict('sys.modules', modules):
            self._patch_cleaning(sys.modules)
            assert hasattr(pysnmp, 'majorVersionId')
            assert pysnmp.majorVersionId == '4'

            # Ensure pynetsnmp is unavailable
            pytest.raises(ImportError, 'import pynetsnmp')
            pytest.raises(ImportError, 'from nav.Snmp.pynetsnmp import *')

            # pysnmp version is available
            from pysnmp import version

            try:
                from nav.Snmp import Snmp
                pytest.fail("Should never happen")
            except ImportError, e:
                assert unicode(e) == "Unsupported PySNMP version 4"


    def test_raise_no_supported_snmp_backend_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_throws_exception_and_fails_with_having_majorVersionId_attr(self):
        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.side_effect = self.raise_pysnmp_error
        modules = {
            'pynetsnmp': None,
            'pysnmp': pysnmp,
            'pysnmp.asn1': pysnmp.asn1,
            'pysnmp.asn1.oid': pysnmp.asn1.oid,
            'pysnmp.mapping': pysnmp.mapping,
            'pysnmp.mapping.udp': pysnmp.mapping.udp,
            'pysnmp.mapping.udp.role': pysnmp.mapping.role,
            'pysnmp.proto': pysnmp.proto,
            'pysnmp.proto.api': pysnmp.proto.api
            }



        with patch.dict(sys.modules, modules):
            self._patch_cleaning(sys.modules)

            # Ensure pynetsnmp is unavailable
            pytest.raises(ImportError, 'import pynetsnmp')
            pytest.raises(ImportError, 'from nav.Snmp.pynetsnmp import *')

            # pysnmp version is available
            from pysnmp import version

            pytest.raises(ImportError, 'from nav.Snmp import Snmp')


    def test_raise_no_supported_snmp_backend_found_raised_if_no_snmp_libraries_are_available(self):
        modules = {
            'pynetsnmp': None,
            'pysnmp': None
        }

        with patch.dict(sys.modules, modules):
            self._patch_cleaning(sys.modules)
            pytest.raises(ImportError, 'import pynetsnmp')
            pytest.raises(ImportError, 'import pysnmp')

            pytest.raises(ImportError, 'from nav.Snmp.pynetsnmp import *')
            pytest.raises(ImportError, 'from nav.Snmp.pysnmp_se import *')
            pytest.raises(ImportError, 'from nav.Snmp.pysnmp_v2 import *')

            try:
                from nav.Snmp import Snmp
                pytest.fail("Should never happen")
            except ImportError, foo:
                assert str(foo) == 'No supported SNMP backend was found'

