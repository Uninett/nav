#!/usr/bin/python
# -*- coding: ISO8859-1 -*-
#
# $Id$
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
#
# Authors: Kristian Eide <kreide@online.no>
#
# Script to simulate up/down events from pping
#
import os
import nav
import sys
from nav import db
import re

connection = db.getConnection('pping','manage')
database = connection.cursor()

def handler(nblist, state):

    for nb in nblist:
        deviceid = nb[0]
        netboxid = nb[1]
        msql = "INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',"+`deviceid`+","+`netboxid`+",'boxState','"+state+"',100)"

        database.execute(msql)


if (len(sys.argv) <= 2):
    print "Not enough arguments ("+`len(sys.argv)`+"), <match spec> <up|down>"
    sys.exit(0)

nb = []
nbdup = {}
sysname = []

for ii in range(1, len(sys.argv)-1):
    sql = "SELECT deviceid,netboxid,sysname,typeid FROM netbox JOIN room USING(roomid) WHERE ip IS NOT NULL";
    qn = sys.argv[ii]
    if (qn.startswith("_") or qn.startswith("-") or qn.startswith("%") or qn.find(",") >= 0):
        if (qn.startswith("-")):
            qn = qn[1:len(qn)]
            sql += " AND typeid IN ("
        elif (qn.startswith("_")):
            qn = qn[1:len(qn)]
            sql += " AND catid IN ("
        elif (qn.startswith("%")):
            qn = qn[1:len(qn)]
            sql += " AND roomid IN ("
        else:
            sql += " AND sysname IN ("
        ids = qn.split(",")
        for i in range(0, len(ids)):
            sql += "'" + ids[i] + "',"
        if len(ids) > 0: sql = sql[0:len(sql)-1]
        sql += ")"
    else:
        sql += " AND sysname LIKE '"+qn+"'"

    database.execute(sql)
    for r in database.fetchall():
        if not nbdup.has_key(r[0]):
            nb.append([r[0], r[1]])
            sysname.append(r[2])
        nbdup[r[0]] = 0

if sys.argv[len(sys.argv)-1].startswith("u"): state = "e"
elif sys.argv[len(sys.argv)-1].startswith("d"): state = "s"
else:
    print "Unknown state: " + sys.argv[len(sys.argv)-1]
    sys.exit(0)


if (state=="e"): updown = "up"
else: updown="down"
print "Devices going " + updown + ": " + `sysname`
handler(nb, state)
connection.commit()

