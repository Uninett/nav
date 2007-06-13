# -*- coding: UTF-8 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
#
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#
"""
The DeviceEvent class of Device Management
"""

### Imports

import nav.db

### Classes

class DeviceEvent:
    STATE_NONE = 'x'
    STATE_START = 's'
    STATE_END = 'e'

    source = 'deviceTracker'
    target = 'eventEngine'
    severity = 0

    deviceid = None
    netboxid = None
    subid = None
    state = STATE_NONE
    start_time = None
    end_time = None

    # String containing list of all vars
    allvars = ''

    def __init__(self,eventtypeid,alerttype=None):
        self.eventtypeid = eventtypeid
        self.alerttype = alerttype

        # Output vars
        self.vars = {}
        # Input vars
        self.startVars = {}
        self.endVars = {}
        self.statelessVars = {}

        # set alerttype var
        if self.alerttype:
            self.addVar("alerttype",self.alerttype)

    def post(self):
        connection = nav.db.getConnection('devicemanagement','manage')
        database = connection.cursor()

        # Set id's
        if not self.deviceid:
            self.deviceid = 'NULL'
        if not self.netboxid:
            self.netboxid = 'NULL'
        if not self.subid:
            self.subid = 'NULL'

        # post event to eventq
        sql = "INSERT INTO eventq (source,target,deviceid,netboxid,subid," +\
              "eventtypeid,state,severity) VALUES " +\
              "('%s','%s', %s, %s, %s, '%s', '%s' ,%s)" %\
        (self.source,self.target,str(self.deviceid),str(self.netboxid),\
        str(self.subid),self.eventtypeid, self.state, self.severity)
        database.execute(sql)
        connection.commit()

        # get the new eventqid
        sql = "SELECT currval('eventq_eventqid_seq')"
        database.execute(sql)
        connection.commit()
        eventqid = int(database.fetchone()[0])

        # post eventvars to eventqvar
        for varName,value in self.vars.items():
            sql = "INSERT INTO eventqvar (eventqid,var,val) VALUES " +\
            "(%s,'%s','%s')" %\
            (eventqid,varName,value)
            database.execute(sql)
        connection.commit()

    def addVar(self, key, value, state=None):
        if state == self.STATE_NONE:
            vars = self.statelessVars
        elif state == self.STATE_START:
            vars = self.startVars
        elif state == self.STATE_END:
            vars = self.endVars
        else:
            vars = self.vars
        vars[key] = value

        self.allvars = self.allvars + ' [' + key + '=' + value + '] '

    def addVars(self, values, state=None):
        if state == self.STATE_NONE:
            vars = self.statelessVars
        elif state == self.STATE_START:
            vars = self.startVars
        elif state == self.STATE_END:
            vars = self.endVars
        else:
            vars = self.vars
        for key,value in values.items():
            vars[key] = value
            self.allvars = self.allvars + ' [' + key + '=' + value + '] '

    def getVar(self, key, state):
        if state == self.STATE_NONE:
            vars = self.statelessVars
        elif state == self.STATE_START:
            vars = self.startVars
        elif state == self.STATE_END:
            vars = self.endVars
        if vars.has_key(key):
            value = vars[key]
        else:
            value = ''
        return value
