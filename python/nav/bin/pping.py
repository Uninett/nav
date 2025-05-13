#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- testargs: -h -*-
#
# Copyright (C) 2018 Uninett AS
# Copyright (C) 2020 Universitetet i Oslo
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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

import os
import sys
import signal
import argparse
import logging

import nav.daemon
from nav.config import NAV_CONFIG
from nav.daemon import safesleep as sleep
from nav.logs import init_generic_logging
from nav.statemon import statistics
from nav.statemon import megaping
from nav.statemon import db
from nav.statemon import config
from nav.statemon import circbuf
from nav.statemon.event import Event
from nav.statemon.netbox import Netbox


_logger = logging.getLogger('nav.pping')


def main():
    args = make_argparser().parse_args()

    if os.getuid() != 0:
        print("Must be started as root")
        sys.exit(1)

    socket = megaping.make_sockets()  # make raw sockets while we have root
    nav.daemon.switchuser(NAV_CONFIG['NAV_USER'])
    start(args.foreground, socket)


def make_argparser():
    parser = argparse.ArgumentParser(description="Parallel pinger daemon (part of NAV)")
    parser.add_argument(
        "-f", "--foreground", action="store_true", help="run in foreground"
    )
    return parser


class Pinger(object):
    def __init__(self, socket=None, foreground=False):
        if not foreground:
            signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        signal.signal(signal.SIGINT, self.signalhandler)

        self.config = config.pingconf()
        init_generic_logging(stderr=True, read_config=True)
        self._isrunning = 1
        self._looptime = int(self.config.get("checkinterval", 60))
        _logger.info("Setting checkinterval=%i", self._looptime)
        self.db = db.db()
        self.pinger = megaping.MegaPing(socket)
        self._nrping = int(self.config.get("nrping", 3))
        # To keep status...
        self.netboxmap = {}  # hash netboxid -> netbox
        self.down = []  # list of netboxids down
        self.replies = {}  # hash netboxid -> circbuf
        self.ip_to_netboxid = {}

    def update_host_list(self):
        """
        Fetches all netboxes from the NAVdb, and updates
        internal data structures.
        """
        _logger.debug("Getting hosts from database...")
        netbox_included_groups = self.config.get("groups_included", "").split()
        netbox_excluded_groups = self.config.get("groups_excluded", "").split()
        hosts = self.db.hosts_to_ping(netbox_included_groups, netbox_excluded_groups)
        netboxmap = {}
        self.ip_to_netboxid = {}
        for host in hosts:
            netboxid, sysname, ip, up = host
            netbox = Netbox(netboxid, sysname, ip, up)
            if netbox.netboxid not in self.netboxmap:
                # new netbox. Be sure to get it's state
                if netbox.up != 'y':
                    _logger.debug(
                        "Got new netbox, %s, currently marked down in navDB",
                        netbox.ip,
                    )
                    self.down.append(netbox.netboxid)
            if netbox.netboxid not in self.replies:
                self.replies[netbox.netboxid] = circbuf.CircBuf(self._nrping)
                if netbox.up != 'y':
                    self.replies[netbox.netboxid].reset_all_to(-1)
            netboxmap[netbox.netboxid] = netbox
            self.ip_to_netboxid[netbox.ip] = netbox.netboxid
        # Update netboxmap
        self.netboxmap = netboxmap
        _logger.debug("We now got %i hosts in our list to ping", len(self.netboxmap))
        # then update our pinger object
        self.pinger.set_hosts(self.ip_to_netboxid.keys())

    def generate_events(self):
        """
        Report state changes to event engine.
        """
        _logger.debug("Checks which hosts didn't answer")
        answers = self.pinger.results()
        for ip, rtt in answers:
            # rtt = round trip time (-1 => host didn't reply)
            netboxid = self.ip_to_netboxid.get(ip)
            self.replies[netboxid].push(rtt)
            netbox = self.netboxmap[netboxid]
            if rtt != -1:
                statistics.update(netbox.sysname, 'N', 'UP', rtt)
            else:
                # ugly...
                statistics.update(netbox.sysname, 'N', 'DOWN', 5)

        down_now = []
        # Find out which netboxes to consider down
        for netboxid, replies in self.replies.items():
            if replies[: self._nrping] == [-1] * self._nrping:
                down_now.append(netboxid)

        _logger.debug("No answer from %i hosts", len(down_now))
        # Detect state changes since last run
        report_down = set(down_now) - set(self.down)
        report_up = set(self.down) - set(down_now)
        self.down = down_now

        # Reporting netboxes as down
        _logger.debug("Starts reporting %i hosts as down", len(report_down))
        for netboxid in report_down:
            netbox = self.netboxmap[netboxid]
            new_event = Event(
                None,
                netbox.netboxid,
                None,  # deviceid
                Event.boxState,
                "pping",
                Event.DOWN,
            )
            self.db.new_event(new_event)
            _logger.info("%s marked as down.", netbox)
        # Reporting netboxes as up
        _logger.debug("Starts reporting %i hosts as up", len(report_up))
        for netboxid in report_up:
            try:
                netbox = self.netboxmap[netboxid]
            except:
                _logger.info("Netbox %s is no longer with us...", netboxid)
                continue
            new_event = Event(
                None,
                netbox.netboxid,
                None,  # deviceid
                Event.boxState,
                "pping",
                Event.UP,
            )
            self.db.new_event(new_event)
            _logger.info("%s marked as up.", netbox)

    def main(self):
        """
        Loops until SIGTERM is caught.
        """
        self.db.start()
        while self._isrunning:
            _logger.debug("Starts pinging....")
            self.update_host_list()
            elapsedtime = self.pinger.ping()
            self.generate_events()
            _logger.info(
                "%i hosts checked in %03.3f secs. %i hosts currently marked as down.",
                len(self.netboxmap),
                elapsedtime,
                len(self.down),
            )
            wait = self._looptime - elapsedtime
            if wait > 0:
                _logger.debug("Sleeping %03.3f secs", wait)
            else:
                wait = abs(self._looptime + wait)
                _logger.warning(
                    "Check lasted longer than looptime. "
                    "Delaying next check for %03.3f secs",
                    wait,
                )
            sleep(wait)

    def signalhandler(self, signum, _frame):
        if signum == signal.SIGTERM:
            _logger.critical("Caught SIGTERM. Exiting.")
            sys.exit(0)
        elif signum == signal.SIGINT:
            _logger.critical("Caught SIGINT. Exiting.")
            sys.exit(0)
        elif signum == signal.SIGHUP:
            # reopen the logfile
            conf = config.pingconf()
            _logger.info("Caught SIGHUP. Reopening logfile...")
            logfile = open(conf.logfile, 'a')
            nav.daemon.redirect_std_fds(stdout=logfile, stderr=logfile)

            _logger.info("Reopened logfile: %s", conf.logfile)
        else:
            _logger.critical("Caught %s. Resuming operation.", signum)


def start(foreground, socket):
    """
    Starts a new process, letting the service run as a daemon if `foreground`
    is false.
    """
    conf = config.pingconf()
    pidfilename = "pping.pid"

    if not foreground:
        # Already running?
        try:
            nav.daemon.justme(pidfilename)
        except nav.daemon.AlreadyRunningError as error:
            sys.exit("pping is already running (pid: %s)" % error.pid)
        except nav.daemon.DaemonError as error:
            sys.exit(error)

        logfile = open(conf.logfile, "a")
        nav.daemon.daemonize(pidfilename, stdout=logfile, stderr=logfile)
    else:
        nav.daemon.writepidfile(pidfilename)

    my_pinger = Pinger(socket=socket, foreground=foreground)
    my_pinger.main()


if __name__ == '__main__':
    main()
