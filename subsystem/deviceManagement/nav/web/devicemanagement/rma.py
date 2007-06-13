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
RMA page of Device Management
"""

### Imports

import forgetSQL

try:
    from mod_python import util
except:
    pass # To allow use of pychecker

import nav.db.manage
from nav.web import SearchBox
from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate
from nav.web.TreeSelect import TreeSelect, Select, UpdateableSelect, Option, SimpleSelect

from nav.web.devicemanagement.common import *
from nav.web.devicemanagement import db as dtTables
from nav.web.devicemanagement.deviceevent import DeviceEvent
from nav.web.devicemanagement.formattedlist import FormattedList
from nav.web.devicemanagement.history import History
from nav.web.devicemanagement.page import Page
from nav.web.devicemanagement.widget import Widget

### Functions

def rma(req,path):
    page = Page()
    form = req.form
    subpath = path[1]

    # Set menu
    page.menu = makeMainMenu(selected=3)

    page.name = 'rma'
    page.title = 'Register RMA'
    page.description = 'Active RMA events. Select return to register ' +\
                       'return of devices.'
    page.widgets = {}
    page.action = BASEPATH+'rma/register/'

    # Get formdata
    addRMAKeys = [CN_YEAR,CN_MONTH,CN_DAY,CN_RMANUMBER,CN_RMACOMMENT,
                  CN_RMARETAILER]
    formData = {}
    for key in addRMAKeys:
        if form.has_key(key):
            formData[key] = form[key]
        else:
            formData[key] = None

    submenu = [('Active RMA events','List active RMA events',
                BASEPATH+'rma/'),
               ('Register RMA request','Register RMA request',
                BASEPATH+'rma/register')]
    page.submenu = submenu

    deviceidList = []
    if form.has_key(CN_ADD_DEVICE):
        if form.has_key(CN_DEVICE):
            deviceidList = form[CN_DEVICE]
            if type(deviceidList) in (str, unicode, util.StringField):
                deviceidList = [deviceidList]
    elif form.has_key(CN_ADD_RMA):
        if form.has_key(CN_RMANUMBER):
            if len(form[CN_RMANUMBER]):
                if form.has_key(CN_ADDED_DEVICES):
                    if len(form[CN_ADDED_DEVICES]):
                        rmanumber = form[CN_RMANUMBER]
                        deviceidsAdded = form[CN_ADDED_DEVICES]
                        if type(deviceidsAdded) in (str, unicode,
                                                    util.StringField):
                            deviceidsAdded = [deviceidsAdded]
                        retailer = None
                        if form.has_key(CN_RMARETAILER):
                            retailer = form[CN_RMARETAILER]
                        comment = None
                        if form.has_key(CN_RMACOMMENT):
                            retailer = form[CN_RMACOMMENT] 
                        year = form[CN_YEAR]
                        month = form[CN_MONTH]
                        day = form[CN_DAY]
                        registerRMA(deviceidsAdded,rmanumber,year,month,day,
                                    retailer,comment,req.session['user'].login)
                        subpath = ''
                        page.messages.append('Sent RMA event')
                    else:
                        page.errors.append('You must select at least one ' +\
                                           'device')
                else:
                    page.errors.append('You must select at least one device')
            else:
                page.errors.append('You must enter an RMA number')
        else:
            page.errors.append('You must enter an RMA number')

    if subpath == 'register':
        page.subname = 'register'
        page.description = 'Add devices to RMA'
        page.rmasearchbox,page.treeselect = makeTreeSelectRMA(req)

        addedDevices = []
        if form.has_key(CN_ADDED_DEVICES):
            addedDevices = form[CN_ADDED_DEVICES]
            if type(addedDevices) in (str, unicode, util.StringField):
                addedDevices = [addedDevices]

        for deviceid in deviceidList:
            if not deviceid in addedDevices:
                addedDevices.append(deviceid)

        rows = []
        for deviceid in addedDevices:
            page.hiddenInputs.append((CN_ADDED_DEVICES,deviceid))
            device = nav.db.manage.Device(deviceid)
            if device.product:
                productname = device.product.productno
            else:
                productname = ''
            rows.append([[device.serial],[productname],
                         [device.hw_ver],[device.sw_ver]])

        page.rmalist = RMAList('Selected devices',rows)

        page.widgets['rmadate'] = Widget([CN_DAY,CN_MONTH,CN_YEAR],'date',
                                          'RMA date',
                                          [formData[CN_YEAR],
                                           formData[CN_MONTH],
                                           formData[CN_DAY]])
        page.widgets['number'] = Widget(CN_RMANUMBER,'text','RMA Number',
                                           formData[CN_RMANUMBER],
                                           required=True)
        page.widgets['comment'] = Widget(CN_RMACOMMENT,'textarea','Comment',
                                           formData[CN_RMACOMMENT],
                                           options={'rows': '5',
                                                    'cols': '10',
                                                    'style': 'width: 100%;'})
        page.widgets['retailer'] = Widget(CN_RMARETAILER,'text','Retailer',
                                           formData[CN_RMARETAILER])

        page.widgets['adddevice'] = Widget(CN_ADD_DEVICE,'submit','Add device')
        page.widgets['addrma'] = Widget(CN_ADD_RMA,'submit','Add RMA')
    else:
        # Main page
        sql = "SELECT device.deviceid,serial,serial " +\
              "FROM device,alerthist WHERE " +\
              "device.deviceid = alerthist.deviceid AND " +\
              "active='false' AND active='true' ORDER BY deviceid"
        colformat = [['$1$'],
                     ['$2$'],
                     ['$3$'],
                     [['url','Details',BASEPATH+'rma/details/$8$/']]]

        headings = [('RMA Number',None),
                    ('Date',None),
                    ('Amount',None),
                    ('',None)]

        page.rmaList = FormattedList('orders','Active RMA events',headings,
                                       colformat,sql)

    nameSpace = {'page': page}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = CURRENT_PATH
    return template.respond()

def registerRMA(deviceidList,rmanumber,year,month,day,retailer,
                comment,username):

    for deviceid in deviceidList:
        # Send RMA events
        # Send deviceState deviceRMA event
        event = DeviceEvent('deviceState','deviceRMA')
        event.state = DeviceEvent.STATE_START
        event.deviceid = deviceid
        event.addVar('rmanumber',rmanumber)
        event.addVar('username',username)
        rmadate = year + '-' + month + '-' + day
        event.addVar('date',rmadate)
        if retailer:
            event.addVar('retailer',rmadate)
        if comment:
            event.addVar('comment',comment)
        event.post()

def makeTreeSelectRMA(req):
    # Make the searchbox
    searchbox = SearchBox.SearchBox(req,
                'Search for (partial) serialname',
                title='Serial search')
    searchbox.addSearch('serial',
                        'serialnumber',
                        'Device',
                        {'devices': ['device','deviceid']},
                        like = 'serial')
    sr = searchbox.getResults(req)

    # Make treeselect
    selectbox = TreeSelect()

    if not sr.has_key('devices'):
        sr['devices'] = []

    select = SimpleSelect(CN_DEVICE,
                          "Devices matching serial '%s'" % \
                          (searchbox.getQuery(req),),
                          initTable='Device', 
                          initTextColumn='serial',
                          initIdColumn='deviceid',
                          initIdList = sr['devices'],
                          multiple = True,
                          multipleSize = 5,
                          optionFormat = '$d',
                          orderByValue = True)

    selectbox.addSelect(select)
    selectbox.update(req.form)
    return (searchbox,selectbox)

def registerRma(req,deviceId=None):
    args = {}
    args['path'] = [('Home','/'),
                    ('Tools','/toolbox'),
                    ('Device Management',BASEPATH),
                    ('Register RMA',False)]

    args['error'] = None
    rmaList = None

    rmaDevice = None
    if deviceId:
        try:
            device = dtTables.Device(deviceId)
            device.load()

            args['action'] = BASEPATH + 'rma/device/' + str(deviceId)
            # is this a netbox or a module?
            netbox = dtTables.Netbox.getAll('deviceid=%s' % (deviceId,))
            module = dtTables.Module.getAll('deviceid=%s' % (deviceId,))
            if len(module):
                rmaDevice = History(deviceId,
                                    netboxId=module[0].netbox.netboxid,
                                    moduleId=module[0].moduleid)
            elif len(netbox):
                rmaDevice = History(deviceId,netboxId=netbox[0].netboxid)
            else:
                # neither netbox nor module, shouldn't happen
                rmaDevice = History(deviceId)
        except forgetSQL.NotFound:
            args['error'] = 'No device with deviceid ' + str(deviceId)

    if req.form.has_key('cn_submit'):
        try:
            if req.form.has_key('cn_rma'):
                if not len(req.form['cn_rma']):
                    raise 'norma','You must enter an RMA number'

                # post a rma start event
                de = DeviceEvent(eventTypeId='deviceRma',
                                 deviceId=deviceId)
                de.state = DeviceEvent.STATE_START
                vars = {'username': req.session['user'].login,
                        'rmanumber': req.form['cn_rma'],
                        'comment': req.form['cn_comment']}
                de.addVars(vars)

                de.postEvent()
                redirect(req,BASEPATH + 'rma/')

        except "norma",e:
            args['error'] = e
    else:
        # No form input, show list of active RMAs
        where = ["eventtypeid='deviceRma'","end_time='infinity'"]
        activeRmas = dtTables.AlerthistDt.getAll(where,orderBy='start_time')
        rmaList = []
        for rma in activeRmas:
            netbox = rma.device.getNetbox()
            module = rma.device.getModule()
            if netbox:
               deviceDescr = 'Netbox %s' % (netbox.sysname)
            elif module:
               deviceDescr = 'Module %s in netbox %s' % \
               (module.module, module.netbox.sysname)
            else:
                deviceDescr = str(rma.device.deviceid)
            date = rma.start_time.strftime(DATEFORMAT)
            username = rma.getVar('username','s')
            comment = rma.getVar('comment','s')
            deviceid = rma.device.deviceid
            rmaList.append((deviceDescr,date,username,comment,deviceid))

    args['rmaList'] = rmaList
    args['rmaDevice'] = rmaDevice
    args['addrma'] = {'url': BASEPATH + 'browse/rma',
                      'text': 'Register RMA for device'}
    args['returned'] = {'url': BASEPATH + 'rma/returned/',
                        'text': 'Device returned'}
    args['newreturned'] = {'url': BASEPATH + 'rma/returnednew/',
                           'text': 'New device returned'}
    args['returnpath'] = {'url': BASEPATH,
                          'text': 'Return'}
    args['update'] = BASEPATH + 'rma/'


    nameSpace = {'page': 'rma', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = args['path']
    return template.respond()

def rmaReturned(req,deviceId,new=False):
    # send deviceRma end event
    de = DeviceEvent(eventTypeId='deviceRma',
                     deviceId=deviceId)
    de.state = DeviceEvent.STATE_END
    vars = {'username': req.session['user'].login}
    de.addVars(vars)

    de.postEvent()
    # redirect to register new device if new = True
    if new:
        redirect(req,BASEPATH + 'register/')
    else:
        redirect(req,BASEPATH + 'rma/')

### Classes

class RMAList:
    headings = [('Serial',''),
                ('Product',''),
                ('Hardware version',''),
                ('Software version','')]

    def __init__(self,title,rows):
        self.title = title
        self.rows = rows
