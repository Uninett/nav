#!/usr/bin/env python
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
# Authors: John Magne Bredal <bredal@itea.ntnu.no>
#
"""
This python script sets the initial thresholds on some of 
the rrd-datasources. This is only meant to be done at install
of NAV-v3, but may be done several times if there is a reason
for that. The script will not overwrite any set thresholds.
"""

import forgetSQL
import re
import nav.db.forgotten
import nav.path
from nav.db import getConnection

conn = getConnection('default')
c = conn.cursor()

def setData (threshold, max, datasourceid):
    datasource.threshold = threshold
    datasource.max = max
    datasource.delimiter = ">"
    datasource.thresholdstate = "inactive"

    sql = """
    UPDATE rrd_datasource SET 
    threshold = %s, max = %s, delimiter = %s thresholdstate = %s 
    WHERE rrd_datasourceid = %s
    """

    c.execute(sql, (threshold, max, ">", "inactive", datasourceid))
    conn.commit()

def openFile (file):
    try:
        return open(file)
    except IOError:
        return None

# setting default threshold
default = "90"

# read configfile to check for other value
confdir = nav.path.sysconfdir
file = confdir + "/fillthresholds.cfg"
handle = openFile (file)
if handle:
    for line in handle.readlines():
        if line.startswith("threshold"):
            default = line.split("=").pop().strip()
            print "Setting default value to %s" % default
            break

    handle.close()
    
query = """
  SELECT rrd_datasourceid, key, value, descr, units FROM rrd_file
  JOIN rrd_datasource USING (rrd_fileid)
  WHERE threshold IS NULL
"""

c.execute(query)

for datasourceid, key, value, descr, units in c.fetchall():
    if units == '%' or units == '-%':
        print "Found percent %s: %s, setting threshold=%s, max=100" \
            %(descr, units, default)
        setData(default, "100", datasourceid)
    elif re.compile("octets",re.I).search(descr):
        # Finds the speed of the interface
        if key != 'interface':
            continue

        interfaceid = value

        port = "SELECT speed FROM interface WHERE interfaceid = %s"
        c.execute(port, (interfaceid,))

        speed = c.fetchone()[0]
        if speed:
            speed = int(speed * 2 ** 20)
        
        print "Found octets: %s, setting threshold to %s, max=%s" \
            %(datasource.descr, default+"%", speed);
        setData(default+"%", speed, datasourceid)
