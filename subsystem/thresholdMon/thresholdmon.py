#!/usr/bin/env python
##################################################
# thresholdmon.py
#
# Author: John Magne Bredal, ITEA / NTNU © 2003
##################################################

import psycopg
import nav.db.forgotten
from nav import db
conn = db.getConnection('thresholdmon','manage')

from nav.db import manage

nav.db.forgotten.manage._Wrapper.cursor = conn.cursor
nav.db.forgotten.manage._Wrapper._dbModule = psycopg

import re
import rrdpresenter
pres = rrdpresenter.presentation()

def setState(datasource,state):
    print "Setting %s to %s" %(datasource.descr,state)
    datasource.thresholdstate = state
    datasource.save()
    

# Makes the event ready for sending and updates the rrd_datasource
# table with the correct information
def makeEvent (presobject,datasource,state):

    # Fetching some data about the rrd
    rrdfile = datasource.rrd_file
    
    if rrdfile.netbox is not None:
        netbox = rrdfile.netbox
        print "thresholdalert regarding %s (%s)" %(netbox.sysname,netbox.ip)
    
    if state == 'active':
        print "Threshold on %s surpassed." %(datasource.descr)
        setState(datasource,state)
    else:
        print "%s has calmed down." % datasource.descr
        setState(datasource,state)

# Updates the correct tables for sending the event
def sendEvent (descr, netbox, state):

    if state == 'active':
        state = 's'
    else:
        state = 'e'

    eventq = Eventq()
    eventq.source = 'thresholdMon'
    eventq.target = 'eventEngine'
    eventq.netboxid = netbox.netboxid
    eventq.eventtypeid = 'thresholdState'
    eventq.state = state
    
    eventq.save()

    eventqvar = Eventqvar()
    eventqvar.eventqid = eventq.eventqid
    eventqvar.var = 'descr'
    eventqvar.val = descr

    eventqvar.save()

##################################################
# Done with functions, let the games begin!
##################################################

# Step-by-step howto

# 1. Select all the rows from the rrd_datasource-table
# with the threshold-field set.

datasources = manage.Rrd_datasource.getAll(where="threshold IS NOT NULL")

# 2. For each rrd_datasource, fetch the value and compare
# it to the max-value.

for datasource in datasources:
    print "-- NEW DATASOURCE --"
    surpassed = 0

    threshold = datasource.threshold
    max = int(datasource.max)
    delimiter = datasource.delimiter

    # Getting the value from the database
    pres.removeAllDs()
    pres.addDs(datasource.rrd_datasourceid)
    pres.fromTime = '-15min'

    value = pres.average().pop()

    # Checking if it is percent or a normal value we are comparing
    m = re.compile("%$").search(threshold)
    threshold = int(re.sub("%$","",threshold))
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
        print "CRISIS!!! Threshold surpassed, duck and cover! (%s,%s,%s)" %(value,threshold,max)
        # must send danger-event
        makeEvent(pres,datasource,'active')
    elif surpassed and datasource.thresholdstate == 'active':
        print "CRISIS still going strong. (%s,%s,%s)" %(value,threshold,max)
    elif datasource.thresholdstate == 'active':
        print "PUH, CRISIS over! (%s,%s,%s)" %(value,threshold,max)
        # Must send nodanger-event
        makeEvent(pres,datasource,'inactive')
    else:
        print "No crisis going on. (%s,%s,%s)" %(value,threshold,max)
