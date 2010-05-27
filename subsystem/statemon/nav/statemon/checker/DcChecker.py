# -*- coding: utf-8 -*-
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

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
import os
import subprocess

class DcChecker(AbstractChecker):
    """
    Required argument:
    username
    """
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "dc", service, **kwargs)

    def execute(self):
        args = self.getArgs()
        username = args.get('username','')
        if not username:
            return Event.DOWN, "Missing required argument: username"

        ip, host = self.getAddress()

        try:
            p = subprocess.Popen(['rpcclient',
                                  '-U', '%',
                                  '-c', 'lookupnames '+username,
                                  ip],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            
            p.wait()
        except OSError, msg:
            return Event.DOWN, 'could not run rpcclient: %s' % msg

        if p.returncode != 0:
            errline = p.stdout.readline()
            return Event.DOWN, "rpcclient returned %s: %s" % (p.returncode, errline)

        output = p.stdout.readlines()
        lastline = output[-1]
        if lastline.split()[0] == username:
            return Event.UP, 'Ok'
        else:
            return Event.DOWN, lastline


def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = ['username']
    return requiredArgs
