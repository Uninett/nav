"""Raw SNMP SMI module dumps.

As dumped by smidump dump using the python format option.

"""
from __future__ import absolute_import

from itertools import chain
import importlib

from django.utils import six

from nav.oids import OID

_mib_map = {}


def get_mib(mib_module):
    """Returns the smidumped MIB definition of a named MIB module, if it exists
    in NAV.

    """
    if not mib_module:
        return None

    if mib_module not in _mib_map:
        try:
            module = importlib.import_module('.' + mib_module, 'nav.smidumps')
            convert_oids(module.MIB)
            _mib_map[mib_module] = module
        except ImportError:
            return None

    return _mib_map[mib_module].MIB


def convert_oids(mib):
    """Converts a mib data structure's oid strings to OID objects.

    mib is expected to be a data structure as dumped by the smidump utility
    (using the -f python option).

    """
    for node in chain(
        mib.get('nodes', {}).values(),
        mib.get('notifications', {}).values()
    ):
        if isinstance(node['oid'], six.string_types):
            node['oid'] = OID(node['oid'])
