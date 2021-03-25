#
# Copyright (C) 2018 Uninett AS
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


class Event(object):
    """
    Class representing a NAV Event
    """

    UP = 'UP'
    DOWN = 'DOWN'
    boxState = 'boxState'
    serviceState = 'serviceState'

    def __init__(
        self,
        serviceid,
        netboxid,
        deviceid,
        eventtype,
        source,
        status,
        info='',
        version='',
    ):
        self.serviceid = serviceid
        self.netboxid = netboxid
        self.deviceid = deviceid
        self.info = info
        self.eventtype = eventtype
        self.status = status
        self.version = version
        self.source = source

    def __repr__(self):
        return "Service: %s, netbox: %s, eventtype: %s, status: %s" % (
            self.serviceid,
            self.netboxid,
            self.eventtype,
            self.status,
        )
