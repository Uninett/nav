# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2006 UNINETT AS
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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#
"""
Function to get the current status from the
alerhist table. Used by the frontpage.
"""

import nav.db

def boxesDown(sort = False):
    connection = nav.db.getConnection('status', 'manage')
    database = connection.cursor()

    # If components is on maintenance, do not show them
    sql = """SELECT n.sysname, n.ip, ah.start_time,
            now() - ah.start_time AS downtime, n.up
        FROM alerthist AS ah, netbox AS n, alerttype AS at
        WHERE ah.netboxid = n.netboxid
            AND ah.alerttypeid = at.alerttypeid
            AND ah.end_time = 'infinity'
            AND ah.eventtypeid = 'maintenanceState'"""
    database.execute(sql)
    result_maint = database.fetchall()

    # Create list of components on maintenance
    onmaint = {}
    for line in result_maint:
        onmaint[line[1]] = True

    # Get components
    sql = """SELECT n.sysname, n.ip, ah.start_time, now() - ah.start_time
            AS downtime, n.up
        FROM alerthist AS ah, netbox AS n, alerttype AS at
        WHERE ah.netboxid = n.netboxid
            AND at.alerttypeid = ah.alerttypeid
            AND ah.end_time = 'infinity'
            AND ah.eventtypeid = 'boxState'
            AND (n.up = 'n' OR n.up = 's')
        ORDER BY now() - ah.start_time"""
    database.execute(sql)
    result = database.fetchall()

    downList = []
    for line in result:
        # If on maintenance, skip this component
        if line[1] in onmaint:
            continue

        shadow = False
        if line[4] == 's':
            shadow = True
        downList.append([line[3],
                         line[0],
                         line[1],
                         line[2],
                         shadow])
    if sort:
        downList.sort()
    return downList 

def boxesDownSortByNewest():
    return boxesDown(sort=True)
