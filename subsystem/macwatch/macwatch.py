#!/usr/bin/env python
#
# $Id$
#
# Copyright 2008 Norwegian University of Science and Technology
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
# Authors: John Magne Bredal <john.m.bredal@ntnu.no>
#

__copyright__ = "Copyright 2008 NTNU"
__license__ = "GPL"
__author__ = "John Magne Bredal <john.m.bredal@ntnu.no>"

# import Python libraries
import logging
import sys
import time
from os.path import join

# import NAV libraries
import nav.db
import nav.errors
import nav.buildconf
from nav.event import Event

LOGFILE = join(nav.buildconf.localstatedir, "log/macwatch.log")
# Loglevel (case-sensitive), may be:
# DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGLEVEL = 'INFO' 


def main():

    # Create logger, start logging
    format = "[%(asctime)s] [%(levelname)s] %(message)s"
    filehandler = logging.FileHandler(LOGFILE)
    formatter = logging.Formatter(format)
    filehandler.setFormatter(formatter)
    logger = logging.getLogger('macwatch')
    logger.addHandler(filehandler)
    logger.setLevel(logging.getLevelName(LOGLEVEL))

    logger.info("--> Starting macwatch. Loglevel: %s <--" %LOGLEVEL)

    # Connect to db
    try:
        conn = nav.db.getConnection('default')
        c = conn.cursor()
    except Exception, e:
        logger.error("Could not connect to database: %s" %e)
        sys.exit()

    # Find active macwatches
    sql = "SELECT * FROM macwatch"
    c.execute(sql)

    # For each active macwatch entry, check if mac is active and post event.
    for row in c.dictfetchall():
        logger.info("Checking for activity on %s" %row['mac'])

        sql = """SELECT * FROM cam JOIN netbox USING (netboxid) WHERE mac=%s
        AND end_time='infinity'"""

        c.execute(sql, (row['mac'],))
        result = c.dictfetchall()

        if len(result) < 1:
            logger.info("Not active")
            continue

        # The search may return more than one hits. This happens as mactrace
        # not always manages to calculate the correct topology. In that case
        # choose the result which is "lowest" in the topology. We do this based
        # on catid, where GSW|GW is top followed by SW and then EDGE.

        # Mac _may_ be active on two ports at the same time (due to duplicate
        # mac addresses, error in db and so on). This is such a small problem
        # that we ignore it for the time.
        pri = { 'GSW': 1, 'GW': 1, 'SW': 2, 'EDGE': 3 }
        cam = {}
        rank = 0
        for camtuple in result:
            logger.debug("Prioritizing %s" %camtuple['catid'])
            if pri[camtuple['catid']] > rank:
                logger.debug("Putting %s first" %camtuple['catid'])
                rank = pri[camtuple['catid']]
                cam = camtuple

        # cam now contains one tuple from the cam-table

        # Check if the mac-address has moved since last time, continue with
        # next mac if not
        if cam['camid'] == row['camid']:
            logger.info("Active, but not moved since last check")
            continue

        # Mac has moved (or appeared). Post event on eventq
        logger.info("%s has appeared on %s (%s:%s)"
                    %(row['mac'], cam['sysname'], cam['module'], cam['port']))
        if postEvent(cam, logger):
            logger.info("Event posted")
            # Update macwatch table
            sql = """UPDATE macwatch SET camid = %s, posted = now()
            WHERE id = %s"""
            c.execute(sql, (cam['camid'], row['id']))
            conn.commit()
        else:
            logger.warning("Failed to post event, no alert will be given.")


    logger.info("Done checking for macs in %s seconds" %time.clock())
        


def postEvent(camtuple, logger):
    """Posts an event on the eventqueue"""

    source = "macwatch"
    target = "eventEngine"
    eventtypeid = "info"

    e = Event(source=source, target=target, eventtypeid=eventtypeid)
    e['sysname'] = camtuple['sysname']
    e['module'] = camtuple['module']
    e['port'] = camtuple['port']
    e['mac'] = camtuple['mac']
    e['alerttype'] = 'macWarning'

    try:
        e.post()
    except Exception, why:
        logger.warning(why)
        return False

    return True
    

if __name__ == '__main__':
    main()
