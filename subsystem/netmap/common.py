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


class Netbox:
    def __init__(self, netboxid, ip, sysname, catid, prefixid, up, uptime, roomid):
        self.netboxid = netboxid
        self.ip = ip
        self.sysname = sysname
        self.catid = catid
        self.prefixid = prefixid
        self.up = up
        self.uptime = uptime
        self.roomid = roomid

        self.modules = {}
        self.is_linked = True

class Module:
    def __init__(self, moduleid, desc):
        self.moduleid = moduleid
        self.desc = desc

        self.gwports = {}
        self.swports = {}

class GWPort:
    def __init__(self, gwportid, gwportip, link, interface, speed, connected_to = None, connected_swport = None):
        self.gwportid = gwportid
        self.gwportip = gwportip
        self.link = link
        self.interface = interface
        self.speed = speed
        self.connected_to = connected_to
        self.connected_swport = connected_swport

class SWPort:
    def __init__(self, swportid, port, link, interface, speed, connected_to = None, connected_swport = None):
        self.swportid = swportid
        self.port = port
        self.link = link
        self.interface = interface
        self.speed = speed
        self.connected_to = connected_to
        self.connected_swport = connected_swport
