import unittest
from mock import Mock, patch, MagicMock
import nav
import pytest
import sys


class SnmpTests(unittest.TestCase):
    def _rm_module(self, module):
        if module in sys.modules:
            del sys.modules[module]

    def _clean(self):
        modules_to_reload = (
            'pynetsnmp.netsnmp',
            'pynetsnmp',
            'pysnmp',
            'pysnmp.asn1',
            'pysnmp.asn1.oid',
            'pysnmp.mapping',
            'pysnmp.mapping.udp',
            'pysnmp.mapping.udp.role',
            'pysnmp.proto',
            'pysnmp.proto.api',
            'nav.Snmp',
        )

        for module in modules_to_reload:
            self._rm_module(module)

    def tearDown(self):
        self._clean()

    def test_load_pynetsnmp_if_available_as_first_choice(self):
        pynetsnmp = Mock()

        modules = {
            'pynetsnmp': pynetsnmp,
            'pynetsnmp.netsnmp' : pynetsnmp.netsnmp
        }
        with patch.dict('sys.modules', modules):

            # This import should be fine
            from nav.Snmp.pynetsnmp import *

            # wrapper should also be fine to import
            from nav.Snmp import Snmp

            # should be of nav.Snmp.pynetsnmp ...
            assert Snmp == nav.Snmp.pynetsnmp.Snmp



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



        with patch.dict('sys.modules', modules):
            pytest.raises(ImportError, 'import pynetsnmp')
            pytest.raises(ImportError, 'from pynetsnmp import netsnmp')

            # Should not fail.
            from nav.Snmp.pysnmp_se import *

            from nav.Snmp import Snmp

            assert Snmp == nav.Snmp.pysnmp_se.Snmp


    def raise_pysnmp_error(self, *args):
        raise Exception()


    def test_load_pysnmp_se_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_satisfy_using_v2_environment(self):
        import os
        os.environ.__getitem__ = Mock(return_value='v2')


        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.return_value = True
        modules = {
            'os': os,
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
            assert os.environ['PYSNMP_API_VERSION'] == 'v2'

            # Ensure pynetsnmp is unavailable
            pytest.raises(ImportError, 'import pynetsnmp')

            # pysnmp version is available
            from pysnmp import version


            from nav.Snmp import Snmp

            assert Snmp == nav.Snmp.pysnmp_se.Snmp


    def test_load_pysnmp_se_if_pynetsnmp_unavaialble_and_pysnmp_version_requirement_satisfy_using_v3_environment(self):
        import os
        os.environ.__getitem__ = Mock(return_value='v3')


        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.return_value = True
        modules = {
            'os': os,
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
            assert os.environ['PYSNMP_API_VERSION'] == 'v3'

            # Ensure pynetsnmp is unavailable
            pytest.raises(ImportError, 'import pynetsnmp')

            # pysnmp version is available
            from pysnmp import version

            from nav.Snmp import Snmp

            assert Snmp == nav.Snmp.pysnmp_se.Snmp

    def test_load_pysnmp_v2_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_throws_exception_using_v2_environment_but_doesnt_have_majorVersionId_attribute(self):
        import os
        os.environ.__getitem__ = Mock(return_value='v2')


        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.side_effect = self.raise_pysnmp_error
        del pysnmp.majorVersionId
        modules = {
            'os': os,
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
            assert os.environ['PYSNMP_API_VERSION'] == 'v2'
            assert not hasattr(pysnmp, 'majorVersionId')


            # Ensure pynetsnmp is unavailable
            pytest.raises(ImportError, 'import pynetsnmp')

            # pysnmp version is available
            from pysnmp import version

            from nav.Snmp import Snmp

            assert Snmp == nav.Snmp.pysnmp_v2.Snmp


    def test_raise_unsupported_pysnmp_backend_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_throws_exception_using_v2_environment(self):
        import os
        os.environ.__getitem__ = Mock(return_value='v2')


        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.side_effect = self.raise_pysnmp_error
        pysnmp.majorVersionId = '4'



        modules = {
            'os': os,
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
            assert os.environ['PYSNMP_API_VERSION'] == 'v2'
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

    def test_raise_unsupported_pysnmp_backend_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_throws_exception_using_v3_environment(self):
        import os
        os.environ.__getitem__ = Mock(return_value='v3')


        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.side_effect = self.raise_pysnmp_error
        pysnmp.majorVersionId = '4'



        modules = {
            'os': os,
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
            assert os.environ['PYSNMP_API_VERSION'] == 'v3'
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

    def test_raise_no_supported_snmp_backend_if_pynetsnmp_unavailable_and_pysnmp_version_requirement_throws_exception_using_v3_environment_and_fails_with_having_majorVersionId_attr(self):
        import os
        os.environ.__getitem__ = Mock(return_value='v3')


        pysnmp = Mock(name='pysnmp root')
        pysnmp.version.verifyVersionRequirement.side_effect = self.raise_pysnmp_error
        modules = {
            'os': os,
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
            assert os.environ['PYSNMP_API_VERSION'] == 'v3'

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

        with patch.dict('sys.modules', modules):
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

