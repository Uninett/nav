"""
$Id$

This file id part of the NAV project.

Function to get the current status from the
alerhist table. Used by the frontpage.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
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
