"""Raw SNMP SMI module dumps.

As dumped by smidump dump using the python format option.

"""

from itertools import chain
import importlib

from nav.config import NAV_CONFIG
from nav.oids import OID

_mib_map = {}


def get_mib(mib_module):
    """Returns the smidumped MIB definition of a named MIB module, if it exists
    in NAV.

    """
    if not mib_module:
        return None

    if mib_module not in _mib_map:
        for path in get_search_path():
            try:
                name = '.' + mib_module if path else mib_module  # support top namespace
                module = importlib.import_module(name, path)
            except ImportError:
                continue
            else:
                convert_oids(module.MIB)
                _mib_map[mib_module] = module
                break
        else:
            return None

    return _mib_map[mib_module].MIB


def get_search_path():
    """Returns the configured smidumps search path"""
    return NAV_CONFIG.get("SMIDUMPS", "nav.smidumps").split(':')


def convert_oids(mib):
    """Converts a mib data structure's oid strings to OID objects.

    mib is expected to be a data structure as dumped by the smidump utility
    (using the -f python option).

    """
    for node in chain(
        mib.get('nodes', {}).values(), mib.get('notifications', {}).values()
    ):
        if isinstance(node['oid'], str):
            node['oid'] = OID(node['oid'])
