#!/usr/bin/env python
#
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
import psycopg, os, sys

#
# This script will connect to a live manage database and dump the
# contents of the snmpoid table in a format suitable for re-insertion
# at the same or a different site.
#
# Make sure the environment variable PGASSWORD is set before running
# the script.  Should be rewritten to ask for a password if none is
# known.
#

dbname = "manage"
dbuser = os.getenv('PGUSER')
if not dbuser:
    dbuser = "postgres"
dbpasswd = os.getenv('PGPASSWORD')

connection = psycopg.connect('host=localhost dbname=%s user=%s password=%s' %
                             (dbname, dbuser, dbpasswd))
cursor = connection.cursor()
cursor.execute("SELECT oidkey, snmpoid, descr, oidsource, getnext, " +
               "match_regex, decodehex, oidname, mib FROM snmpoid " +
               "ORDER BY oidkey")

print "BEGIN;"
for row in cursor.fetchall():
    newrow = []
    for col in row:
        if col is None:
            newrow.append('NULL')
        else:
            newrow.append("'%s'" % str(col))
    print "DELETE FROM snmpoid WHERE oidkey=%s;" % newrow[0]
    print "INSERT INTO snmpoid (oidkey, snmpoid, descr, oidsource, getnext,",
    print "match_regex, decodehex, oidname, mib)"
    print "VALUES (%s);" % ",".join(newrow)
    print
    
print "COMMIT;"
