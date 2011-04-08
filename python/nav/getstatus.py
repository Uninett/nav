# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2006 UNINETT AS
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
