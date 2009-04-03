#!/usr/bin/env python
# -*- coding: ISO8859-1 -*-
# Copyright 2004 Norwegian University of Science and Technology
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
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#
""" This script will connect to a live manage database and dump the
contents of the snmpoid table in a format suitable for re-insertion at
the same or a different site.

Make sure the environment variable PGASSWORD is set before running
the script.  Should be rewritten to ask for a password if none is
known."""

import sys
import os
import psycopg2
import time

def main(args):
    dbname = "manage"
    dbhost = os.getenv('PGHOST') or 'localhost'
    dbport = os.getenv('PGPORT') or '5432'
    dbuser = os.getenv('PGUSER') or 'postgres'
    dbpasswd = os.getenv('PGPASSWORD')

    connection = psycopg2.connect(
        'host=%s port=%s dbname=%s user=%s password=%s' %
        (dbhost, dbport, dbname, dbuser, dbpasswd))
    cursor = connection.cursor()
    cursor.execute("SELECT oidkey, snmpoid, descr, oidsource, getnext, " +
                   "match_regex, decodehex, oidname, mib FROM snmpoid " +
                   "ORDER BY oidkey")

    timeString = time.strftime("%Y-%m-%d %H:%M:%S GMT", time.gmtime())
    print '--\n-- Automated dump by dumpsnmpoid.py initiated at ' + \
          timeString + '\n--'

    print "BEGIN;"
    for row in cursor.fetchall():
        newrow = []
        for col in row:
            if col is None:
                newrow.append('NULL')
            else:
                newrow.append(str(psycopg2.QuotedString(str(col))))
        print "DELETE FROM snmpoid WHERE oidkey=%s;" % newrow[0]
        print "INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource,",
        print "getnext, match_regex, decodehex, oidname, mib)"
        print "VALUES (%s);" % ",".join(newrow)
        print

    # We insert statements that will force getDeviceData to re-test all
    # the boxes, as we've made changed to the list of known snmpoids.
    print
    print "UPDATE snmpoid SET getnext=true, uptodate=true;"
    print "UPDATE netbox SET uptodate=false;"
    print
    print "COMMIT;"
    print '--\n-- Automatic dump ends here\n--'

##############
# begin here #
##############
if __name__ == '__main__':
    main(sys.argv[1:])
