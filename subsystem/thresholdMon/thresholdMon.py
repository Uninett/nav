#!/usr/bin/env python
##################################################
# thresholdmon.py
#
# Author: John Magne Bredal, ITEA / NTNU © 2003
##################################################

import time

start = int(time.time())

import getopt,sys
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

# Globals
exceptions = ['cpu5min','c5000BandwidthMax']
ll = 1

def usage(name):
    print "USAGE: %s [-h] [-l loglevel]" % name
    print "-h\t\tthis helptext"
    print "-l loglevel\tset the loglevel (1-silent,2-normal,3-debug)"

def setState(datasource,state):
    if ll >= 2: print "Setting %s to %s" %(datasource.descr,state)
    datasource.thresholdstate = state
    datasource.save()
    

# Makes the event ready for sending and updates the rrd_datasource
# table with the correct information
def makeEvent (presobject,datasource,state):

    # Fetching some data about the rrd
    rrdfile = datasource.rrd_file
    
    if rrdfile.netbox is not None:
        netbox = rrdfile.netbox
        if ll >= 2: print "thresholdalert regarding %s (%s)" %(netbox.sysname,netbox.ip)
    
    if state == 'active':
        if ll >= 2: print "Threshold on %s surpassed." %datasource.descr
        setState(datasource,state)
    elif state == 'inactive':
        if ll >= 2: print "%s has calmed down." % datasource.descr
        setState(datasource,state)
    elif state == 'stillactive':
        if ll >= 2: print "Alert on %s is still active." % datasource.descr
    else:
        if ll >= 2: print "No such state (%s)" % state

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

# First we get options from the commandline
try:
    opt,args = getopt.getopt(sys.argv[1:], "hl:")
except getopt.GetoptError:
    print "GetoptError %s" % str(getopt.GetoptError)

for option, argument in opt:
    if option == '-h':
        usage(sys.argv[0])
        sys.exit()
    elif option == '-l':
        argument = int(argument)
        if argument in range(1,4):
            ll = argument
        else:
            if ll >= 2: print "No such loglevel: %s, using loglevel 1" % argument
            ll = 1

# For each rrd_datasource, fetch the value and compare
# it to the max-value.

for datasource in manage.Rrd_datasource.getAllIterator(where="threshold IS NOT NULL"):
    if ll >= 3: print "-- NEW DATASOURCE --"
    surpassed = 0

    # These values are silly. They just show how much the maximum value
    # ever in the life of the unit has been, which is totally useless to
    # the thresholdMonitor
    if exceptions.count(datasource.descr):
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
    
    pres.fromTime = '-15min'

    if ll >= 3: print "Getting data from %s (%s)" % (datasource.rrd_datasourceid,datasource.descr)
    if pres.average():
        value = pres.average().pop()
        if ll >= 3: print "%s" % value
    else:
        continue

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
