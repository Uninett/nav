#!/usr/bin/env python3
#
# Copyright (C) 2007, 2012, 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"Script to simulate snmpAgentState events from ipdevpoll"

import sys
from nav import db
from nav.event import Event

connection = db.getConnection('default')
database = connection.cursor()


def handler(nblist, state):
    for netboxid in nblist:
        e = Event(
            'ipdevpoll',
            'eventEngine',
            netboxid=netboxid,
            eventtypeid='snmpAgentState',
            state=state,
            severity=1,
        )
        e['alerttype'] = 'snmpAgentDown' if state == 's' else 'snmpAgentUp'
        e.post()


if len(sys.argv) <= 2:
    print("Not enough arguments (%d), <match spec> <up|down>" % len(sys.argv))
    sys.exit(0)

nb = []
nbdup = set()
sysnames = []

for ii in range(1, len(sys.argv) - 1):
    sql = (
        "SELECT netboxid,sysname,typeid FROM netbox JOIN room USING(roomid) "
        "WHERE ip IS NOT NULL"
    )
    qn = sys.argv[ii]
    if (
        qn.startswith("_")
        or qn.startswith("-")
        or qn.startswith("%")
        or qn.find(",") >= 0
    ):
        if qn.startswith("-"):
            qn = qn[1 : len(qn)]
            sql += " AND typeid IN ("
        elif qn.startswith("_"):
            qn = qn[1 : len(qn)]
            sql += " AND catid IN ("
        elif qn.startswith("%"):
            qn = qn[1 : len(qn)]
            sql += " AND roomid IN ("
        else:
            sql += " AND sysname IN ("
        ids = qn.split(",")
        for i in range(0, len(ids)):
            sql += "'" + ids[i] + "',"
        if len(ids) > 0:
            sql = sql[0 : len(sql) - 1]
        sql += ")"
    else:
        sql += " AND sysname LIKE '" + qn + "'"

    database.execute(sql)
    for netboxid, sysname, typeid in database.fetchall():
        if netboxid not in nbdup:
            nb.append(netboxid)
            sysnames.append(sysname)
        nbdup.add(netboxid)

if sys.argv[len(sys.argv) - 1].startswith("u"):
    state = "e"
elif sys.argv[len(sys.argv) - 1].startswith("d"):
    state = "s"
else:
    print("Unknown state: " + sys.argv[len(sys.argv) - 1])
    sys.exit(0)


if state == "e":
    updown = "up"
else:
    updown = "down"
print("SNMP agents going %s on: %r" % (updown, sysnames))
handler(nb, state)
connection.commit()
