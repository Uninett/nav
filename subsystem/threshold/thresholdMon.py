#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
# Copyright 2011 UNINETT AS
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
#
"""
This is a python script that walks through the rrd-files in
the nav-database and reports if the threshold is surpassed.
"""

import re
import time
import sys
import optparse

# import NAV libraries
import nav.config
import nav.logs
import nav.path
from nav.event import Event
from nav.db import getConnection
from nav.rrd import presenter
from nav.models.rrd import RrdFile, RrdDataSource

pres = presenter.presentation()

start = int(time.time())
date = time.ctime()

# Globals
exceptions = ['cpu5min','c5000BandwidthMax']
log_level = 2
downmodifier = 20

def log_it(level, msg):
    if log_level >= level:
        print >> sys.stdout, msg

# A simple method to set state in the rrd_datasource table
def setState(dsid, descr, state):
    log_it(2, "Setting %s to %s" %(descr, state))
    if isinstance(dsid, str) or isinstance(dsid, unicode):
        if dsid.isdigit():
            dsid = int(dsid)
        else:
            print >> sys.stderr, 'dsid is an illegal type: %s' % dsid
            return
    rrd_datasource = None
    try :
        rrd_datasource = RrdDataSource.objects.get(pk=dsid)
    except Exception, e:
        print >> sys.stderr, e
        return

    rrd_datasource.thresholdstate = state
    try :
        rrd_datasource.save()
    except Exception, e:
        print >> sys.stderr, e

# Makes the event ready for sending and updates the rrd_datasource
# table with the correct information
# calls sendEvent with correct values
def makeEvent (presobject, var, val, subid, fileid, state):
    if isinstance(fileid, str) or isinstance(fileid, unicode):
        if fileid.isdigit():
            fileid = int(fileid)
        else:
            print >> sys.stderr, 'fileid is an illegal type: %s' % fileid
            return
    rrd_file = None
    try :
        rrd_file = RrdFile.objects.filter(pk=fileid)
    except Exception, e:
        print >> sys.stderr, e
        return
  
    netboxid = rrd_file.nextbox.id
    sysname = rrd_file.nextbox.sysname
    ip = rrd_file.nextbox.ip

    if netboxid:
        log_it(2, "thresholdalert regarding %s (%s)" %(sysname, ip))
    if state == 'active':
        log_it(2, "Threshold on %s surpassed." %var)
        setState(subid, var, state)
        sendEvent(var, val, netboxid, state, subid);
    elif state == 'inactive':
        log_it(2, "%s has calmed down." %var)
        setState(subid, var, state)
        sendEvent(var, val, netboxid, state, subid);
    elif state == 'stillactive':
        log_it(2, "Alert on %s is still active." %var)
    else:
        log_it(2, "No such state (%s)" % state)


# Updates the correct tables for sending the event
def sendEvent (var, val, netboxid, state, subid):
    if state == 'active':
        state = 's'
    else:
        state = 'e'

    log_it(1, "sending event")

    e = Event(source='thresholdMon', target='eventEngine', 
                netboxid=netboxid, subid=subid, 
                eventtypeid='thresholdState', state=state)
    e[var] = val

    try:
        e.post()
    except Exception, e:
        print >> sys.stderr, e


##################################################
# Done with functions, let the games begin!
##################################################

def main(argv):
    global log_level
    # First we get options from the commandline
    usage = "usage: %prog [-h|--help] [-l LEVEL|--log=LEVEL]"
    parser = optparse.OptionParser(usage)
    parser.add_option('-l', '--log', action='store', type='int',
                        dest='level', default=2, help='Log level (1-3)')
    (options, args) = parser.parse_args()
    if options.level in range(1, 4):
        log_level = options.level
    else:
        log_it(2, "No such loglevel: %d, using loglevel %d" %
                (options.level, log_level))
    
    log_it(1, "Starting thresholdMon at %s" % date)
    # For each rrd_datasource, fetch the value and compare
    # it to the max-value.
    for rrd_datasource in RrdDataSource.objects.filter(threshold__isnull=False):

        rrd_fileid = rrd_datasource.rrd_file_id
        rrd_datasourceid = rrd_datasource.id
        descr = rrd_datasource.description
        threshold = rrd_datasource.threshold
        max = rrd_datasource.max
        delimiter = rrd_datasource.delimiter
        thresholdstate = rrd_datasource.threshold_state

        log_it(3, "-- NEW DATASOURCE (%s) --" % rrd_datasourceid)
        surpassed = 0

        # These values are silly. They just show how much the maximum value
        # ever in the life of the unit has been, which is totally useless to
        # the thresholdMonitor
        if exceptions.count(descr):
            log_it(3, "%s is in exceptions" % descr)
            continue

        max = int(max)
        log_it(3, "Adding datasource %s" % rrd_datasourceid)
        # Getting the value from the database
        pres.removeAllDs()
        try:
            pres.addDs(rrd_datasourceid)
        except TypeError:
            log_it(3, "Error could not add ds, continuing (%s,%s,%s)" %
                    (rrd_datasourceid))
            continue

        
        # We look at values over the 15 last minutes. 
        pres.fromTime = '-15min'

        log_it(3, "Getting data from %s (%s)" % (rrd_datasourceid, descr))
        if pres.average():
            value = pres.average().pop()
            log_it(3, "Value returned = %s" % value)
        else:
            log_it(3, "No value returned")
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
            
        log_it(3, "Threshold is %s" % threshold)

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
            log_it(2, "--------------------")
            log_it(2, "Threshold surpassed (%s,%s,%s ds:%s)" %
                    (value, threshold, max, rrd_datasourceid))
            # must send danger-event
            makeEvent(pres, descr, threshold, rrd_datasourceid, rrd_fileid, 
                      'active')
        elif surpassed and thresholdstate == 'active':
            log_it(2, "--------------------")
            log_it(2, "Threshold still surpassed. (%s,%s,%s ds:%s)" %
                    (value, threshold, max, rrd_datasourceid))
            makeEvent(pres, descr, threshold, rrd_datasourceid, rrd_fileid,
                      'stillactive')
        elif thresholdstate == 'active':
            log_it(2, "--------------------")
            log_it(2, "Threshold below value (%s,%s,%s ds:%s)" %
                    (value, threshold, max, rrd_datasourceid))
            # Must send nodanger-event
            makeEvent(pres, descr, threshold, rrd_datasourceid, rrd_fileid, 
                  'inactive')
        else:
            log_it(3, "Threshold not surpassed (%s,%s,%s)" %
                    (value, threshold, max))

    end = int(time.time())
    log_it(2, "%s executed in %s seconds." %(sys.argv[0],end-start))
    log_it(2, "------------------------------------------------------------------\n\n")

if __name__ == '__main__':
    main(sys.argv)
