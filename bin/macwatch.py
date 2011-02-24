#!/usr/bin/env python
#
# Copyright (C) 2011 UNINETT AS
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
from os.path import join
from datetime import datetime

import time
import logging
import logging.handlers
import os
import os.path
import pwd
import sys

# import NAV libraries
import nav.config
import nav.daemon
import nav.logs
import nav.path
import nav.db

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

from nav.models.manage import Cam
from nav.event import Event
from nav.models.profiles import Account
from nav.web.macwatch.models import MacWatch


# These have to be imported after the envrionment is setup
from django.db import DatabaseError, connection
from nav.alertengine.base import check_alerts

LOGFILE = join(nav.buildconf.localstatedir, "log/macwatch.log")
# Loglevel (case-sensitive), may be:
# DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGLEVEL = 'INFO' 

# Occurences of the mac-address nearest to the edges has highest
# priority
location_priority = {u'GSW': 1, u'GW': 1, u'SW': 2, u'EDGE': 3 }

def get_logger():
    """ Return a custom logger """
    format = "[%(asctime)s] [%(levelname)s] %(message)s"
    filehandler = logging.FileHandler(LOGFILE)
    formatter = logging.Formatter(format)
    filehandler.setFormatter(formatter)
    logger = logging.getLogger('macwatch')
    logger.addHandler(filehandler)
    logger.setLevel(logging.getLevelName(LOGLEVEL))
    return logger
 
def prioritize_location(cam_objects, logger):
        # The search may return more than one hits. This happens as mactrace
        # not always manages to calculate the correct topology. In that case
        # choose the result which is "lowest" in the topology. We do this based
        # on catid, where GSW|GW is top followed by SW and then EDGE.

        # Mac _may_ be active on two ports at the same time (due to duplicate
        # mac addresses, error in db and so on). This is such a small problem
        # that we ignore it for the time.
        cam = None
        rank = 0
        for curr_cam in cam_objects:
            logger.debug("Prioritizing %s" % curr_cam.netbox.category_id)
            if location_priority[curr_cam.netbox.category_id] > rank:
                logger.debug("Putting %s first" % curr_cam.netbox.category_id)
                rank = location_priority[curr_cam.netbox.category_id]
                cam = curr_cam
        return cam
   
def post_event(mac_watch, cam, logger):
    """Posts an event on the eventqueue"""

    source = "macwatch"
    target = "eventEngine"
    eventtypeid = "info"
    value = 100
    severity = 50
    event = nav.event.Event(source=source, target=target,
                            deviceid=cam.netbox.device_id,
                            netboxid=cam.netbox.id,
                            eventtypeid=eventtypeid,
                            value=value,
                            severity=severity)
    event['sysname'] = cam.sysname
    if cam.module:
        event['module'] = cam.module
    event['port'] = cam.port
    event['mac'] = mac_watch.mac
    event['alerttype'] = 'macWarning'
    try:
        event.post()
    except Exception, why:
        logger.warning(why)
        return False
    return True

def main():

    # Create logger, start logging
    logger = get_logger()
    logger.info("--> Starting macwatch. Loglevel: %s <--" %LOGLEVEL)

    # For each active macwatch entry, check if mac is active and post event.
    for mac_watch in MacWatch.objects.all():
        logger.info("Checking for activity on %s" % mac_watch.mac)

        cam_objects = Cam.objects.filter(mac=mac_watch.mac,
                                         end_time=datetime.max)
        if len(cam_objects) < 1:
            logger.info("%s is not active" % mac_watch.mac)
            continue

        cam = prioritize_location(cam_objects, logger)
        # cam now contains one tuple from the cam-table

        # Check if the mac-address has moved since last time, continue with
        # next mac if not
        if cam.id == mac_watch.camid_id:
            logger.info("Mac-address is active, but have not moved " +
                            "since last check")
            continue

        # Mac has moved (or appeared). Post event on eventq
        logger.info("%s has appeared on %s (%s:%s)" %
                    (mac_watch.mac, cam.sysname, cam.module, cam.port))
        if post_event(mac_watch, cam, logger):
            logger.info("Event posted")
            # Update macwatch table
            mac_watch.camid = cam
            mac_watch.posted = datetime.now()
            mac_watch.save()
        else:
            logger.warning("Failed to post event, no alert will be given.")

    logger.info("Done checking for macs in %s seconds" %time.clock())


if __name__ == '__main__':
    main()
