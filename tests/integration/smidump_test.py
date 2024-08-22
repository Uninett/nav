"""Regression tests to validate smidump file contents"""

import os

import pynetsnmp.netsnmp
import pytest

from nav.Snmp.pynetsnmp import Snmp
from nav.Snmp import errors
from nav.smidumps import get_mib


#
# Parametrization helpers
#


def get_smi_dumps():
    """Returns a list of all MIB modules found in the nav.smidump namespace"""
    import nav.smidumps

    directory = os.path.dirname(nav.smidumps.__file__)
    files = [f for f in os.listdir(directory) if f.endswith('.py') and f[0] not in '_.']
    modules = [os.path.splitext(f)[0] for f in files]
    return set(modules)


#
# Tests
#


@pytest.mark.parametrize("smidump", get_smi_dumps())
def test_all_oids_in_smidumped_mib_should_be_valid(smidump, validator):
    """Naively tests that all OIDs represented in an smidumped MIB module is encodeable
    by NET-SNMP. Specifically written to discover issues with incomplete MIB information
    as described in https://github.com/Uninett/nav/issues/2494
    """
    mib = get_mib(smidump)
    for node in mib['nodes'].values():
        assert validator(node['oid']), "{} seems to contain invalid OID {}".format(
            smidump, node['oid']
        )


#
# Fixtures
#


@pytest.fixture(scope="session")
def validator():
    """Returns a session-scoped OID validator function"""
    snmp = Snmp('0.0.0.0', version='2c', timeout=0.0001)

    def is_valid(oid):
        """Attempts to send an SNMP get operation using NET-SNMP, translating
        failures to a False result and success to True
        """
        try:
            # Uses the internal handle to avoid synchronously waiting for a response
            # that will never come
            snmp.handle.get([oid])
        except (errors.SnmpError, pynetsnmp.netsnmp.SnmpError) as err:
            print(err)
            return False
        return True

    return is_valid
