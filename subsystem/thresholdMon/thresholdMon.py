#!/usr/bin/env python
# -*- coding: ISO8859-1 -*-
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
import nav.db.forgotten
from nav import db
conn = db.getConnection('thresholdmon','manage')

from nav.db import manage

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
def setState(datasource,state):
    if ll >= 2: print "Setting %s to %s" %(datasource.descr,state)
    datasource.thresholdstate = state
    datasource.save()
    

# Makes the event ready for sending and updates the rrd_datasource
# table with the correct information
# calls sendEvent with correct values
def makeEvent (presobject,datasource,state):

    # Fetching some data about the rrd
    rrdfile = datasource.rrd_file

    var = datasource.descr
    val = datasource.threshold
    subid = datasource.rrd_datasourceid

    if rrdfile.netbox is not None:
        netbox = rrdfile.netbox
        if ll >= 2: print "thresholdalert regarding %s (%s)" %(netbox.sysname,netbox.ip)
    
    if state == 'active':
        if ll >= 2: print "Threshold on %s surpassed." %datasource.descr
        setState(datasource,state)
        sendEvent(var,val,netbox,state,subid);
    elif state == 'inactive':
        if ll >= 2: print "%s has calmed down." % datasource.descr
        setState(datasource,state)
        sendEvent(var,val,netbox,state,subid);
    elif state == 'stillactive':
        if ll >= 2: print "Alert on %s is still active." % datasource.descr
    else:
        if ll >= 2: print "No such state (%s)" % state

# Updates the correct tables for sending the event
def sendEvent (var, val, netbox, state, subid):

    if state == 'active':
        state = 's'
    else:
        state = 'e'

    if ll >= 2: print "sending event"

    eventq = manage.Eventq()
    eventq.source = 'thresholdMon'
    eventq.target = 'eventEngine'
    eventq.netbox = netbox.netboxid
    eventq.eventtype = 'thresholdState'
    eventq.state = state
    eventq.time = "NOW()"
    eventq.value = 100
    eventq.severity = 100
    eventq.subid = subid
    
    eventq.save()

    if ll >= 2: print "Eventq object saved"

    # Have some trouble getting forgetSQL to find correct key here, so using normal psql-query
    cur = conn.cursor()

    query = "INSERT INTO eventqvar (eventqid, var, val) VALUES (%s, '%s', '%s')" %(eventq.eventqid, var, val)
    cur.execute(query)
    conn.commit();

    if ll >= 2: print "Eventvar object saved"
    

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

for datasource in manage.Rrd_datasource.getAllIterator(where="threshold IS NOT NULL"):
    if ll >= 3: print "-- NEW DATASOURCE (%s) --" % datasource.rrd_datasourceid
    surpassed = 0

    # These values are silly. They just show how much the maximum value
    # ever in the life of the unit has been, which is totally useless to
    # the thresholdMonitor
    if exceptions.count(datasource.descr):
        if ll >= 3: print "%s is in exceptions" % datasource.descr
        continue

    threshold = datasource.threshold
    max = int(datasource.max)
    delimiter = datasource.delimiter

    if ll >= 3: print "Adding datasource %s" % datasource.rrd_datasourceid
    # Getting the value from the database
    pres.removeAllDs()
    try:
        pres.addDs(datasource.rrd_datasourceid)
    except TypeError:
        temprrd = datasource.rrd_file
        if ll >= 3: print "Error could not add ds, continuing (%s,%s,%s)" % (datasource.rrd_datasourceid,temprrd.path,temprrd.filename)
        continue

    # We look at values over the 15 last minutes. 
    pres.fromTime = '-15min'

    if ll >= 3: print "Getting data from %s (%s)" % (datasource.rrd_datasourceid,datasource.descr)
    if pres.average():
        value = pres.average().pop()
        if ll >= 3: print "%s" % value
    else:
        if ll >= 3: print "No value returned, are we collecting data to this rrd-file???"
        continue


    # Checking if it is percent or a normal value we are comparing
    m = re.compile("%$").search(threshold)
    threshold = int(re.sub("%$","",threshold))

    # To prevent oscillation in case the value is just below the threshold
    # we create a lower limit that has to be passed to really say that the
    # crisis os over.
    if datasource.thresholdstate == 'active':
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
        

    if surpassed and datasource.thresholdstate == 'inactive':
        if ll >= 2: print "--------------------"
        if ll >= 2: print "CRISIS!!! Threshold surpassed, duck and cover! (%s,%s,%s ds:%s)" %(value,threshold,max,datasource.rrd_datasourceid)
        # must send danger-event
        makeEvent(pres,datasource,'active')
    elif surpassed and datasource.thresholdstate == 'active':
        if ll >= 2: print "--------------------"
        if ll >= 2: print "CRISIS still going strong. (%s,%s,%s ds:%s)" %(value,threshold,max,datasource.rrd_datasourceid)
	makeEvent(pres,datasource,'stillactive')
    elif datasource.thresholdstate == 'active':
        if ll >= 2: print "--------------------"
        if ll >= 2: print "PUH, CRISIS over! (%s,%s,%s ds:%s)" %(value,threshold,max,datasource.rrd_datasourceid)
        # Must send nodanger-event
        makeEvent(pres,datasource,'inactive')
    else:
        if ll >= 3: print "No crisis going on. (%s,%s,%s)" %(value,threshold,max)

end = int(time.time())
if ll >= 2: print "%s executed in %s seconds." %(sys.argv[0],end-start)
if ll >= 2: print "------------------------------------------------------------------\n\n"
