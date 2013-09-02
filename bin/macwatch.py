#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
"""This is a very clever script to find mac-addresses that should
be under surveillance and report the closest location if the
mac-address is found."""

from os.path import join
from datetime import datetime

import re
import time
import logging

# import NAV libraries
import nav.logs

from nav.models.manage import Cam
from nav.event import Event
from nav.web.macwatch.models import MacWatch
from nav.web.macwatch.models import MacWatchMatch


LOGFILE = join(nav.buildconf.localstatedir, "log/macwatch.log")
# Loglevel (case-sensitive), may be:
# DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGLEVEL = 'INFO'

# Max number of nybbles in a mac-address.
MAC_ADDR_MAX_LEN = 12
# Used for filling in a max adddress value when
# only a prefix is given.
MAC_ADDR_MAX_VAL = 'ffffffffffff'
# Possible delimiters as regexps
STRIP_MAC_ADDR_DELIMS = ['-', ':']
# The returning mac-address will use this as delimiter
RET_MAC_ADDR_DELIM = ':'

# Occurences of the mac-address nearest to the edges has highest
# priority
LOCATION_PRIORITY = {u'GSW': 1, u'GW': 1, u'SW': 2, u'EDGE': 3}


def get_logger():
    """ Return a custom logger """
    log_format = "[%(asctime)s] [%(levelname)s] %(message)s"
    filehandler = logging.FileHandler(LOGFILE)
    formatter = logging.Formatter(log_format)
    filehandler.setFormatter(formatter)
    logger = logging.getLogger('macwatch')
    logger.addHandler(filehandler)
    logger.setLevel(logging.getLevelName(LOGLEVEL))
    return logger


def prioritize_location(cam_objects, logger):
    """Try to find an entry for a cam-object that is closest
    to the edge of a network."""
    # The search may return more than one hits. This happens as mactrace
    # not always manages to calculate the correct topology. In that case
    # choose the result which is "lowest" in the topology. We do this based
    # on catid, where GSW|GW is top followed by SW and then EDGE.

    # Mac _may_ be active on two ports at the same time (due to duplicate
    # mac addresses, error in db and so on). This is such a small problem
    # that we ignore it for the time.
    prioritized_cams = {0: [], }
    for value in LOCATION_PRIORITY.itervalues():
        if not value in prioritized_cams:
            prioritized_cams[value] = []
    for curr_cam in cam_objects:
        category = curr_cam.netbox.category_id
        prioritized_cams[LOCATION_PRIORITY[category]].append(curr_cam)
    rank = 0
    for value in LOCATION_PRIORITY.itervalues():
        if prioritized_cams[value] and value > rank:
            rank = value
    logger.debug('Returning %s' % str(prioritized_cams.get(rank)))
    return prioritized_cams.get(rank)


def post_event(mac_watch, cam, logger):
    """Post an event on the event-queue, obviously..."""
    source = "macwatch"
    target = "eventEngine"
    eventtypeid = "info"
    value = 100
    severity = 50
    event = Event(source=source, target=target,
                  deviceid=cam.netbox.device_id,
                  netboxid=cam.netbox.id,
                  eventtypeid=eventtypeid,
                  value=value,
                  severity=severity)
    event['sysname'] = cam.sysname
    if cam.module:
        event['module'] = cam.module
    event['port'] = cam.port
    event['mac'] = cam.mac
    event['macwatch-mac'] = mac_watch.mac
    event['alerttype'] = 'macWarning'
    try:
        event.post()
    except Exception, why:
        logger.warning(why)
        return False
    return True


def strip_delimiters(mac_addr):
    """Strip mac-address delimiters, legal delimiters are
    defined in the constant STRIP_MAC_ADDR_DELIMS."""
    stripped_addr = mac_addr
    for delim in STRIP_MAC_ADDR_DELIMS:
        stripped_addr = re.sub(delim, '', stripped_addr)
    return stripped_addr


def insert_addr_delimiters(mac_addr):
    """Insert mac-address delimiters (:) between every
    hex-number."""
    start = end = 0
    hex_numbers = []
    while end < (MAC_ADDR_MAX_LEN - 2):
        end = start + 2
        hex_numbers.append(mac_addr[start:end])
        start += 2
    hex_numbers.append(mac_addr[end:])
    return RET_MAC_ADDR_DELIM.join(hex_numbers)


def make_upper_mac_addr(mac_addr, last_pos):
    """Replace all nybbles in a mac-address with
    'f' from a specified index."""
    filtered_macaddr = strip_delimiters(mac_addr)
    full_mac_addr = filtered_macaddr
    if last_pos < MAC_ADDR_MAX_LEN:
        full_mac_addr = (filtered_macaddr[0:last_pos] +
                         MAC_ADDR_MAX_VAL[last_pos:])
    return insert_addr_delimiters(full_mac_addr)


def find_the_latest(macwatch_matches):
    """Find the match that have posted an event latest"""
    latest_time = datetime.min
    match_to_keep = None
    for macwatch_match in macwatch_matches:
        if (macwatch_match.posted and
                macwatch_match.posted > latest_time):
            latest_time = macwatch_match.posted
            match_to_keep = macwatch_match
    return match_to_keep


def delete_unwanted_matches(macwatch_matches, logger):
    """Delete unwanted matches, but keep the match
    that have posted an event latest in time."""
    match_to_keep = find_the_latest(macwatch_matches)
    for macwatch_match in macwatch_matches:
        if (match_to_keep and
                match_to_keep.id == macwatch_match.id):
            continue
        else:
            logger.info('Deleting match %d; macwatch = %d' %
                        (macwatch_match.id,
                         macwatch_match.macwatch.id))
            macwatch_match.delete()


def main():
    """Start the show.  You haven't seen nothing yet..."""
    # Create logger, start logging
    logger = get_logger()
    logger.info("--> Starting macwatch. Loglevel: %s <--", LOGLEVEL)

    # For each active macwatch entry, check if mac is active and post event.
    for mac_watch in MacWatch.objects.all():
        logger.info("Checking for activity on %s", mac_watch.mac)

        cam_objects = []
        # Substitute zeroes in mac-addresses with 'f' if we
        # are searching for mac-addresses by a prefix.
        # The search is done with:
        # mac-addr > prefix:00:00 and mac-address < prefix:ff:ff
        if mac_watch.prefix_length:
            upper_mac_addr = make_upper_mac_addr(mac_watch.mac,
                                                 mac_watch.prefix_length)
            logger.debug('Mac-addresses; prefix = %s and upper mac = %s' %
                         (mac_watch.mac, upper_mac_addr))
            cam_objects = Cam.objects.filter(mac__gte=mac_watch.mac,
                                             mac__lte=upper_mac_addr,
                                             end_time=datetime.max,
                                             netbox__isnull=False)
        else:
            cam_objects = Cam.objects.filter(mac=mac_watch.mac,
                                             end_time=datetime.max,
                                             netbox__isnull=False)
        if len(cam_objects) < 1:
            logger.info("%s is not active", mac_watch.mac)
            continue

        cam_by_mac = {}
        for cam_obj in cam_objects:
            if not cam_obj.mac in cam_by_mac:
                cam_by_mac[cam_obj.mac] = []
            cam_by_mac[cam_obj.mac].append(cam_obj)

        for cams in cam_by_mac.itervalues():
            logger.debug('Cam-objects length %d; cam-objects = %s' %
                         (len(cams), str(cams)))
            prioritized_cams = prioritize_location(cams, logger)
            for cam in prioritized_cams:
                macwatch_matches = MacWatchMatch.objects.filter(
                    macwatch=mac_watch, cam=cam)

                # Check if the mac-address has moved since last time,
                # continue with next mac if not.
                if len(macwatch_matches) == 1:
                    logger.info("Mac-address is active, but have not moved " +
                                "since last check")
                    continue

                if len(macwatch_matches) > 1:
                    # Something strange has happened, delete all but
                    # the match that has posted an event latest in time.
                    logger.info('%d matches found for macwatch = %d' %
                                (len(macwatch_matches), mac_watch.id))
                    delete_unwanted_matches(macwatch_matches, logger)
                    continue

                # Mac has moved (or appeared). Post event on eventq
                logger.info("%s has appeared on %s (%s:%s)" %
                            (cam.mac, cam.sysname, cam.module, cam.port))
                if post_event(mac_watch, cam, logger):
                    logger.info("Event posted for macwatch = %d" %
                                mac_watch.id)
                    new_macwatch_match = MacWatchMatch(macwatch=mac_watch,
                                                       cam=cam,
                                                       posted=datetime.now())
                    new_macwatch_match.save()
                else:
                    logger.warning("Failed to post event, no alert " +
                                   "will be given.")

    logger.info("--> Done checking for macs in %s seconds <--" %
                str(time.clock()))


if __name__ == '__main__':
    main()
