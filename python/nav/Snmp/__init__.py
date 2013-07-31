#
# Copyright (C) 2010, 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A high level interface for synchronouse SNMP operations in NAV.

This interface supports both pynetsnmp, PySNMP v2 and PySNMP SE.

"""
from __future__ import absolute_import

# Debian enables multi-version installs of pysnmp.  On Debian, setting this
# environment variable to v3 will select PySNMP-SE, which is the highest
# version supported by NAV.
import os
os.environ['PYSNMP_API_VERSION'] = 'v3'

BACKEND = None

try:
    # our highest preference is pynetsnmp, since it can support IPv6
    import pynetsnmp
except ImportError:
    try:
        import pysnmp
    except ImportError:
        os.environ['PYSNMP_API_VERSION'] = 'v2'
        try:
            import pysnmp
        except:
            pass

    # Identify which PySNMP version is actually installed.  Looks ugly, but each
    # version provides (or forgets to provide) a different API for reporting its
    # version.
    try:
        from pysnmp import version
        try:
            version.verifyVersionRequirement(3, 4, 3)
            BACKEND = 'se'
        except Exception, e:
            # Accept any exception, it will be from the verifyVersionRequirement
            # function (pysnmp.error.PySnmpVersionError)
            # For easier unit testing we accept any exception for this code line
            #
            raise ImportError(e)
    except ImportError:
        try:
            if hasattr(pysnmp, 'majorVersionId'):
                # pylint: disable=E1101
                raise ImportError('Unsupported PySNMP version %s' %
                                  pysnmp.majorVersionId)
            else:
                BACKEND = 'v2'
        except NameError:
            # pysnmp never got loaded, hasattr fails...
            # we still got no SNMP backend.
            # so continune "searching" for a BACKEND
            pass
else:
    BACKEND = 'pynetsnmp'

# These wildcard imports are informed, not just accidents.
# pylint: disable=W0401
if BACKEND == 'v2':
    from .pysnmp_v2 import *
elif BACKEND == 'se':
    from .pysnmp_se import *
elif BACKEND == 'pynetsnmp':
    from .pynetsnmp import *
else:
    raise ImportError("No supported SNMP backend was found")
