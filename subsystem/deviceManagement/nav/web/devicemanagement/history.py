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
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no
#
"""
History page with helper classes of Device Management
"""

### Imports

import forgetSQL
import mx.DateTime
import re

import nav.db.manage
from nav.web import urlbuilder
from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate

from nav.web.devicemanagement.constants import *
from nav.web.devicemanagement.common import *
from nav.web.devicemanagement import db as dtTables
from nav.web.devicemanagement.deviceevent import DeviceEvent
from nav.web.devicemanagement.page import Page
from nav.web.devicemanagement.widget import Widget

### Functions

def history(req,deviceorderid=None):
    page = Page()
    form = req.form

    page.name = 'history'
    page.title = 'Device history'
    page.description = 'Select and view device history for a location, ' + \
                       'room, box or module. Use quicksearch to search for '+\
                       'a (partial) serialnumber, hostname, IP or room.'
    page.widgets = {}

    if (form.has_key('startday') and form['startday'].isdigit()
        and form.has_key('startmonth') and form['startmonth'].isdigit()
        and form.has_key('startyear')) and form['startyear'].isdigit():
        startdate_value = [form['startyear'],
                           form['startmonth'],
                           form['startday']]
        startTime = mx.DateTime.Date(int(form['startyear']),
                                     int(form['startmonth']),
                                     int(form['startday']))
    else:
        startdate_value = [None, None, None]
        startTime = None

    if (form.has_key('endday') and form['endday'].isdigit()
        and form.has_key('endmonth') and form['endmonth'].isdigit()
        and form.has_key('endyear')) and form['endyear'].isdigit():
        enddate_value = [form['endyear'],
                         form['endmonth'],
                         form['endday']]
        endTime = mx.DateTime.Date(int(form['endyear']),
                                   int(form['endmonth']),
                                   int(form['endday']),
                                   23, 59, 59)
    else:
        enddate_value = [None, None, None]
        endTime = None

    page.widgets['tf_startdate'] = Widget(['startday', 'startmonth', 'startyear'],
                                       'date',
                                       'Start date',
                                       startdate_value)
    page.widgets['tf_enddate'] = Widget(['endday', 'endmonth', 'endyear'],
                                       'date',
                                       'End date',
                                       enddate_value)
    page.widgets['tf_submit'] = Widget('history', 'submit', 'Search')

    # Add data from treeselect to hidden fields in the time frame form
    page.timeframeform = {}

    if form.has_key('location'):
        page.timeframeform['location'] = form['location']
    else:
        page.timeframeform['location'] = ''

    if form.has_key('room'):
        page.timeframeform['room'] = form['room']
    else:
        page.timeframeform['room'] = ''

    if form.has_key('box'):
        page.timeframeform['box'] = form['box']
    else:
        page.timeframeform['box'] = ''

    if form.has_key('module'):
        page.timeframeform['module'] = form['module']
    else:
        page.timeframeform['module'] = ''

    submenu = [('Browse devices','Browse or search for devices',
                BASEPATH),
               ('Show active devices','Show all devices in operation',
                BASEPATH),
               ('Show devices with registered errors',
                'Show all devices with registered errors',
                BASEPATH)]
    if deviceorderid:
        submenu.append(('Order history','Go back to order history',
                        BASEPATH+'order/history'))
    page.submenu = submenu

    # Set menu
    page.menu = makeMainMenu(selected=0)

    page.action = ''
    page.subname = ''

    showHistory = False
    if form.has_key('history'):
        # History mode
        historyType = None
        if form.has_key(CN_MODULE):
            historyType = CN_MODULE
        elif form.has_key(CN_BOX):
            historyType = CN_BOX
        elif form.has_key(CN_ROOM):
            historyType = CN_ROOM
        elif form.has_key(CN_LOCATION):
            historyType = CN_LOCATION
        elif form.has_key(CN_DEVICE):
            historyType = CN_DEVICE
        if historyType:
            showHistory = True
            unitList = form[historyType]
            if not type(unitList) is list:
                unitList = [unitList]
            page.boxList = makeHistory(form, historyType, unitList, startTime, endTime)
            page.searchbox = None
            page.subname = 'history'
        else:
            page.errors.append('No unit selected')
    elif deviceorderid:
        sql = "SELECT deviceid FROM device WHERE " +\
              "deviceorderid='%s'" % (deviceorderid,)
        result = executeSQL(sql,fetch=True)
        if result:
            historyType = CN_DEVICE
            unitList = []
            for row in result:
                unitList.append(row[0])
            page.boxList = makeHistory(form, historyType, unitList, startTime, endTime)
            page.searchbox = None
            page.subname = 'history'
        else:
            page.errors.append('Could not find any devices for this order')

    if not showHistory:
        # Browse mode, make treeselect
        page.searchbox,page.treeselect = makeTreeSelect(req,serialSearch=True)
        page.formname = page.treeselect.formName

        #validSubmit = False
        #if form.has_key(CN_LOCATION):
        #    # If a location has been selected, allow submit
        #    validSubmit = True

        page.submit = {'control': 'history',
                       'value': 'View history',
                       'enabled': True}

    nameSpace = {'page': page}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = CURRENT_PATH
    return template.respond()

def makeHistory(form, historyType, unitList, startTime, endTime):
    boxList = []

    for unitid in unitList:
        if historyType == CN_MODULE:
            boxList.append(ModuleHistoryBox(unitid, startTime, endTime))
        elif historyType == CN_BOX:
            boxList.append(NetboxHistoryBox(unitid, startTime, endTime))
        elif historyType == CN_ROOM:
            boxList.append(RoomHistoryBox(unitid, startTime, endTime))
        elif historyType == CN_LOCATION:
            boxList.append(LocationHistoryBox(unitid, startTime, endTime))
        elif historyType == CN_DEVICE:
            where = "deviceid='%s'" % (unitid,)
            box = nav.db.manage.Netbox.getAll(where=where)
            module = nav.db.manage.Module.getAll(where=where)
            if box:
                box = box[0]
                boxList.append(NetboxHistoryBox(box.netboxid, startTime, endTime))
            elif module:
                module = module[0]
                boxList.append(ModuleHistoryBox(module.moduleid, startTime, endTime))
            else:
                boxList.append(DeviceHistoryBox(unitid, startTime, endTime))
    return boxList

### Classes

class HistoryBox:
    # Format string tokens

    tokenVars = {DN_E_USERNAME: ['username',DeviceEvent.STATE_NONE],
                 DN_E_COMMENT: ['comment',DeviceEvent.STATE_NONE],
                 DN_E_UNITTYPE: ['unittype',DeviceEvent.STATE_NONE],
                 DN_E_LOCATIONID: ['locationid',DeviceEvent.STATE_NONE],
                 DN_E_ROOMID: ['roomid',DeviceEvent.STATE_NONE]}

    globalVars = {G_EVENTTYPE: 'eventtypeid',
                  G_ALERTTYPE: 'alerttype',
                  G_ALLVARS: 'allvars'}


    headings = [('Start',''),
                ('End',''),
                ('Description','')]

    def fill(self):
        self.rows = []
        formatData = {}

        if self.events:
           for event in self.events:
                # Default description formatting (used if no format
                # string is returned by getFormatting()
                default = [G_EVENTTYPE + ", " +\
                           G_ALERTTYPE + ", " + G_ALLVARS]

                formatString = self.getFormatting(event)
                if not formatString:
                    formatString = default

                startTime = event.start_time.strftime(TIMEFORMAT)
                endTime = None
                if event.end_time:
                    endTime = event.end_time.strftime(TIMEFORMAT)

                descr = self.format(formatString,event)

                self.rows.append([[startTime],[endTime],descr])

    def format(self,formatList,event):
        formattedList = []
        for formatString in formatList:
            #if type(formatString) == type(mx.DateTime.now()):
            #    formatString = formatString.strftime(TIMEFORMAT)
            #elif not type(formatString) is str:
            #    formatString = str(formatString)

            regexp = re.compile("\$(\w+)\$")

            while regexp.search(formatString):
                match = regexp.search(formatString).groups()[0]

                match = '$' + match + '$'
                var = self.tokenVars[match][0]
                state = self.tokenVars[match][1]
                data = event.getVar(var,state)

                formatString = formatString.replace(match,data)

            # Globals
            regexp = re.compile("\%(\w+)\%")
            while regexp.search(formatString):
                match = regexp.search(formatString).groups()[0]

                match = '%' + match + '%'
                data = getattr(event,self.globalVars[match])

                formatString = formatString.replace(match,str(data))
            formattedList.append(formatString) 
        return formattedList

class LocationHistoryBox(HistoryBox):
    def __init__(self, locationid, startTime, endTime):
        loc = nav.db.manage.Location(locationid)
        self.title = loc.descr

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime)
        vars = [['locationid',locationid]]
        self.events = ec.getEventsByVar(vars)
        self.fill()

    def getFormatting(self,event):
        formatString = None
        if event.eventtypeid == 'deviceActive':
            # deviceAcrive events doesn't have locationid, so
            # there is no need to provide formatting
            pass
        elif event.eventtypeid == 'deviceState':
            pass
        elif event.eventtypeid == 'deviceNotice':
            if event.alerttype == 'deviceError':
                unitType = event.getVar('unittype',
                                        DeviceEvent.STATE_NONE)
        return formatString

class RoomHistoryBox(HistoryBox):
    def __init__(self, roomid, startTime, endTime):
        room = nav.db.manage.Room(roomid)
        self.title = str(roomid) + ' (' + room.descr + ')'

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime)
        vars = [['roomid',roomid]]
        self.events = ec.getEventsByVar(vars)
        self.fill()

    def getFormatting(self,event):
        formatString = None
        if event.eventtypeid == 'deviceActive':
            # deviceAcrive events doesn't have locationid, so
            # there is no need to provide formatting
            pass
        elif event.eventtypeid == 'deviceState':
            pass
        elif event.eventtypeid == 'deviceNotice':
            if event.alerttype == 'deviceError':
                unitType = event.getVar('unittype',
                                        DeviceEvent.STATE_NONE)
        return formatString

class NetboxHistoryBox(HistoryBox):
    def __init__(self, netboxid, startTime, endTime):
        box = nav.db.manage.Netbox(netboxid)
        self.title = box.sysname

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime)
        try:
            deviceid = nav.db.manage.Netbox(netboxid).device.deviceid
        except forgetSQL.NotFound:
            deviceid = None
        if deviceid:
            self.events = ec.getEventsByDeviceid([deviceid])
        else:
            self.events = None
        self.fill()

    def getFormatting(self,event):
        formatString = None
        if event.eventtypeid == 'deviceActive':
            # deviceAcrive events doesn't have locationid, so
            # there is no need to provide formatting
            pass
        elif event.eventtypeid == 'deviceState':
            pass
        elif event.eventtypeid == 'deviceNotice':
            if event.alerttype == 'deviceError':
                unitType = event.getVar('unittype',
                                        DeviceEvent.STATE_NONE)
        return formatString


class ModuleHistoryBox(HistoryBox):
    def __init__(self, moduleid, startTime, endTime):
        module = nav.db.manage.Module(moduleid)

        self.title = 'Module ' + str(module.module) + ' in ' + \
                      module.netbox.sysname

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime)
        try:
            deviceid = nav.db.manage.Module(moduleid).device.deviceid
        except forgetSQL.NotFound:
            deviceid = None
        if deviceid:
            self.events = ec.getEventsByDeviceid([deviceid])
        else:
            self.events = None
        self.fill()

    def getFormatting(self,event):
        formatString = None
        if event.eventtypeid == 'deviceActive':
            # deviceAcrive events doesn't have locationid, so
            # there is no need to provide formatting
            pass
        elif event.eventtypeid == 'deviceState':
            pass
        elif event.eventtypeid == 'deviceNotice':
            if event.alerttype == 'deviceError':
                unitType = event.getVar('unittype',
                                        DeviceEvent.STATE_NONE)

        return formatString

class DeviceHistoryBox(HistoryBox):
    def __init__(self, deviceid, startTime, endTime):
        device = nav.db.manage.Device(deviceid)
        self.title = 'Device not currently in operation (%s)' % (device.serial,)

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime)
        self.events = ec.getEventsByDeviceid([deviceid])
        self.fill()

    def getFormatting(self,event):
        formatString = None
        if event.eventtypeid == 'deviceActive':
            # deviceAcrive events doesn't have locationid, so
            # there is no need to provide formatting
            pass
        elif event.eventtypeid == 'deviceState':
            pass
        elif event.eventtypeid == 'deviceNotice':
            if event.alerttype == 'deviceError':
                unitType = event.getVar('unittype',
                                        DeviceEvent.STATE_NONE)
        return formatString

class History:
    """
    The interpreted history for a device (netbox or module)
    """

    url = None
    sysname = None

    def __init__(self,deviceId,netboxId=None,moduleId=None):
        self.deviceId = deviceId
        self.netboxId = netboxId
        self.moduleId = moduleId
        self.events = []
        self.moduleevents = []
        self.error = None
        self.getHistory()

        if self.netboxId:
            self.url = urlbuilder.createUrl(id=netboxId,division='netbox')
            self.sysname = dtTables.Netbox(netboxId).sysname
        if self.moduleId:
            module = dtTables.Module(moduleId)
            self.module = module.module
            self.sysname = module.netbox.sysname
            self.url = urlbuilder.createUrl(id=module.netbox.netboxid,
            division='netbox')

    def addEvent(self,sort_key, e, modulehist=False):
        if not modulehist:
            self.events.append((sort_key,e))
        else:
            self.moduleevents.append((sort_key,e))

    def getHistory(self):
        # This should be replaced by urlbuilder stuff:
        HISTORYPATH = BASEPATH + 'history/device/'
        if self.deviceId:
            # Display the history for a device

            where = ["deviceid=%s" % (self.deviceId,),"""eventtypeid='deviceOrdered' or eventtypeid='deviceRegistered' or eventtypeid='deviceInOperation' or eventtypeid='deviceError' or eventtypeid='deviceSwUpgrade' or eventtypeid='deviceHwUpgrade' or eventtypeid='deviceRma'"""]
            events = dtTables.AlerthistDt.getAll(where)

            try:
                # Try to load this device from the db, if it doesnt exist this will
                # fail and raise a forgetSQL.NotFound exception
                device = dtTables.DeviceDt(self.deviceId)
                device.load()
                self.netbox = device.getNetbox()

                for de in events:
                    # de.state can only be trusted on events that send
                    # vars with start and end events. fix this by looking
                    # for end_time equal or not equal to INFINITY

                    eventtype = de.eventtype.eventtypeid

                    if eventtype == 'deviceOrdered' and de.end_time == INFINITY:
                        # A deviceOrdered start event
                        e = {'eventType': 'Ordered',
                             'time': de.start_time.strftime(DATEFORMAT),
                             'descr': 'Ordered by %s for %s from %s' %
                             (de.vars['username'],de.vars['orgid'],
                             de.vars['retailer'])}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceOrdered' and de.end_time != INFINITY:
                        # A deviceOrdered end event
                        # start
                        e = {'eventType': 'Ordered',
                             'time': de.start_time.strftime(DATEFORMAT),
                             'descr': 'Ordered by %s for %s from %s' %
                             (de.getVar('username','s'),de.getVar('orgid','s'),
                             de.getVar('retailer','s'))}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                        # end
                        e = {'eventType': 'Arrived',
                             'time': de.end_time.strftime(DATEFORMAT),
                             'descr': 'Registered with serialnumber "%s" by %s'\
                             % (de.device.serial,de.getVar('username','e'))}
                        sort_key = de.end_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceRegistered':
                        # A deviceRegistered event
                        e = {'eventType': 'Registered',
                             'time': de.start_time.strftime(DATEFORMAT),
                             'descr': 'Registered with serialnumber "%s" by %s'\
                             % (de.device.serial,de.getVar('username'))}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceError':
                        # A deviceError event
                        e = {'eventType': 'Error',
                             'time': de.start_time.strftime(TIMEFORMAT),
                             'descr': de.getVar('comment')}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceInOperation' and \
                    de.end_time == INFINITY:
                        # A deviceInOperation event (still in operation)
                        if de.netbox:
                            sysname = de.getVar('sysname','s')
                            descr = 'Device in operation as netbox %s' % sysname
                        if de.subid:
                            module = de.getVar('module','s')
                            descr = 'Device in operation as module %s in \
                            netbox %s' % (module,sysname)
                        e = {'eventType': 'In operation',
                             'time': de.start_time.strftime(TIMEFORMAT),
                             'descr': descr}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceInOperation' and \
                    de.end_time != INFINITY:
                        # A deviceInOperation event (finished)
                        # the start event
                        if de.netbox:
                            sysname = de.getVar('sysname','s')
                            descr = 'Device in operation as netbox %s' % sysname
                        if de.subid:
                            module = de.getVar('module','s')
                            descr = 'Device in operation as module %s in \
                            netbox %s' % (module,sysname)
                        e = {'eventType': 'In operation',
                             'time': de.start_time.strftime(TIMEFORMAT),
                             'descr': descr}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                        # the end event
                        if de.netbox:  
                            sysname = de.getVar('sysname','s')
                            descr = 'Device out of operation as netbox %s' % (sysname,)
                        if de.subid:
                            module = de.getVar('module','s')
                            descr = 'Device out of operation as module %s in \
                            netbox %s' % (module,sysname)
                        e = {'eventType': 'Out of operation',
                             'time': de.end_time.strftime(TIMEFORMAT),
                             'descr': descr}
                        sort_key = de.end_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceSwUpgrade':
                        # A deviceSwUpgrade event
                        e = {'eventType': 'Software upgrade',
                             'time': de.start_time.strftime(TIMEFORMAT),
                             'descr': 'Upgraded from %s to %s' %
                             (de.getVar('oldversion'),de.getVar('newversion'))}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceHwUpgrade':
                        # A devicHwUpgrade event
                        e = {'eventType': 'Hardware upgrade',
                             'time': de.start_time.strftime(TIMEFORMAT),
                             'descr': '%s' %
                             (de.getVar('description'),)}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceRma' and de.end_time == INFINITY:
                        # A deviceRma start event
                        e = {'eventType': 'RMA registered',
                             'time': de.start_time.strftime(TIMEFORMAT),
                             'descr': 'Registered by %s with comment "%s"' %
                             (de.getVar('username','s'),de.getVar('comment','s'),)}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceRma' and de.end_time != INFINITY:
                        # A deviceRma end event
                        e = {'eventType': 'RMA registered',
                             'time': de.start_time.strftime(TIMEFORMAT),
                             'descr': 'Registered by %s with comment "%s"' %
                             (de.getVar('username','s'),de.getVar('comment','s'),)}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                       # end of event
                        e = {'eventType': 'RMA returned',
                             'time': de.end_time.strftime(TIMEFORMAT),
                             'descr': 'Registered returned by %s' %
                             (de.getVar('username','e'),)}
                        sort_key = de.end_time
                        self.addEvent(sort_key,e)
                    else:
                        # Unknown event
                        if de.end_time == INFINITY:
                            end_time = 'infinity'
                        elif de.end_time:
                            end_time = de.end_time.strftime(TIMEFORMAT)
                        else:
                            end_time = ''
                        e = {'eventType': eventtype,
                             'time': de.start_time.strftime(TIMEFORMAT) \
                             + ' - ' + end_time,
                             'descr': 'Unknown event'}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                self.events.sort()

                # If this device is a netbox, make the module history for it
                if self.netbox:
                    where = ["netboxid=%s" % (self.netbox.netboxid,),"eventtypeid='deviceInOperation'"]
                    events = dtTables.AlerthistDt.getAll(where)

                    for de in events:
                        if de.subid:
                            # This is a deviceInOperation event for a module
                            if de.end_time == INFINITY:
                            # A deviceInOperation event (still in operation)
                                if de.subid:
                                    module = de.getVar('module','s')
                                    descr = 'Module <a href="%s%s">%s</a> added to \
                                    netbox %s' % (HISTORYPATH,de.device.deviceid,module,sysname)
                                    e = {'eventType': 'In operation',
                                        'time': de.start_time.strftime(TIMEFORMAT),
                                        'descr': descr}
                                    sort_key = de.start_time
                                    self.addEvent(sort_key,e,True)
                            if de.end_time != INFINITY:
                                # A deviceInOperation event (finished)
                                # the start event
                                if de.subid:
                                    module = de.getVar('module','s')
                                    descr = 'Module <a href="%s%s">%s</a> added to \
                                    netbox %s' % (HISTORYPATH,de.device.deviceid,module,sysname)
                                    e = {'eventType': 'In operation',
                                         'time': de.start_time.strftime(TIMEFORMAT),
                                         'descr': descr}
                                    sort_key = de.start_time
                                    self.addEvent(sort_key,e,True)
                                # the end event
                                if de.subid:
                                    module = de.getVar('module','s')
                                    descr = 'Module <a href="%s%s">%s</a> removed from \
                                    netbox %s' % (HISTORYPATH,de.device.deviceid,module,sysname)
                                    e = {'eventType': 'Out of operation',
                                         'time': de.end_time.strftime(TIMEFORMAT),
                                         'descr': descr}
                                    sort_key = de.end_time
                                    self.addEvent(sort_key,e,True)
                    self.moduleevents.sort()

                if not (self.events or self.moduleevents):
                    self.error = 'No history registered for this device'

            except forgetSQL.NotFound,e:
                self.error = 'No device with deviceid ' + str(self.deviceId)

class EventCollector:
    def __init__(self,eventtypes=[],alerttypes=[],limit=None,offset=None,
                 orderBy=None,startTime=None,endTime=None):

        self.eventtypes = eventtypes
        self.alerttypes = alerttypes
        self.limit = limit
        self.offset = offset
        self.orderBy = orderBy
        self.startTime = startTime
        self.endTime = endTime

    def getEventsByVar(self,vars):
        # vars: list of [var,value]

        # SQL for list of alerthistids
        sql = "SELECT DISTINCT alerthist.alerthistid FROM " +\
              "alerthist,alerthistvar WHERE " +\
              "alerthist.alerthistid=alerthistvar.alerthistid AND "

        first = True
        for var,val in vars:
            if not first:
                sql += "AND "
            sql += "(alerthistvar.var='%s' AND alerthistvar.val='%s') " % \
                   (var,val)
            first = False
        return self.getEvents(idsql=sql)

    def getEventsByDeviceid(self,deviceids):
        # deviceids: list of deviceids

        sql = "("

        first = True
        for id in deviceids:
            if not first:
                sql += "OR "
            sql += "alerthist.deviceid='%s' " % (id,)
            first = False
        sql += ") "
        return self.getEvents(where=sql)

    def getEvents(self,idsql=None,where=None):
        # idsql: sql that selects list of alerthist ids
        # where: where clause to add

        # Constants
        ALERTHISTID = 0
        SOURCE = 1
        DEVICEID = 2
        NETBOXID = 3
        SUBID = 4
        START_TIME = 5
        END_TIME = 6
        EVENTTYPEID = 7
        VALUE = 8
        SEVERITY = 9
        ALERTTYPEID = 10
        ALERTTYPE = 11

        sql = "SELECT alerthist.alerthistid,alerthist.source," +\
              "alerthist.deviceid,alerthist.netboxid,alerthist.subid," +\
              "alerthist.start_time,alerthist.end_time," +\
              "alerthist.eventtypeid,alerthist.value,alerthist.severity," +\
              "alerthist.alerttypeid,alerttype.alerttype FROM alerthist " +\
              "LEFT JOIN alerttype using (alerttypeid) "

        addedWhere = False

        # Limit on select of alerthistids
        if idsql:
            if not addedWhere:
                sql += "WHERE "
                addedWhere = True
            else:
                sql += "AND "
            sql += "alerthist.alerthistid IN (%s) " % (idsql,)

        # Add where
        if where:
            if not addedWhere:
                sql += "WHERE "
                addedWhere = True
            else:
                sql += "AND "
            sql += where + " "

        # Limit on eventtypes
        if self.eventtypes:
            if not addedWhere:
                sql += "WHERE "
                addedWhere = True
            else:
                sql += "AND "
            first = True
            sql += "("
            for eventtype in self.eventtypes:
                if not first:
                    sql += "OR "
                sql += "alerthist.eventtype='%s' " % (eventtype,)
                first = False
            sql += ") "

        # Limit on alerttypes
        if self.alerttypes:
            if not addedWhere:
                sql += "WHERE "
                addedWhere = True
            else:
                sql += "AND "
            first = True
            sql += "("
            for alerttype in self.alerttypes:
                if not first:
                    sql += "OR "
                # Get alerttypeid
                atidsql = "(SELECT alerttypeid FROM alerttype WHERE " +\
                          "alerttype='%s')" % (alerttype,)

                sql += "alerthist.alerthistid='%s'" % (atidsql,)
                first = False
            sql += ") "

        # Limit on time interval
        if self.startTime and self.endTime:
            if not addedWhere:
                sql += "WHERE "
                addedWhere = True
            else:
                sql += "AND "
            # Get all events with event start < interval end, and event end >
            # interval start. In the case of a stateless event (end = NULL),
            # also check that event start > interval start.
            sql += """(alerthist.start_time <= '%(end)s')
                      AND (alerthist.end_time >= '%(start)s'
                           OR (alerthist.end_time IS NULL
                               AND alerthist.start_time >= '%(start)s')) """ % \
                   {'start': self.startTime.strftime('%Y-%m-%d'),
                    'end': self.endTime.strftime('%Y-%m-%d')}

        # Add order by
        if self.orderBy:
            sql += "ORDER BY %s " % (self.orderBy,)

        # Add limit
        if self.limit:
            sql += "LIMIT %s " % (self.limit,) 

        # Add offset
        if self.offset:
            sql += "OFFSET %s " % (self.limit,) 

        connection = nav.db.getConnection('devicemanagement','manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall() 

        events = []
        if result:
            for row in result:
                event = DeviceEvent(row[EVENTTYPEID],
                                    row[ALERTTYPE])
                event.alerthistid = row[ALERTHISTID]
                event.source = row[SOURCE]
                event.deviceid = row[DEVICEID]
                event.netboxid = row[NETBOXID]
                event.subid = row[SUBID]
                event.start_time = row[START_TIME]
                event.end_time = row[END_TIME]
                event.value = row[VALUE]
                event.severity = row[SEVERITY]

                # get alerthistvars
                sql = "SELECT state,var,val FROM alerthistvar WHERE " +\
                      "alerthistid='%s'" % (event.alerthistid,)
                database.execute(sql)
                vars = database.fetchall() 
                if vars:
                    for var in vars:
                        event.addVar(var[1],var[2],var[0])
                events.append(event)
        return events
