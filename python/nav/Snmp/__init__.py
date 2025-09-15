#
# Copyright (C) 2010, 2013 Uninett AS
# Copyright (C) 2022 Sikt
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

import os
import sys

BACKEND = None

try:
    # our highest preference is pynetsnmp, since it can support IPv6
    import pynetsnmp  # noqa: F401 - needed to set BACKEND
except ImportError:
    pass
else:
    BACKEND = 'pynetsnmp'

if BACKEND == 'pynetsnmp':
    if sys.platform == "darwin" and not os.getenv("DYLD_LIBRARY_PATH"):
        # horrible workaround for MacOS problems, described at length at
        # https://hynek.me/articles/macos-dyld-env/
        os.environ["DYLD_LIBRARY_PATH"] = os.getenv(
            "LD_LIBRARY_PATH", "/usr/local/opt/openssl/lib"
        )
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

    if isinstance(string, str):
        return string
    if isinstance(string, bytes):
        string = string.strip(b'\x00')
        for encoding in encodings_to_try:
            try:
                return string.decode(encoding)
            except UnicodeDecodeError:
                pass

    return repr(string)  # fallback
