# -*- coding: UTF-8 -*-
# $Id$
#
# Copyright 2003 Norwegian University of Science and Technology
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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#
"""
Custom forgetSQL classes for Device Management
"""

### Imports

from nav.db.manage import *

### Classes

class DeviceDt(Device):
    def getNetbox(self):
        where = ["deviceid=%s" % (self._getID()[0],)]
        netbox = Netbox.getAll(where)
        if len(netbox):
            return netbox[0]
        else:
            return False

    def getModule(self):
        where = ["deviceid=%s" % (self._getID()[0],)]
        module = Module.getAll(where)
        if len(module):
            return module[0]
        else:
            return False

class AlerthistDt(Alerthist):
    _userClasses = {'device': DeviceDt, 'eventtype': Eventtype}

    def getVar(self, var, state=None):
        if state:
            where = ["alerthistid=%d" % (self._getID()[0]),
                     "var='%s'" % (var,),
                     "state='%s'" % (state,)]
        else:
             where = ["alerthistid=%d" % (self._getID()[0]),
                      "var='%s'" % (var,)]

        valList = AlerthistvarDt.getAll(where)
        if valList:
            return valList[0].val
        else:
            return None

class AlerthistvarDt(Alerthistvar):
    # nav.db.manage is missing _sqlPrimary for Alerthistvar
    _sqlPrimary = tuple(Alerthistvar._sqlFields.keys())
