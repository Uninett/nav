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

#
# These functions should be moved to some library so
# other checkers can use them.
#
import sys
import stat

def find_cmd(cmd):
    """Return full path to cmd (if found in $PATH and is executable),
    or None."""
    pathstr = os.environ['PATH']
    dirs = pathstr.split(':')

    for d in dirs:
        path = os.path.join(d, cmd)

        if not os.path.isfile(path):
            continue

        if not os.access(path, os.X_OK):
            continue
        
        return path

    return None

def is_setuid_root(path):
    """Return True if the file is owned by root and has
    the setuid bit set."""

    # Can't be setuid root if it's not there.
    if not os.path.isfile(path):
        return False

    s = os.stat(path)

    # Owned by root?
    if s.st_uid != 0:
        return False

    # Setuid bit set?
    if s.st_mode & stat.S_ISUID == 0:
        return False

    # Yay, passed all test!
    return True

class DhcpChecker(AbstractChecker):
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "dhcp", service, port=0, **kwargs)

    def execute(self):
        ip, port = self.getAddress()
        timeout = self.getTimeout()
        
        cmd = 'dhcping'

        path = find_cmd(cmd)
        if not path:
            return Event.DOWN, 'Command not found: %s ($PATH = %s)' % (cmd, os.environ['PATH'])

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
