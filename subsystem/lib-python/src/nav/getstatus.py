"""
$Id$

This file id part of the NAV project.

Function to get the current status from the
alerhist table. Used by the frontpage (and
eventually by the status page).

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
"""

import mx.DateTime,nav.db.manage

def boxesDown():
    downList = []
    t = nav.db.manage.AlerthistNetbox()

    w = "eventtypeid = 'boxState' and end_time = 'infinity'"
    for alert in t.getAllIterator(where=w):
        shadow = False
        if alert.netbox.up == 's':
            shadow = True
        downList.append([alert.netbox.sysname,
                         alert.netbox.ip,
                         alert.start_time,
                         mx.DateTime.now() - alert.start_time,
                         shadow])
        
    return downList 

def boxesDownSortByNewest():
    downList = []
    t = nav.db.manage.AlerthistNetbox()

    w = "eventtypeid = 'boxState' and end_time = 'infinity'"
    for alert in t.getAllIterator(where=w):
        shadow = False
        if alert.netbox.up == 's':
            shadow = True
        downList.append([mx.DateTime.now() - alert.start_time,
                         alert.netbox.sysname,
                         alert.netbox.ip,
                         alert.start_time,
                         shadow])
    downList.sort()    
    return downList 
