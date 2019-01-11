# -*- coding: utf-8 -*-
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
"""DHCP service checker"""

import os
import subprocess

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event
from nav.util import which, is_setuid_root


class DhcpChecker(AbstractChecker):
    """DHCP"""
    DESCRIPTION = "DHCP"
    OPTARGS = (
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=0, **kwargs)

    def execute(self):
        ip, _port = self.get_address()

        cmd = 'dhcping'

        path = which(cmd)
        if not path:
            return (Event.DOWN,
                    'Command %s not found in %s' % (cmd, os.environ['PATH']))

        if not is_setuid_root(path):
            return Event.DOWN, '%s must be setuid root' % path

        try:
            proc = subprocess.Popen(
                [path,
                 '-i',  # Use inform packet so we don't have to be valid client
                 '-s', ip,
                 '-t', str(self.timeout),  # Timeout in seconds
                 ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            proc.wait()

            proc.stdout.read()
            stderr = proc.stderr.read()

            if proc.returncode != 0:
                return Event.DOWN, repr(stderr.strip())
        except IOError as msg:
            return Event.DOWN, 'Could not run dhcping: %s' % msg

        return Event.UP, 'OK'
