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

from django.utils import six


class Netbox(object):
    """
    Class representing a NAV netbox
    """
    def __init__(self, netboxid, sysname, ip, up):
        self.netboxid = netboxid
        self.sysname = sysname
        self.ip = ip
        self.up = up

    def __eq__(self, obj):
        if isinstance(obj, six.string_types):
            return self.ip == obj
        return self.netboxid == obj.netboxid

    def __repr__(self):
        return "%s (%s)" % (self.sysname, self.ip)

    def __str__(self):
        return "%s (%s)" % (self.sysname, self.ip)

    def __hash__(self):
        return self.ip.__hash__()
