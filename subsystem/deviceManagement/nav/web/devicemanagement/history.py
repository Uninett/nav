# -*- coding: UTF-8 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2007-2008 UNINETT AS
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
#          Thomas Adamcik <thomas.adamcik@uninett.no>
#
"""
History page with helper classes of Device Management
"""

### Imports

import calendar
import forgetSQL
import mx.DateTime
import re

import nav.db
import nav.db.manage
from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate

from nav.web.devicemanagement.constants import *
from nav.web.devicemanagement.common import *
from nav.web.devicemanagement import db as dtTables
from nav.web.devicemanagement.deviceevent import DeviceEvent
from nav.web.devicemanagement.page import Page
from nav.web.devicemanagement.widget import Widget

from nav.web.quickselect import QuickSelect


quickselect_kwargs = {
    'button': 'View %s history',
    'module': True,
    'netbox_multiple': False,
    'module_multiple': False,
    'netbox_label': '%(sysname)s [%(ip)s - %(device__serial)s]',
}

DeviceQuickSelect = QuickSelect(**quickselect_kwargs)

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

    dbconn = nav.db.getConnection('devicemanagement', 'manage')
    db = dbconn.cursor()

    # Get year of first entry in alerthist
    date_options = {}
    sql = """
        SELECT min(start_time) IS NOT NULL AS exists, min(start_time)
        FROM alerthist
    """
    db.execute(sql)
    row = db.dictfetchall()[0]
    if row['exists']:
        date_options['startyear'] = row['min'].year

    # Get filter values for start time
    if (form.has_key('startday') and form['startday'].isdigit()
        and form.has_key('startmonth') and form['startmonth'].isdigit()
        and form.has_key('startyear') and form['startyear'].isdigit()):
        startyear = int(form['startyear'])
        startmonth = int(form['startmonth'])
        startday = int(form['startday'])
        startdaymax = calendar.monthrange(startyear, startmonth)[1]
        if startday > startdaymax:
            startday = startdaymax
        startdate_value = [str(startyear), str(startmonth), str(startday)]
        startTime = mx.DateTime.Date(startyear, startmonth, startday)
    else:
        weekago = mx.DateTime.now() - mx.DateTime.oneWeek
        startdate_value = [str(weekago.year),
                           str(weekago.month),
                           str(weekago.day)]
        startTime = weekago

    # endtime
    if (form.has_key('endday') and form['endday'].isdigit()
        and form.has_key('endmonth') and form['endmonth'].isdigit()
        and form.has_key('endyear') and form['endyear'].isdigit()):
        endyear = int(form['endyear'])
        endmonth = int(form['endmonth'])
        endday = int(form['endday'])
        enddaymax = calendar.monthrange(endyear, endmonth)[1]
        if endday > enddaymax:
            endday = enddaymax
        enddate_value = [str(endyear), str(endmonth), str(endday)]
        endTime = mx.DateTime.Date(endyear, endmonth, endday, 23, 59, 59)
    else:
        now = mx.DateTime.now()
        enddate_value = [str(now.year),
                         str(now.month),
                         str(now.day)]
        endTime = now

    # types
    if form.has_key('type') and form['type'] != 'All':
        type_value = form['type']
    else:
        type_value = 'All'
    if type_value.startswith('e_'):
        eventtype_filter = [type_value[2:]]
    else:
        eventtype_filter = []
    if type_value.startswith('a_'):
        alerttype_filter = [type_value[2:]]
    else:
        alerttype_filter = []

    type_options = {'options': [('opt', 'All', 'All', False)]}
    for eventtype in nav.db.manage.Eventtype.getAllIDs():
        if type_value.startswith('e_') and type_value.endswith(eventtype):
            selected = True
        else:
            selected = False
        optgroup = [('opt', 'e_%s' % eventtype, 'All %s' % eventtype, selected)]
        for alerttype in nav.db.manage.Alerttype.getAllIDs(
                            where="eventtypeid='%s'" % eventtype,
                            orderBy='alerttype'):
            if type_value.startswith('a_') and type_value.endswith(alerttype):
                selected = True
            else:
                selected = False
            optgroup.append(('opt', 'a_%s' % alerttype, alerttype, selected))
        type_options['options'].append(('grp', eventtype, eventtype, optgroup))

    # Create filter form widgets
    page.widgets['filter_startdate'] = Widget(['startday', 'startmonth', 'startyear'], 'date',
                                              name='Start date',
                                              value=startdate_value,
                                              options=date_options)
    page.widgets['filter_enddate'] = Widget(['endday', 'endmonth', 'endyear'], 'date',
                                            name='End date',
                                            value=enddate_value,
                                            options=date_options)
    page.widgets['filter_eventtype'] = Widget('type', 'selectoptgroup',
                                              name='Type',
                                              options=type_options)
    page.widgets['filter_submit'] = Widget('history', 'submit', 'Filter')

    submenu = []
    if deviceorderid:
        submenu.append(('Order history','Go back to order history',
                        BASEPATH+'order/history'))
    page.submenu = submenu

    # Set menu
    page.menu = makeMainMenu(selected=0)

    page.action = ''
    page.subname = ''
    page.filterform = {}

    showHistory = False

    historyType = None
    unitList = []
    for key, value in DeviceQuickSelect.handle_post(req).iteritems():
        if value:
            historyType = key
            unitList = value

            page.boxList = makeHistory(form, historyType, unitList, startTime,
                                       endTime, eventtype_filter, alerttype_filter)

            page.filterform[key] = value

            page.subname = 'history'
            showHistory = True

            break

    if deviceorderid:
        sql = "SELECT deviceid FROM device WHERE " +\
              "deviceorderid='%s'" % (deviceorderid,)
        result = executeSQL(sql,fetch=True)
        if result:
            historyType = CN_DEVICE
            unitList = []
            for row in result:
                unitList.append(row[0])
            page.boxList = makeHistory(form, historyType, unitList,
                                       startTime, endTime, eventtype_filter,
                                       alerttype_filter)
            page.subname = 'history'
        else:
            page.errors.append('Could not find any devices for this order')

    if not showHistory:
        page.quickselect = DeviceQuickSelect
    else:
        page.quickselect = ''

    nameSpace = {'page': page}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = CURRENT_PATH
    return template.respond()

def makeHistory(form, historyType, unitList, startTime, endTime,
                eventtypes, alerttypes):
    boxList = []

    for unitid in unitList:
        if historyType == CN_MODULE:
            boxList.append(ModuleHistoryBox(unitid, startTime, endTime,
                                            eventtypes, alerttypes))
        elif historyType == CN_BOX:
            boxList.append(NetboxHistoryBox(unitid, startTime, endTime,
                                            eventtypes, alerttypes))
        elif historyType == CN_ROOM:
            boxList.append(RoomHistoryBox(unitid, startTime, endTime,
                                          eventtypes, alerttypes))
        elif historyType == CN_LOCATION:
            boxList.append(LocationHistoryBox(unitid, startTime, endTime,
                                              eventtypes, alerttypes))
        elif historyType == CN_DEVICE:
            where = "deviceid='%s'" % (unitid,)
            box = nav.db.manage.Netbox.getAll(where=where)
            module = nav.db.manage.Module.getAll(where=where)
            if box:
                box = box[0]
                boxList.append(NetboxHistoryBox(box.netboxid, startTime,
                                                endTime,
                                                eventtypes,
                                                alerttypes))
            elif module:
                module = module[0]
                boxList.append(ModuleHistoryBox(module.moduleid, startTime,
                                                endTime, eventtypes,
                                                alerttypes))
            else:
                boxList.append(DeviceHistoryBox(unitid, startTime, endTime,
                                                eventtypes, alerttypes))
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
                  G_ALLVARS: 'allvars',
                  G_ALLMSGS: 'allmsgs'}

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
                default = ['Event: ' + G_EVENTTYPE + ', '
                           'Alert: ' + G_ALERTTYPE + ' '
                           #'Vars: ' + G_ALLVARS +
                           '\n' + G_ALLMSGS]

                formatString = self.getFormatting(event)
                if not formatString:
                    formatString = default

                startTime = event.start_time.strftime(TIMEFORMAT)
                endTime = None
                if event.end_time:
                    if event.end_time == INFINITY:
                        endTime = 'Still active'
                    else:
                        endTime = event.end_time.strftime(TIMEFORMAT)

                descr = self.format(formatString,event)

                self.rows.append([[startTime],[endTime],descr])

    def format(self,formatList,event):
        formattedList = []
        for formatString in formatList:
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
    def __init__(self, locationid, startTime, endTime, eventtypes, alerttypes):
        loc = nav.db.manage.Location(locationid)
        self.title = loc.descr

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime,
                            eventtypes=eventtypes, alerttypes=alerttypes)
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
    def __init__(self, roomid, startTime, endTime, eventtypes, alerttypes):
        room = nav.db.manage.Room(roomid)
        self.title = str(roomid) + ' (' + str(room.descr) + ')'

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime,
                            eventtypes=eventtypes, alerttypes=alerttypes)
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
    def __init__(self, netboxid, startTime, endTime, eventtypes, alerttypes):
        box = nav.db.manage.Netbox(netboxid)
        self.title = box.sysname

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime,
                            eventtypes=eventtypes, alerttypes=alerttypes)
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
    def __init__(self, moduleid, startTime, endTime, eventtypes, alerttypes):
        module = nav.db.manage.Module(moduleid)

        self.title = 'Module ' + str(module.module) + ' in ' + \
                      module.netbox.sysname

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime,
                            eventtypes=eventtypes, alerttypes=alerttypes)
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
    def __init__(self, deviceid, startTime, endTime, eventtypes, alerttypes):
        device = nav.db.manage.Device(deviceid)
        self.title = 'Device not currently in operation (%s)' % (device.serial,)

        ec = EventCollector(orderBy='start_time desc',
                            startTime=startTime, endTime=endTime,
                            eventtypes=eventtypes, alerttypes=alerttypes)
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
            self.sysname = dtTables.Netbox(netboxId).sysname
            self.url = '/ipdevinfo/%s/' % self.sysname
        if self.moduleId:
            module = dtTables.Module(moduleId)
            self.module = module.module
            self.sysname = module.netbox.sysname
            self.url = '/ipdevinfo/%s/%s/' % (self.sysname, self.module)

    def addEvent(self,sort_key, e, modulehist=False):
        if not modulehist:
            self.events.append((sort_key,e))
        else:
            self.moduleevents.append((sort_key,e))

    def getHistory(self):
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
    def __init__(self, eventtypes=None, alerttypes=None, limit=None,
                 offset=None, orderBy=None, startTime=None, endTime=None):

        self.eventtypes = eventtypes or []
        self.alerttypes = alerttypes or []
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

        sql = """
SELECT
    alerthist.alerthistid,
    alerthist.source,
    alerthist.deviceid,
    alerthist.netboxid,
    alerthist.subid,
    alerthist.start_time,
    alerthist.end_time,
    alerthist.eventtypeid,
    alerthist.value,
    alerthist.severity,
    alerthist.alerttypeid,
    alerttype.alerttype
FROM
    alerthist LEFT JOIN alerttype USING (alerttypeid)
"""

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
                sql += "alerthist.eventtypeid='%s' " % (eventtype,)
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

                sql += "alerthist.alerttypeid=%s" % (atidsql,)
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
                   {'start': self.startTime.strftime('%Y-%m-%d 00:00:00'),
                    'end': self.endTime.strftime('%Y-%m-%d 23:59:59')}

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
        result = database.dictfetchall()

        events = []
        if result:
            for row in result:
                event = DeviceEvent(row['eventtypeid'], row['alerttype'])
                event.alerthistid = row['alerthistid']
                event.source = row['source']
                event.deviceid = row['deviceid']
                event.netboxid = row['netboxid']
                event.subid = row['subid']
                event.start_time = row['start_time']
                event.end_time = row['end_time']
                event.value = row['value']
                event.severity = row['severity']

                # get alerthistvars
                sql = """
SELECT state, var, val
FROM alerthistvar
WHERE alerthistid='%s'""" % event.alerthistid
                database.execute(sql)
                vars = database.dictfetchall()
                if vars:
                    for var in vars:
                        event.addVar(var['var'], var['val'], var['state'])

                # get alerthistmsgs
                sql = """
SELECT state, msg
FROM alerthistmsg
WHERE msgtype='sms' AND language='en' AND alerthistid='%s'""" % \
                    event.alerthistid
                database.execute(sql)
                msgs = database.dictfetchall()
                if msgs:
                    for msg in msgs:
                        event.addMsg(msg['msg'], msg['state'])

                events.append(event)
        return events
