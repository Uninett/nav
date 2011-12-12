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
import logging

# import NAV libraries
import nav.buildconf
from nav.event import Event
from nav.rrd import presenter
from nav.models.rrd import RrdFile, RrdDataSource

LOG_FILE = nav.buildconf.localstatedir + "/log/thresholdMon.log"

pres = presenter.presentation()

# Script started
start = time.time()

# Globals
# Exceptions, values that will give 2 alerts if enables
exceptions = ['cpu5min', 'c5000BandwidthMax']
# Default log-level, correspond to INFO
log_level = 2
# Extra slack in calculations
downmodifier = 20
logger = None


def set_state(dsid, descr, state):
    """
    A simple method to set state in the rrd_datasource table
    """
    logger.info("Setting %s to %s" % (descr, state))
    if isinstance(dsid, str) or isinstance(dsid, unicode):
        if dsid.isdigit():
            dsid = int(dsid)
        else:
            logger.error('dsid is an illegal type: %s' % dsid)
            return
    rrd_datasource = None
    try:
        rrd_datasource = RrdDataSource.objects.get(pk=dsid)
    except Exception, get_ex:
        logger.error('%s' % get_ex)
        return

    rrd_datasource.thresholdstate = state
    try:
        rrd_datasource.save()
    except Exception, save_ex:
        logger.error('%s' % save_ex)


def make_event(var, val, subid, fileid, state):
    """
    Makes the event ready for sending and updates the rrd_datasource
    table with the correct information
    calls sendEvent with correct values
    """
    if isinstance(fileid, str) or isinstance(fileid, unicode):
        if fileid.isdigit():
            fileid = int(fileid)
        else:
            logger.error('fileid is an illegal type: %s' % fileid)
            return
    rrd_file = None
    try:
        rrd_file = RrdFile.objects.get(pk=fileid)
    except Exception, get_ex:
        logger.error('%s' % get_ex)
        return

    netboxid = rrd_file.netbox.id
    sysname = rrd_file.netbox.sysname
    ip = rrd_file.netbox.ip

    if netboxid:
        logger.info("thresholdalert regarding %s (%s)" % (sysname, ip))
    if state == 'active':
        logger.info("Threshold on %s surpassed." % var)
        set_state(subid, var, state)
        send_event(var, val, netboxid, state, subid)
    elif state == 'inactive':
        logger.info("%s has calmed down." % var)
        set_state(subid, var, state)
        send_event(var, val, netboxid, state, subid)
    elif state == 'stillactive':
        logger.info("Alert on %s is still active." % var)
    else:
        logger.info("No such state (%s)" % state)


def send_event(var, val, netboxid, state, subid):
    """
    Updates the correct tables for sending the event
    """
    if state == 'active':
        state = 's'
    else:
        state = 'e'

    logger.debug("sending event")

    the_event = Event(source='thresholdMon', target='eventEngine',
                netboxid=netboxid, subid=subid,
                eventtypeid='thresholdState', state=state)
    the_event[var] = val

    try:
        the_event.post()
    except Exception, post_ex:
        logger.error('%s' % post_ex)


def _init_logger():
    """
    Creates a logger for this script, obviously... ;)
    """
    global logger
    filehandler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] ' \
                                  '[%(name)s] L%(lineno)d %(message)s')
    filehandler.setFormatter(formatter)

    logger = logging.getLogger('thresholdMon')
    logger.addHandler(filehandler)
    loglevel = logging.ERROR - (log_level * 10)
    logger.setLevel(loglevel)

##################################################
# Done with functions, let the games begin!
##################################################


def main(argv):
    """
    Main
    """
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
        print >> sys.stderr, ("No such loglevel: %d, using loglevel %d" %
                (options.level, log_level))
    _init_logger()
    logger.info('Starting thresholdMon')
    # For each rrd_datasource, fetch the value and compare
    # it to the max-value.  Threshold can be an empty string.
    for rrd_datasource in RrdDataSource.objects.filter(
                                    threshold__isnull=False).exclude(
                                                            threshold=''):
        rrd_fileid = rrd_datasource.rrd_file_id
        rrd_datasourceid = rrd_datasource.id
        descr = rrd_datasource.description
        threshold = rrd_datasource.threshold
        threshold_max = rrd_datasource.max
        delimiter = rrd_datasource.delimiter
        thresholdstate = rrd_datasource.threshold_state

        logger.debug("-- NEW DATASOURCE (%s) --" % rrd_datasourceid)
        surpassed = 0

        # These values are silly. They just show how much the maximum value
        # ever in the life of the unit has been, which is totally useless to
        # the thresholdMonitor
        if exceptions.count(descr):
            logger.debug("%s is in exceptions" % descr)
            continue

        if threshold_max:
            threshold_max = int(threshold_max)
        logger.debug("Adding datasource %s" % rrd_datasourceid)
        # Getting the value from the database
        pres.removeAllDs()
        try:
            pres.addDs(rrd_datasourceid)
        except TypeError:
            logger.error("Error could not add ds, continuing (%s,%s,%s)" %
                    (rrd_datasourceid))
            continue

        # We look at values over the 15 last minutes.
        pres.fromTime = '-15min'

        logger.debug("Getting data from %s (%s)" % (rrd_datasourceid, descr))
        if pres.average():
            value = pres.average().pop()
            logger.debug("Value returned = %s" % value)
        else:
            logger.debug("No value returned")
            continue

        # Checking if it is percent or a normal value we are comparing
        is_percent = re.compile("%$").search(threshold)
        threshold = re.sub('%$', '', threshold.strip())
        threshold = int(threshold)

        # To prevent oscillation in case the value is just below the threshold
        # we create a lower limit that has to be passed to really say that the
        # crisis os over.
        if thresholdstate == 'active':
            if delimiter == '>':
                threshold = threshold - downmodifier
            elif delimiter == '<':
                threshold = threshold + downmodifier

        if is_percent:
            logger.debug('Threshold is set as %s%%' % threshold)
            if delimiter == '>':
                if ((value / threshold_max) * 100) > threshold:
                    surpassed = 1
            elif delimiter == '<':
                if ((value / threshold_max) * 100) < threshold:
                    surpassed = 1
        else:
            logger.debug("Threshold is %s" % threshold)
            if delimiter == '<' and value < threshold:
                surpassed = 1
            elif delimiter == '>' and value > threshold:
                surpassed = 1

        if surpassed and (thresholdstate == 'inactive' or not thresholdstate):
            logger.info("--------------------")
            logger.info("Threshold surpassed (%s,%s,%s ds:%s)" %
                    (value, threshold, threshold_max, rrd_datasourceid))
            # must send danger-event
            make_event(descr, threshold, rrd_datasourceid, rrd_fileid,
                      'active')
        elif surpassed and thresholdstate == 'active':
            logger.info("--------------------")
            logger.info("Threshold still surpassed. (%s,%s,%s ds:%s)" %
                    (value, threshold, threshold_max, rrd_datasourceid))
            make_event(descr, threshold, rrd_datasourceid, rrd_fileid,
                      'stillactive')
        elif not surpassed and thresholdstate == 'active':
            logger.info("--------------------")
            logger.info("Threshold below value (%s,%s,%s ds:%s)" %
                    (value, threshold, threshold_max, rrd_datasourceid))
            # Must send nodanger-event
            make_event(descr, threshold, rrd_datasourceid, rrd_fileid,
                  'inactive')
        elif not surpassed and (thresholdstate == 'inactive'
                                        or not thresholdstate):
            logger.debug("Threshold not surpassed (%s,%s,%s)" %
                    (value, threshold, threshold_max))
        else:
            logger.warn('This should not happen: surpassed = %d' +
                        '; thresholdstate = %s' % (surpassed, thresholdstate))

    end = time.time()
    logger.info("%s executed in %.2f seconds." % (argv[0], end - start))
    logger.info('-----------------------------------------------' +
                '-------------------\n\n')

if __name__ == '__main__':
    main(sys.argv)
