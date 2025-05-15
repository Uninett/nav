#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- testargs: -h -*-
#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
This program controls the service monitoring in NAV.
"""

import os
import sys
import time
import random
import signal
import argparse
import logging

from nav import buildconf
import nav.daemon
from nav.daemon import safesleep as sleep
from nav.logs import init_generic_logging
from nav.statemon import RunQueue, config, db


_logger = logging.getLogger('nav.servicemon')


class Controller:
    def __init__(self, foreground=False):
        if not foreground:
            signal.signal(signal.SIGHUP, self.signalhandler)
        signal.signal(signal.SIGTERM, self.signalhandler)
        signal.signal(signal.SIGINT, self.signalhandler)

        self.conf = config.serviceconf()
        init_generic_logging(stderr=True, read_config=True)
        self._isrunning = 1
        self._checkers = []
        self._looptime = int(self.conf.get("checkinterval", 60))
        _logger.debug("Setting checkinterval=%i", self._looptime)
        self.db = db.db()
        _logger.debug("Reading database config")
        _logger.debug("Setting up runqueue")
        self._runqueue = RunQueue.RunQueue(controller=self)
        self.dirty = 1

    def get_checkers(self):
        """
        Fetches new checkers from the NAV database and appends them to
        the runqueue.
        """
        newcheckers = self.db.get_checkers(self.dirty)
        self.dirty = 0
        # make sure we don't delete all checkers if we get an empty
        # list from the database (maybe we have lost connection to
        # the db)
        if newcheckers:
            s = []
            for i in newcheckers:
                if i in self._checkers:
                    oldchecker = self._checkers[self._checkers.index(i)]
                    s.append(oldchecker)
                else:
                    s.append(i)

            self._checkers = s
        elif self.db.status and self._checkers:
            _logger.info("No checkers left in database, flushing list.")
            self._checkers = []

        # Randomize order of checker plugins
        random.shuffle(self._checkers)

    def main(self):
        """
        Loops until SIGTERM is caught. The looptime is defined
        by self._looptime
        """
        self.db.start()
        while self._isrunning:
            start = time.time()
            self.get_checkers()

            wait = self._looptime - (time.time() - start)
            if wait <= 0:
                _logger.warning(
                    "System clock has drifted backwards, resetting loop delay"
                )
                wait = self._looptime
            if self._checkers:
                pause = wait / (len(self._checkers) * 2)
            else:
                pause = 0
            for checker in self._checkers:
                self._runqueue.enq(checker)
                sleep(pause)

            wait = self._looptime - (time.time() - start)
            _logger.debug("Waiting %i seconds.", wait)
            if wait <= 0:
                _logger.critical(
                    "Only superman can do this. Humans cannot wait for %i seconds.",
                    wait,
                )
                wait %= self._looptime
                sleep(wait)
            else:
                sleep(wait)

    def signalhandler(self, signum, _):
        if signum == signal.SIGTERM:
            _logger.info("Caught SIGTERM. Exiting.")
            self._runqueue.terminate()
            sys.exit(0)
        elif signum == signal.SIGINT:
            _logger.info("Caught SIGINT. Exiting.")
            self._runqueue.terminate()
            sys.exit(0)
        elif signum == signal.SIGHUP:
            # reopen the logfile
            _logger.info("Caught SIGHUP. Reopening logfile...")
            logfile = open(self.conf.logfile, 'a')
            nav.daemon.redirect_std_fds(stdout=logfile, stderr=logfile)

            _logger.info("Reopened logfile: %s", self.conf.logfile)
        else:
            _logger.info("Caught %s. Resuming operation.", signum)


def main(args=None):
    """Daemon main entry point"""
    os.umask(0o0002)
    if args is None:
        args = parse_args()
    foreground = args.foreground
    conf = config.serviceconf()
    pidfilename = conf.get("pidfile", "servicemon.pid")

    # Already running?
    try:
        nav.daemon.justme(pidfilename)
    except nav.daemon.AlreadyRunningError as error:
        sys.exit("servicemon is already running (pid: %s)" % error.pid)
    except nav.daemon.DaemonError as error:
        sys.exit(error)

    if not foreground:
        logfile = open(conf.logfile, 'a')
        nav.daemon.daemonize(pidfilename, stdout=logfile, stderr=logfile)

    my_controller = Controller(foreground=foreground)
    my_controller.main()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Service monitor for NAV (Network Administration Visualized)"
    )
    parser.add_argument(
        '--version', action='version', version='NAV ' + buildconf.VERSION
    )
    parser.add_argument(
        '-f', '--foreground', action="store_true", help="run in foreground"
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()
