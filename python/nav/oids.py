#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""OID manipulation"""
from __future__ import absolute_import

from django.utils import six

SEPARATOR = '.'
SEPARATOR_B = b'.'


class OID(tuple):
    """Object IDentifier represented in tuple form.

    Example usages:

      >>> ifXTable = OID('.1.3.6.1.2.1.31.1.1')
      >>> ifXTable
      OID('.1.3.6.1.2.1.31.1.1')
      >>> ifName = ifXTable + '1.1'
      >>> ifName
      OID('.1.3.6.1.2.1.31.1.1.1.1')
      >>> ifXTable.is_a_prefix_of(ifName)
      True
      >>> ifName.strip_prefix(ifXTable)
      OID('.1.1')
      >>> str(ifXTable)
      '.1.3.6.1.2.1.31.1.1'
      >>> ifXTable[:3]
      (1, 3, 6)

    """

    def __new__(cls, oid):
        if isinstance(oid, six.string_types):
            oid = map(int, oid.strip(SEPARATOR).split(SEPARATOR))
        elif isinstance(oid, six.binary_type):
            oid = map(int, oid.strip(SEPARATOR_B).split(SEPARATOR_B))
        elif isinstance(oid, OID):
            return oid
        return tuple.__new__(cls, oid)

    def __str__(self):
        return SEPARATOR + SEPARATOR.join([str(i) for i in self])

    def __repr__(self):
        return "OID(%s)" % repr(str(self))

    def __add__(self, other):
        return OID(super(OID, self).__add__(OID(other)))

    def is_a_prefix_of(self, other):
        """Returns True if this OID is a prefix of other"""
        other = OID(other)
        return len(other) > len(self) and other[: len(self)] == self

    def strip_prefix(self, prefix):
        """Returns this OID with prefix stripped.

        If prefix isn't an actual prefix of this OID, this OID is returned
        unchanged.

        """
        prefix = OID(prefix)
        if prefix.is_a_prefix_of(self):
            return OID(self[len(prefix) :])
        else:
            return self


def get_enterprise_id(sysobjectid):
    "Returns the enterprise ID number from a sysObjectID"
    if not sysobjectid:
        return
    enterprises = OID('.1.3.6.1.4.1')
    sysobj = OID(sysobjectid)
    if enterprises.is_a_prefix_of(sysobj):
        return sysobj[len(enterprises)]


def _test():
    import doctest

    doctest.testmod()


if __name__ == "__main__":
    _test()
