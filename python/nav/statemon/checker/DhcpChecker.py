# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 University of Tromsø
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

import os
import subprocess

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
from nav.util import which, is_setuid_root

class DhcpChecker(AbstractChecker):
    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, "dhcp", service, port=0, **kwargs)

    def execute(self):
        ip, port = self.getAddress()
        timeout = self.getTimeout()
        
        cmd = 'dhcping'

        path = which(cmd)
        if not path:
            return Event.DOWN, 'Command %s not found in %s' % (cmd, os.environ['PATH'])

        if not is_setuid_root(path):
            return Event.DOWN, '%s must be setuid root' % path

        try:
            p = subprocess.Popen([path,
                                  '-i',  # Use an inform packet so we don't have to be valid client
                                  '-s', ip,
                                  '-t', str(timeout),  # Timeout in seconds
                                  ],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            p.wait()

            stdout = p.stdout.read()
            stderr = p.stderr.read()

            if p.returncode != 0:
                return Event.DOWN, repr(stderr.strip())
        except IOError, msg:
            return Event.DOWN, 'Could not run dhcping: %s' % msg

        return Event.UP, 'OK'
