#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Stubs for use in Netmap"""


class Netbox(object):
    """Netbox stub"""

    id = None  # we need this, but it should always be empty

    def __str__(self):
        return str(self.sysname)

    def __unicode__(self):
        return '%s' % self.sysname

    def __repr__(self):
        return "<stubs.Netbox: %r>" % vars(self)

    def __key(self):
        return self.sysname

    def __eq__(self, value):
        return self.sysname == getattr(value, "sysname", None)

    def __hash__(self):
        return hash(self.__key())

    @classmethod
    def get_absolute_url(cls):
        return None


class GwPortPrefix(object):
    """Gwport stub"""

    def __init__(self):
        self.virtual = None

    def __str__(self):
        return str(self.gw_ip)

    def __unicode__(self):
        return '%s' % self.gw_ip

    def __key(self):
        return self.gw_ip, self.interface

    def __eq__(self, i):
        return self.__key() == i.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        return "<stubs.GwPortPrefix: %r>" % vars(self)


class Interface(object):
    """Interface stub"""

    def __str__(self):
        return "{0} ({1})".format(str(self.ifname), str(self.netbox))

    def __unicode__(self):
        return '%s' % self.ifname, self.netbox

    def __key(self):
        return self.netbox, self.ifname

    def __eq__(self, i):
        return self.__key() == i.__key()

    def __hash__(self):
        return hash(self.__key())

    @classmethod
    def get_absolute_url(cls):
        return None
