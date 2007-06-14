# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import psycopg

from common import *

class netmapException(Exception):
    def __init__(self):
        self.reason = "Unknown"
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason



def getData(db_cursor = None):
    """Returns a dictionary containing the netboxes with their modules, ports and connections"""

    if not db_cursor:
        raise netmapException("No db-cursor given")

    netboxes = {}

    query = """
SELECT  DISTINCT ON(gwportid, swportid)
        gwportid, swportid,

        netboxid, sysname, netbox.prefixid, catid, netbox.up AS netbox_up,
        netbox.ip, netbox.roomid, (now() - upsince) AS netbox_uptime,

        module.moduleid, module.descr as module_descr,

        nettype, netident, netaddr,

        gwport.speed AS gwspeed, gwport.interface AS gwinterface, gwip,
        gwport.metric AS gwmetric, gwport.link AS gwlink,
        gwport.to_netboxid AS gw_to_netboxid, gwport.to_swportid AS gw_to_swportid,

        swport.speed AS swspeed, swport.interface AS swinterface,
        swport.link AS swlink, swport.port AS swport,
        swport.to_netboxid AS sw_to_netboxid, swport.to_swportid AS sw_to_swportid

FROM netbox
    LEFT OUTER JOIN prefix USING(prefixid)
    LEFT OUTER JOIN vlan USING(vlanid)
    LEFT OUTER JOIN module USING(netboxid)
    LEFT OUTER JOIN type USING(typeid)
    LEFT OUTER JOIN gwport USING(moduleid)
    LEFT OUTER JOIN gwportprefix USING(gwportid)
    LEFT OUTER JOIN swport USING(moduleid)
WHERE sysname != 'voldsminde.uninett.no'
ORDER BY gwportid, swportid, netboxid, swport.port;
    """

    db_cursor.execute(query)
    results = db_cursor.dictfetchall()

    for row in results:
        # Add a new netbox to the return if it doesnt exist
        if not netboxes.has_key(row['netboxid']):
            netboxes[row['netboxid']] = \
                Netbox(row['netboxid'], row['ip'], row['sysname'], row['catid'],
                       row['prefixid'], row['netbox_up'], row['netbox_uptime'],
                       row['roomid'])

        # Add a new module to the netbox if it doesnt exist
        if not netboxes[row['netboxid']].modules.has_key(row['moduleid']):
            netboxes[row['netboxid']].modules[row['moduleid']] = \
                Module(row['moduleid'], row['module_descr'])

        # Add swport to the module
        if not netboxes[row['netboxid']].modules[row['moduleid']].swports.has_key(row['swportid']):
            netboxes[row['netboxid']].modules[row['moduleid']].swports[row['swportid']] = \
                SWPort(row['swportid'], row['swport'], row['swlink'], row['swinterface'], row['swspeed'], row['sw_to_netboxid'], row['sw_to_swportid'])

        # Add gwport to the module
        if not netboxes[row['netboxid']].modules[row['moduleid']].gwports.has_key(row['gwportid']):
            netboxes[row['netboxid']].modules[row['moduleid']].gwports[row['gwportid']] = \
                GWPort(row['gwportid'], row['gwip'], row['gwlink'], row['gwinterface'], row['gwspeed'], row['gw_to_netboxid'], row['gw_to_swportid'])

    # Fetch netbox of the box the ports are connected to.
    for box in netboxes.values():
        for module in box.modules.values():
            for port in module.swports.values():
                if port.connected_swport:
                    db_cursor.execute("SELECT netboxid FROM swport JOIN module USING(moduleid) WHERE swportid = %i LIMIT 1" % port.connected_swport)
                    res = db_cursor.fetchall()
                    port.connected_to = res[0][0]
            for port in module.gwports.values():
                if port.connected_swport:
                    db_cursor.execute("SELECT netboxid FROM swport JOIN module USING(moduleid) WHERE swportid = %i LIMIT 1" % port.connected_swport)
                    res = db_cursor.fetchall()
                    port.connected_to = res[0][0]

    return netboxes
