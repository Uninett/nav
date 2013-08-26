#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Stubs for use in Netmap"""

#Ignore too few public methods, these are stubs.
# pylint: disable=R0903

class Netbox(object):
    """Netbox stub"""
    def __str__(self):
        return str(self.sysname)

    def __unicode__(self):
        return u'%s' % self.sysname

    def __key(self):
        return (self.sysname)

    # Yes we know we access private variable
    # pylint: disable=W0212
    def __eq__(self, i):
        return self.__key() == i.__key()

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
        return u'%s' % self.gw_ip

    def __key(self):
        return (self.gw_ip)

    # Yes we know we access private variable
    # pylint: disable=W0212
    def __eq__(self, i):
        return self.__key() == i.__key()

    def __hash__(self):
        return hash(self.__key())

class Interface(object):
    """Interface stub"""
    def __str__(self):
        return "{0} ({1})".format(
            str(self.ifname),
            str(self.netbox)
        )

    def __unicode__(self):
        return u'%s' % self.ifname, self.netbox

    def __key(self):
        return (self.ifname)

    # Yes we know we access private variable
    # pylint: disable=W0212
    def __eq__(self, i):
        return self.__key() == i.__key()

    def __hash__(self):
        return hash(self.__key())

    @classmethod
    def get_absolute_url(cls):
        return None


