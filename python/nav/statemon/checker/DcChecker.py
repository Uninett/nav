#
# Copyright (C) 2003,2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Domain Controller service checker"""

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
from nav.util import which
import os
import subprocess


class DcChecker(AbstractChecker):
    """Domain Controller"""
    TYPENAME = "dc"
    DESCRIPTION = "Domain Controller"
    ARGS = (
        ('username', ''),
    )

    def execute(self):
        args = self.getArgs()
        username = args.get('username', '')
        if not username:
            return Event.DOWN, "Missing required argument: username"

        ip, _port = self.getAddress()

        cmd = 'rpcclient'
        cmdpath = which(cmd)
        if not cmdpath:
            return (Event.DOWN,
                    'Command %s not found in %s' % (cmd, os.environ['PATH']))

        try:
            proc = subprocess.Popen([cmdpath,
                                     '-U', '%',
                                     '-c',
                                     'lookupnames ' + username,
                                     ip],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            
            proc.wait()
        except OSError, msg:
            return Event.DOWN, 'could not run rpcclient: %s' % msg

        if proc.returncode != 0:
            errline = proc.stdout.readline()
            return (Event.DOWN,
                    "rpcclient returned %s: %s" % (proc.returncode, errline))

        output = proc.stdout.readlines()
        lastline = output[-1]
        if lastline.split()[0] == username:
            return Event.UP, 'Ok'
        else:
            return Event.DOWN, lastline
