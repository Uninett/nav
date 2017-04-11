#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- testargs: -h -*-
#
# Copyright (C) 2002-2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Pings multiple hosts in parallel
"""

from __future__ import print_function

import os
import sys
import signal
import getopt
import time
import logging

import nav.daemon
from nav import buildconf
from nav.daemon import safesleep as sleep
from nav.logs import init_generic_logging, convert_debug_level_to_loglevel
from nav.statemon import statistics
from nav.statemon import megaping
from nav.statemon import db
from nav.statemon import config
from nav.statemon import circbuf
from nav.statemon.event import Event
from nav.statemon.netbox import Netbox


LOGGER = logging.getLogger('nav.pping')


class pinger:
    def __init__(self, **kwargs):
        signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        self.config = config.pingconf()
        init_generic_logging(stderr=True, read_config=True)
        self._isrunning = 1
        self._looptime = int(self.config.get("checkinterval", 60))
        LOGGER.info("Setting checkinterval=%i", self._looptime)
        self.db = db.db()
        sock = kwargs.get("socket", None)
        self.pinger = megaping.MegaPing(sock)
        self._nrping = int(self.config.get("nrping", 3))
        # To keep status...
        self.netboxmap = {}  # hash netboxid -> netbox
        self.down = []       # list of netboxids down
        self.replies = {}    # hash netboxid -> circbuf
        self.ipToNetboxid = {}

    def updateHostList(self):
        """
        Fetches all netboxes from the NAVdb, and updates
        internal data structures.
        """
        LOGGER.debug("Getting hosts from database...")
        hosts = self.db.hosts_to_ping()
        netboxmap = {}
        self.ipToNetboxid = {}
        for host in hosts:
            netboxid, sysname, ip, up = host
            netbox = Netbox(netboxid, sysname, ip, up)
            if not self.netboxmap.has_key(netbox.netboxid):
                # new netbox. Be sure to get it's state
                if netbox.up != 'y':
                    LOGGER.debug(
                        "Got new netbox, %s, currently "
                        "marked down in navDB", netbox.ip)
                    self.down.append(netbox.netboxid)
            if not self.replies.has_key(netbox.netboxid):
                self.replies[netbox.netboxid] = circbuf.CircBuf()
                if netbox.up != 'y':
                    buf = self.replies[netbox.netboxid]
                    # This genious line marks all-down for the whole buf
                    map(buf.push, [-1]*len(buf))
            netboxmap[netbox.netboxid] = netbox
            self.ipToNetboxid[netbox.ip] = netbox.netboxid
        # Update netboxmap
        self.netboxmap = netboxmap
        LOGGER.debug("We now got %i hosts in our list to ping",
                     len(self.netboxmap))
        # then update our pinger object
        self.pinger.set_hosts(self.ipToNetboxid.keys())

    def generateEvents(self):
        """
        Report state changes to event engine.
        """
        LOGGER.debug("Checks which hosts didn't answer")
        answers = self.pinger.results()
        for ip, rtt in answers:
            # rtt = round trip time (-1 => host didn't reply)
            netboxid = self.ipToNetboxid.get(ip)
            self.replies[netboxid].push(rtt)
            netbox = self.netboxmap[netboxid]
            if rtt != -1:
                statistics.update(netbox.netboxid, netbox.sysname, 'N', 'UP',
                                  rtt)
            else:
                # ugly...
                statistics.update(netbox.netboxid, netbox.sysname, 'N', 'DOWN',
                                  5)

        downNow = []
        # Find out which netboxes to consider down
        for (netboxid, replies) in self.replies.items():
            if replies[:self._nrping] == [-1]*self._nrping:
                downNow.append(netboxid)

        LOGGER.debug("No answer from %i hosts", len(downNow))
        # Detect state changes since last run
        reportDown = filter(lambda x: x not in self.down, downNow)
        reportUp = filter(lambda x: x not in downNow, self.down)
        self.down = downNow

        # Reporting netboxes as down
        LOGGER.debug("Starts reporting %i hosts as down", len(reportDown))
        for netboxid in reportDown:
            netbox = self.netboxmap[netboxid]
            newEvent = Event(None,
                             netbox.netboxid,
                             None,  # deviceid
                             Event.boxState,
                             "pping",
                             Event.DOWN
                             )
            self.db.new_event(newEvent)
            LOGGER.info("%s marked as down.", netbox)
        # Reporting netboxes as up
        LOGGER.debug("Starts reporting %i hosts as up", len(reportUp))
        for netboxid in reportUp:
            try:
                netbox = self.netboxmap[netboxid]
            except:
                LOGGER.info("Netbox %s is no longer with us...", netboxid)
                continue
            newEvent = Event(None,
                             netbox.netboxid,
                             None,  # deviceid
                             Event.boxState,
                             "pping",
                             Event.UP
                             )
            self.db.new_event(newEvent)
            LOGGER.info("%s marked as up.", netbox)

    def main(self):
        """
        Loops until SIGTERM is caught.
        """
        self.db.start()
        while self._isrunning:
            LOGGER.debug("Starts pinging....")
            self.updateHostList()
            elapsedtime = self.pinger.ping()
            self.generateEvents()
            LOGGER.info("%i hosts checked in %03.3f secs. %i hosts "
                        "currently marked as down.",
                        len(self.netboxmap), elapsedtime, len(self.down))
            wait = self._looptime-elapsedtime
            if wait > 0:
                LOGGER.info("Sleeping %03.3f secs", wait)
            else:
                wait = abs(self._looptime + wait)
                LOGGER.critical("Check lasted longer than looptime. "
                                "Delaying next check for %03.3f secs", wait)
            sleep(wait)

    def signalhandler(self, signum, frame):
        if signum == signal.SIGTERM:
            LOGGER.critical("Caught SIGTERM. Exiting.")
            sys.exit(0)
        elif signum == signal.SIGHUP:
            # reopen the logfile
            logfile_path = self.config.get("logfile", "pping.log")
            LOGGER.info("Caught SIGHUP. Reopening logfile...")
            logfile = file(logfile_path, 'a')
            nav.daemon.redirect_std_fds(stdout=logfile, stderr=logfile)

            LOGGER.info("Reopened logfile: %s", logfile_path)
        else:
            LOGGER.critical("Caught %s. Resuming operation.", signum)


def help():
    print(("""Parallel pinger for NAV (Network Administration Visualized).

    Usage: %s [OPTIONS]
    -h  --help      Displays this message
    -n  --nofork    Run in foreground

    """ % os.path.basename(sys.argv[0])))


def start(nofork):
    """
    Forks a new prosess, letting the service run as
    a daemon.
    """
    conf = config.pingconf()
    pidfilename = conf.get(
        "pidfile", os.path.join(buildconf.localstatedir, "run", "pping.pid"))

    # Already running?
    try:
        nav.daemon.justme(pidfilename)
    except nav.daemon.AlreadyRunningError, e:
        otherpid = file(pidfilename, "r").read().strip()
        sys.stderr.write("pping is already running (pid: %s)\n" % otherpid)
        sys.exit(1)
    except nav.daemon.DaemonError, e:
        sys.stderr.write("%s\n" % e)
        sys.exit(1)

    if not nofork:
        logfile_path = conf.get(
            'logfile',
            os.path.join(buildconf.localstatedir, 'log','pping.log'))
        logfile = file(logfile_path, "a")
        nav.daemon.daemonize(pidfilename, stdout=logfile, stderr=logfile)

    myPinger = pinger(socket=sock)
    myPinger.main()


def setUser():
    conf = config.pingconf()
    username = conf.get("user", "nobody")
    nav.daemon.switchuser(username)


if __name__ == "__main__":
    nofork = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hn",
                                   ["help", "nofork"])
        for opt, val in opts:
            if opt in ("-h", "--help"):
                help()
                sys.exit(0)
            elif opt in ("-n", "--nofork"):
                nofork = 1

    except getopt.error:
        help()
        sys.exit(2)
    if os.getuid() != 0:
        print("Must be started as root")
        sys.exit(1)
    sock = megaping.make_sockets()
    setUser()
    start(nofork)
