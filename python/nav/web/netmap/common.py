# -*- coding: UTF-8 -*-
#
# Copyright 2007 UNINETT AS
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
# Authors: Kristian Klette <klette@samfundet.no>

import sys

class unbuffered:
    """Utility class for writing to stderr easily"""
    def write(self, data):
        sys.stderr.write(data)
        sys.stderr.write("\n")
        sys.stderr.flush()

class Connection:
    """Class to represent a link between two netboxes"""
    def __init__(self, from_netboxid = None, to_netboxid = None,
                 capacity = None, load = (0, 0)):
        self.from_netboxid = from_netboxid
        self.to_netboxid = to_netboxid
        self.capacity = capacity
        self.load = load

class Netbox:
    """Class to represent a netbox. Contains all the info about the netbox"""

    def __init__(self, netboxid = None, sysname = "Unknown", ip = "Unknown",
                       category = None, room = "unknown", location = "unknown",
                       up = None, connections = None):
        self.netboxid = netboxid
        self.sysname = sysname
        self.ip = ip
        self.category = category
        self.room = room
        self.location = location
        self.up = up
        if not connections:
            self.connections = []
        else:
            self.connections = connections

    def __str__(self):
        return "%s: %s (%s) -> %s" % (self.netboxid, self.sysname, self.ip, str(self.connections))

