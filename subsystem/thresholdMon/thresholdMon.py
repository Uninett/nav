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
This is a python script that walks through the rrd-files in
the nav-database and reports if the threshold is surpassed.
"""

import time

start = int(time.time())
date = time.ctime()

import getopt,sys
import nav.event
from nav.db import getConnection
conn = getConnection('default')

import re

from nav.rrd import presenter
pres = presenter.presentation()

# Globals
exceptions = ['cpu5min','c5000BandwidthMax']
ll = 2
downmodifier = 20

# Print usage when -h option called
def usage(name):
    print "USAGE: %s [-h] [-l loglevel]" % name
    print "-h\t\tthis helptext"
    print "-l loglevel\tset the loglevel (1-silent,2-normal,3-debug)"

# A simple method to set state in the rrd_datasource table
def setState(dsid, descr, state):
    if ll >= 2: print "Setting %s to %s" %(descr, state)

    c = conn.cursor()
    sql = """
    UPDATE rrd_datasource SET thresholdstate = %s WHERE rrd_datasourceid = %s
    """
    c.execute(sql, (state, dsid))
    conn.commit()
    

# Makes the event ready for sending and updates the rrd_datasource
# table with the correct information
# calls sendEvent with correct values
def makeEvent (presobject, var, val, subid, fileid, state):
    # Fetching some data about the rrd
    c = conn.cursor()
    sql = """
    SELECT netboxid, sysname, ip FROM rrd_file 
    LEFT JOIN netbox USING (netboxid)
    WHERE rrd_fileid = %s
    """
    c.execute(sql, (fileid, ))
    
    netboxid, sysname, ip = c.fetchone()

    if netboxid:
        if ll >= 2: print "thresholdalert regarding %s (%s)" %(sysname, ip)
    if state == 'active':
        if ll >= 2: print "Threshold on %s surpassed." %var
        setState(subid, var, state)
        sendEvent(var, val, netboxid, state, subid);
    elif state == 'inactive':
        if ll >= 2: print "%s has calmed down." %var
        setState(subid, var, state)
        sendEvent(var, val, netboxid, state, subid);
    elif state == 'stillactive':
        if ll >= 2: print "Alert on %s is still active." %var
    else:
        if ll >= 2: print "No such state (%s)" % state


# Updates the correct tables for sending the event
def sendEvent (var, val, netboxid, state, subid):
    if state == 'active':
        state = 's'
    else:
        state = 'e'

    if ll >= 2: print "sending event"

    e = nav.event.Event(source='thresholdMon', target='eventEngine', 
                        netboxid=netboxid, subid=subid, 
                        eventtypeid='thresholdState', state=state)
    e[var] = val

    try:
        e.post()
    except Exception, e:
        print e


##################################################
# Done with functions, let the games begin!
##################################################

# First we get options from the commandline
try:
    opt,args = getopt.getopt(sys.argv[1:], "hl:")
except getopt.GetoptError:
    print "GetoptError %s" % str(getopt.GetoptError)

if ll >= 2: print "Starting thresholdMon at %s" % date
for option, argument in opt:
    if option == '-h':
        # If -h option set, print usage, exit
        usage(sys.argv[0])
        sys.exit()
    elif option == '-l':
        # If -l option set, use the argument as loglevel if it is in range 1:4
        argument = int(argument)
        if argument in range(1,4):
            ll = argument
        else:
            if ll >= 2: print "No such loglevel: %s, using loglevel 1" % argument
            ll = 1

# For each rrd_datasource, fetch the value and compare
# it to the max-value.
c = conn.cursor()
sql = """
SELECT rrd_fileid, rrd_datasourceid, descr, threshold, max, delimiter, 
thresholdstate
FROM rrd_datasource 
WHERE threshold IS NOT NULL
"""
c.execute(sql)

for (rrd_fileid, rrd_datasourceid, descr, threshold, max, delimiter, 
     thresholdstate) in c.fetchall():
    if ll >= 3: print "-- NEW DATASOURCE (%s) --" % rrd_datasourceid
    surpassed = 0

    # These values are silly. They just show how much the maximum value
    # ever in the life of the unit has been, which is totally useless to
    # the thresholdMonitor
    if exceptions.count(descr):
        if ll >= 3: print "%s is in exceptions" % descr
        continue

    max = int(max)

    if ll >= 3: print "Adding datasource %s" % rrd_datasourceid
    # Getting the value from the database
    pres.removeAllDs()
    try:
        pres.addDs(rrd_datasourceid)
    except TypeError:
        if ll >= 3: 
            print "Error could not add ds, continuing (%s,%s,%s)" \
                %(rrd_datasourceid)
        continue

    # We look at values over the 15 last minutes. 
    pres.fromTime = '-15min'

    if ll >= 3: print "Getting data from %s (%s)" % (rrd_datasourceid, descr)
    if pres.average():
        value = pres.average().pop()
        if ll >= 3: print "%s" % value
    else:
        if ll >= 3: print "No value returned"
        continue

    # Checking if it is percent or a normal value we are comparing
    m = re.compile("%$").search(threshold)
    threshold = int(re.sub("%$","",threshold))

    # To prevent oscillation in case the value is just below the threshold
    # we create a lower limit that has to be passed to really say that the
    # crisis os over.
    if thresholdstate == 'active':
        if delimiter == '>':
            threshold = threshold - downmodifier
        elif delimiter == '<':
            threshold = threshold + downmodifier
            
    if ll >= 3: print "Threshold is %s" % threshold

    if m:
        if delimiter == '>' and (value / max  * 100) > threshold:
            surpassed = 1
        elif delimiter == '<' and (value / max * 100) < threshold:
            surpassed = 1
    else:
        if delimiter == '<' and value < threshold:
            surpassed = 1
        elif delimiter == '>' and value > threshold:
            surpassed = 1
        

    if surpassed and thresholdstate == 'inactive':
        if ll >= 2: print "--------------------"
        if ll >= 2: print "Threshold surpassed (%s,%s,%s ds:%s)" \
                %(value, threshold, max, rrd_datasourceid)
        # must send danger-event
        makeEvent(pres, descr, threshold, rrd_datasourceid, rrd_fileid, 
                  'active')
    elif surpassed and thresholdstate == 'active':
        if ll >= 2: print "--------------------"
        if ll >= 2: print "Threshold still surpassed. (%s,%s,%s ds:%s)" \
                %(value, threshold, max, rrd_datasourceid)
	makeEvent(pres, descr, threshold, rrd_datasourceid, rrd_fileid,
                  'stillactive')
    elif datasource.thresholdstate == 'active':
        if ll >= 2: print "--------------------"
        if ll >= 2: print "Threshold below value (%s,%s,%s ds:%s)" \
                %(value, threshold, max, rrd_datasourceid)
        # Must send nodanger-event
        makeEvent(pres, descr, threshold, rrd_datasourceid, rrd_fileid, 
                  'inactive')
    else:
        if ll >= 3: print "Threshold not surpassed (%s,%s,%s)" \
                %(value, threshold, max)

end = int(time.time())
if ll >= 2: print "%s executed in %s seconds." %(sys.argv[0],end-start)
if ll >= 2: print "------------------------------------------------------------------\n\n"
