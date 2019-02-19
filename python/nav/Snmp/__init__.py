#
# Copyright (C) 2010, 2013 Uninett AS
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
"""A high level interface for synchronouse SNMP operations in NAV.

This interface only supports pynetsnmp, but is designed to allow
multiple implementations

"""
from __future__ import absolute_import
from django.utils import six

BACKEND = None

try:
    # our highest preference is pynetsnmp, since it can support IPv6
    import pynetsnmp
except ImportError:
    pass
else:
    BACKEND = 'pynetsnmp'

# These wildcard imports are informed, not just accidents.
# pylint: disable=W0401
if BACKEND == 'pynetsnmp':
    from .pynetsnmp import *
else:
    raise ImportError("No supported SNMP backend was found")


def safestring(string, encodings_to_try=('utf-8', 'latin-1')):
    """Tries to safely decode strings retrieved using SNMP.

    SNMP does not really define encodings, and will not normally allow
    non-ASCII strings to be written  (though binary data is fine). Sometimes,
    administrators have been able to enter descriptions containing non-ASCII
    characters using CLI's or web interfaces. The encoding of these are
    undefined and unknown. To ensure they can be safely stored in the
    database (which only accepts UTF-8), we make various attempts at decoding
    strings to unicode objects before the database becomes involved.
    """
    if string is None:
        return

    if isinstance(string, six.text_type):
        return string
    if isinstance(string, six.binary_type):
        for encoding in encodings_to_try:
            try:
                return string.decode(encoding)
            except UnicodeDecodeError:
                pass

    return repr(string)  # fallback
