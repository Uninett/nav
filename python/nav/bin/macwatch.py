#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2011, 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Searches NAV's cam logs and reports the closest location of surveilled MAC
addresses, if found.
"""

from datetime import datetime

import time
import logging

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

# import NAV libraries
import nav.logs

from nav.models.manage import Cam
from nav.event import Event
from nav.web.macwatch.models import MacWatch
from nav.web.macwatch.models import MacWatchMatch


LOGFILE = "macwatch.log"
_logger = logging.getLogger('nav.macwatch')

# Occurences of the mac-address nearest to the edges has highest
# priority
LOCATION_PRIORITY = {'GSW': 1, 'GW': 1, 'SW': 2, 'EDGE': 3}


def prioritize_location(cam_objects):
    """Try to find an entry for a cam-object that is closest
    to the edge of a network."""
    # The search may return more than one hits. This happens as mactrace
    # not always manages to calculate the correct topology. In that case
    # choose the result which is "lowest" in the topology. We do this based
    # on catid, where GSW|GW is top followed by SW and then EDGE.

    # Mac _may_ be active on two ports at the same time (due to duplicate
    # mac addresses, error in db and so on). This is such a small problem
    # that we ignore it for the time.
    prioritized_cams = {0: []}
    for value in LOCATION_PRIORITY.values():
        if value not in prioritized_cams:
            prioritized_cams[value] = []
    for curr_cam in cam_objects:
        category = curr_cam.netbox.category_id
        prioritized_cams[LOCATION_PRIORITY[category]].append(curr_cam)
    rank = 0
    for value in LOCATION_PRIORITY.values():
        if prioritized_cams[value] and value > rank:
            rank = value
    _logger.debug('Returning %s', prioritized_cams.get(rank))
    return prioritized_cams.get(rank)


def post_event(mac_watch, cam):
    """Post an event on the event-queue, obviously..."""
    source = "macwatch"
    target = "eventEngine"
    eventtypeid = "info"
    value = 100
    severity = 5
    event = Event(
        source=source,
        target=target,
        netboxid=cam.netbox.id,
        eventtypeid=eventtypeid,
        value=value,
        severity=severity,
    )
    event['sysname'] = cam.sysname
    if cam.module:
        event['module'] = cam.module
    event['port'] = cam.port
    event['mac'] = cam.mac
    event['macwatch-mac'] = mac_watch.mac
    event['alerttype'] = 'macWarning'
    try:
        event.post()
    except Exception:  # noqa: BLE001
        _logger.exception("Unhandled exception while posting event")
        return False
    return True


def find_the_latest(macwatch_matches):
    """Find the match that have posted an event latest"""
    latest_time = datetime.min
    match_to_keep = None
    for macwatch_match in macwatch_matches:
        if macwatch_match.posted and macwatch_match.posted > latest_time:
            latest_time = macwatch_match.posted
            match_to_keep = macwatch_match
    return match_to_keep


def delete_unwanted_matches(macwatch_matches):
    """Delete unwanted matches, but keep the match
    that have posted an event latest in time."""
    match_to_keep = find_the_latest(macwatch_matches)
    for macwatch_match in macwatch_matches:
        if match_to_keep and match_to_keep.id == macwatch_match.id:
            continue
        else:
            _logger.info(
                'Deleting match %s; macwatch = %s',
                macwatch_match.id,
                macwatch_match.macwatch.id,
            )
            macwatch_match.delete()


def main():
    """Start the show.  You haven't seen nothing yet..."""
    # Create logger, start logging
    nav.logs.init_generic_logging(logfile=LOGFILE, stderr=False, read_config=True)
    start_time = time.time()
    _logger.info("--> Starting macwatch <--")

    # For each active macwatch entry, check if mac is active and post event.
    for mac_watch in MacWatch.objects.all():
        _logger.info("Checking for activity on %s", mac_watch.mac)

        if mac_watch.prefix_length:
            mac = mac_watch.get_mac_prefix()
            _logger.debug(
                'Mac-addresses; prefix = %s and upper mac = %s', mac[0], mac[-1]
            )
            cam_objects = Cam.objects.filter(
                mac__gte=mac[0],
                mac__lte=mac[-1],
                end_time=datetime.max,
                netbox__isnull=False,
            )
        else:
            cam_objects = Cam.objects.filter(
                mac=mac_watch.mac, end_time=datetime.max, netbox__isnull=False
            )
        if len(cam_objects) < 1:
            _logger.info("%s is not active", mac_watch.mac)
            continue

        cam_by_mac = {}
        for cam_obj in cam_objects:
            if cam_obj.mac not in cam_by_mac:
                cam_by_mac[cam_obj.mac] = []
            cam_by_mac[cam_obj.mac].append(cam_obj)

        for cams in cam_by_mac.values():
            _logger.debug('Cam-objects length %s; cam-objects = %s', len(cams), cams)
            prioritized_cams = prioritize_location(cams)
            for cam in prioritized_cams:
                macwatch_matches = MacWatchMatch.objects.filter(
                    macwatch=mac_watch, cam=cam
                )

                # Check if the mac-address has moved since last time,
                # continue with next mac if not.
                if len(macwatch_matches) == 1:
                    _logger.info(
                        "Mac-address is active, but have not moved since last check"
                    )
                    continue

                if len(macwatch_matches) > 1:
                    # Something strange has happened, delete all but
                    # the match that has posted an event latest in time.
                    _logger.info(
                        '%s matches found for macwatch = %s',
                        len(macwatch_matches),
                        mac_watch.id,
                    )
                    delete_unwanted_matches(macwatch_matches)
                    continue

                # Mac has moved (or appeared). Post event on eventq
                _logger.info(
                    "%s has appeared on %s (%s:%s)",
                    cam.mac,
                    cam.sysname,
                    cam.module,
                    cam.port,
                )
                if post_event(mac_watch, cam):
                    _logger.info("Event posted for macwatch = %s", mac_watch.id)
                    new_macwatch_match = MacWatchMatch(
                        macwatch=mac_watch, cam=cam, posted=datetime.now()
                    )
                    new_macwatch_match.save()
                else:
                    _logger.warning("Failed to post event, no alert will be given.")

    _logger.info(
        "--> Done checking for macs in %.3f seconds <--", time.time() - start_time
    )


if __name__ == '__main__':
    main()
