"""
$Id$

This file is part of the NAV project.
This module contains custom forgetSQL classes used by
the deviceTracker.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
"""


from nav.db.manage import *

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
