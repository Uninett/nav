# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# $Id$
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
import os

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
        command = "/usr/local/samba/bin/rpcclient -U %% -c 'lookupnames %s' %s  2>/dev/null" % (username, ip)
        result = os.popen(command).readlines()
        if not result:
            return Event.UP, "Failed to check service"
        result = result[-1]
        if result.split(" ")[0] == username:
            return Event.UP, 'Ok'
        else:
            return Event.DOWN, result


def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = ['username']
    return requiredArgs
