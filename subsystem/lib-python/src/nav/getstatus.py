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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#
"""
Function to get the current status from the
alerhist table. Used by the frontpage.
"""

import nav.db

def boxesDown():
    downList = []
    sql = "SELECT netbox.sysname,netbox.ip,alerthist.start_time," +\
          "now()-start_time,netbox.up FROM alerthist,netbox,alerttype " + \
          "WHERE alerthist.eventtypeid='boxState' AND end_time='infinity' " +\
          "AND alerttype.alerttypeid=alerthist.alerttypeid AND " +\
          "alerthist.netboxid=netbox.netboxid AND " +\
          "(alerttype.alerttype='boxDown' or " +\
          "alerttype.alerttype='boxShadow') AND " +\
          "(netbox.up='n' OR netbox.up='s') " +\
          "ORDER BY now()-alerthist.start_time;"

    connection = nav.db.getConnection('status', 'manage')
    database = connection.cursor()
    database.execute(sql)
    result = database.fetchall()

    for alert in result:
        shadow = False
        if alert[4] == 's':
            shadow = True
        downList.append([alert[0],
                         alert[1],
                         alert[2],
                         alert[3],
                         shadow])
    return downList 

def boxesDownSortByNewest():
    downList = []
    sql = "SELECT netbox.sysname,netbox.ip,alerthist.start_time," +\
          "now()-start_time,netbox.up FROM alerthist,netbox,alerttype " + \
          "WHERE alerthist.eventtypeid='boxState' AND end_time='infinity' " +\
          "AND alerttype.alerttypeid=alerthist.alerttypeid AND " +\
          "alerthist.netboxid=netbox.netboxid AND " +\
          "(alerttype.alerttype='boxDown' or " +\
          "alerttype.alerttype='boxShadow') AND " +\
          "(netbox.up='n' OR netbox.up='s') " +\
          "ORDER BY now()-alerthist.start_time;"

    connection = nav.db.getConnection('status', 'manage')
    database = connection.cursor()
    database.execute(sql)
    result = database.fetchall()

    for alert in result:
        shadow = False
        if alert[4] == 's':
            shadow = True
        downList.append([alert[3],
                         alert[0],
                         alert[1],
                         alert[2],
                         shadow])
    downList.sort()
    return downList 
