#!/usr/bin/python
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2007, 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"Script to simulate link up/down events from snmptrapd / ipdevpoll"

import sys
from nav import db

def handler(cursor, boxlist, state):

    for (deviceid, netboxid, subid) in boxlist:
        sql = """INSERT INTO eventq
                   (source, target, deviceid, netboxid, subid, eventtypeid,
                    state,severity)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(sql, ('snmptrapd', 'eventEngine', deviceid,
                             netboxid, subid, 'linkState', state, 100))


def main():
    if (len(sys.argv) <= 2):
        print "Not enough arguments (%d), <match spec> <up|down>" % (
            len(sys.argv),)
        sys.exit(0)

    connection = db.getConnection('getDeviceData','manage')
    cursor = connection.cursor()

    netboxes = []
    device_dupes = set()
    sysnames = []

    for spec in sys.argv[1:-1]:
        sql = """SELECT deviceid, interfaceid, ifname, netboxid, sysname
                 FROM netbox
                 JOIN interface USING (netboxid)
                 WHERE ip IS NOT NULL
                    AND sysname ILIKE %s AND ifname ILIKE %s"""

        box, module = spec.split(":")
        cursor.execute(sql, (box, module))
        for (deviceid, interfaceid, ifname, netboxid, sysname
             ) in cursor.fetchall():
            if interfaceid not in device_dupes:
                netboxes.append((deviceid, netboxid, interfaceid))
                sysnames.append((sysname, ifname))
            device_dupes.add(interfaceid)

    if sys.argv[-1].startswith("u"):
        state = "e"
    elif sys.argv[-1].startswith("d"):
        state = "s"
    else:
        print "Unknown state: " + sys.argv[-1]
        sys.exit(0)


    updown = "up" if (state=="e") else "down"
    print "Links going %s: %r" % (updown, sysnames)
    handler(cursor, netboxes, state)
    connection.commit()

if __name__ == '__main__':
    main()
