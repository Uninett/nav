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
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Erik Gorset     <erikgors@itea.ntnu.no>
#
"""
Module representing a NAV service
"""
import string
class Service:
    def __init__(self, sysname, handler, args, id=''):
        self.sysname = sysname
        self.handler = handler
        self.args = args
        self.id = id
        self.active='t'
    def __cmp__(self, obj):
        return self.sysname==obj.sysname and \
               self.handler==obj.handler and self.args==obj.args
    def __eq__(self, obj):
        return self.sysname==obj.sysname and \
               self.handler==obj.handler and self.args==obj.args
    def __hash__(self):
        value = self.sysname.__hash__() + self.handler.__hash__() + \
                self.args.__str__().__hash__()
        value = value % 2**31
        return int(value)
    def __repr__(self):
        strargs = string.join(map(lambda x: x+'='+self.args[x], self.args))
        return "%-20s %-10s %s" % (self.sysname, self.handler, strargs)
