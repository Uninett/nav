#
# Copyright (C) 2012 UNINETT AS
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
"Process control for multi-process invocation of ipdevpoll"

import sys
import logging

from twisted.runner import procmon
from twisted.internet import reactor

from . import config

_logger = logging.getLogger(__name__)

def run_as_multiprocess():
    "Sets up a process monitor to run each ipdevpoll job as a subprocess"
    procmon.LineLogger.lineReceived = line_received
    mon = ProcessMonitor()
    jobs = config.get_jobs()

    for job in jobs:
        mon.addProcess(job.name,
                       [get_process_command(),
                        '-J', job.name, '-f', '-s', '-P'])

    reactor.callWhenRunning(mon.startService)
    return mon

def get_process_command():
    "Tries to return the path to the current executable"
    return sys.argv[0]

def line_received(_, line):
    """Prints line to stderr.

    Used to monkeypatch procmon.LineLogger.lineReceived so that received lines
    will be logged the ipdevpoll way.

    """
    print >> sys.stderr, line

class ProcessMonitor(procmon.ProcessMonitor):
    "A ProcessMonitor variant that properly logs dead children"
    # an expected API name:
    # pylint: disable=C0103
    def connectionLost(self, name):
        _logger.warning("Subprocess %s died, restart will be tried", name)
        return procmon.ProcessMonitor.connectionLost(self, name)

