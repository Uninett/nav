#!/usr/bin/python
# -*- coding: ISO8859-1 -*-
#
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2007 UNINETT AS
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
# Authors: Morten Brekkevold <morten.brekkevold@uninett.no>
#          Kristian Eide <kreide@online.no>
#
# Script to simulate up/down module events from moduleMon
#
import os
import nav
import sys
from nav import db
import re

connection = db.getConnection('getDeviceData','manage')
database = connection.cursor()

def handler(nblist, state):

    for nb in nblist:
        deviceid, netboxid, subid = nb

        msql = "INSERT INTO eventq (source,target,deviceid,netboxid,subid, " \
               "                    eventtypeid,state,severity) " \
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        database.execute(msql, ('moduleMon', 'eventEngine', deviceid,
                                netboxid, subid, 'moduleState', state, 100))


if (len(sys.argv) <= 2):
    print "Not enough arguments ("+`len(sys.argv)`+"), <match spec> <up|down>"
    sys.exit(0)

nb = []
nbdup = {}
sysname = []

for qn in sys.argv[1:-1]:
    sql = "SELECT module.deviceid,netboxid,moduleid,sysname,module FROM netbox JOIN module USING (netboxid) WHERE ip IS NOT NULL";
    box, module = qn.split(":")
    sql += " AND sysname ILIKE %s AND module=%s" % (db.escape(box), db.escape(module))
    
    database.execute(sql)
    for r in database.fetchall():
        if not nbdup.has_key(r[0]):
            nb.append(r[0:3])
            sysname.append(r[3:5])
        nbdup[r[0]] = 0

if sys.argv[-1].startswith("u"): state = "e"
elif sys.argv[-1].startswith("d"): state = "s"
else:
    print "Unknown state: " + sys.argv[-1]
    sys.exit(0)


if (state=="e"): updown = "up"
else: updown="down"
print "Modules going " + updown + ": " + `sysname`
handler(nb, state)
connection.commit()

