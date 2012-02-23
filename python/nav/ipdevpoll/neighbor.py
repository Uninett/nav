#
# Copyright (C) 2009-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utility functions for device neighbor identification.

Useful for ipdevpoll plugins who collect neighbor information from neigbor
discovery protocols and such (e.g. CDP, LLDP, switch forwarding tables).

"""
from datetime import timedelta
from nav.util import cachedfor

@cachedfor(timedelta(minutes=5))
def get_netbox_macs():
    "Returns a dict of (mac, netboxid) mappings of NAV-monitored devices"
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('SELECT mac, netboxid FROM netboxmac')
    netbox_macs = dict(cursor.fetchall())
    return netbox_macs

