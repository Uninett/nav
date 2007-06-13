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
Error page of Device Management
"""

### Imports

import nav.db.manage
from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate

from nav.web.devicemanagement.common import *
from nav.web.devicemanagement.deviceevent import DeviceEvent
from nav.web.devicemanagement.page import Page
from nav.web.devicemanagement.widget import Widget

### Functions

def error(req):
    page = Page()
    form = req.form

    page.name = 'error'
    page.title = 'Register error'
    page.description = 'Register an error by selecting one ' +\
                       'or more units (locations, rooms, boxes or modules) ' +\
                       'and enter a description of the error.'

    # Set menu
    page.menu = makeMainMenu(selected=4)

    page.action = ''

    showSelect = True
    if form.has_key('error') and form.has_key(CN_ERRCOMMENT):
        if len(form[CN_ERRCOMMENT]):
            # Register error
            comment = form[CN_ERRCOMMENT]
            username = req.session['user'].login
            errorType = None
            if form.has_key(CN_MODULE):
                errorType = CN_MODULE
            elif form.has_key(CN_BOX):
                errorType = CN_BOX
            elif form.has_key(CN_ROOM):
                errorType = CN_ROOM
            elif form.has_key(CN_LOCATION):
                errorType = CN_LOCATION
            elif form.has_key(CN_DEVICE):
                errorType = CN_DEVICE

            if form[errorType] is list:
                unitList = form[errorType]
            else:
                unitList = [form[errorType]]

            result = registerError(errorType,unitList,comment,username)
            page.messages = result
        else:
            page.errors.append('You must enter an error comment.')

    if showSelect:
        # Browse mode, make treeselect
        page.searchbox,page.treeselect = makeTreeSelect(req,size=10,
                                                        serialSearch=True)
        page.formname = page.treeselect.formName

        page.submit = {'control': 'error',
                       'value': 'Register error',
                       'enabled': True}

        page.widgets = {}
        page.widgets['comment'] = Widget(CN_ERRCOMMENT,'textarea','Error comment',
                                           options={'rows': '5',
                                                    'cols': '80',
                                                    'style': 'width: 100%;'})

        #page.errorInput = {'control': 'errorinput',
        #                   'description': 'Error comment:',
        #                   'size': '50',
        #                   'enabled': validSubmit}

    nameSpace = {'page': page}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = CURRENT_PATH
    return template.respond()

def registerError(errorType,unitList,comment,username):
    result = []

    olderrorType = errorType
    for unitid in unitList:
        if errorType == CN_DEVICE:
            where = "deviceid='%s'" % (unitid,)
            box = nav.db.manage.Netbox.getAll(where)
            module = nav.db.manage.Module.getAll(where)
            if box:
                errorType = CN_BOX
                unitid = box[0].netboxid
            elif module:
                errorType = CN_MODULE
                unitid = module[0].moduleid

        event = DeviceEvent('deviceNotice','deviceError')
        event.addVar('comment',comment)
        event.addVar('username',username)
        if errorType == CN_MODULE:
            module = nav.db.manage.Module(unitid)
            event.subid = module.moduleid
            event.netboxid = module.netbox.netboxid
            event.deviceid = module.device.deviceid
            event.addVar('unittype','module')
            event.addVar('roomid',module.netbox.room.roomid)
            event.addVar('locationid',module.netbox.room.location.locationid)
            result.append('Registered error on module ' + str(module.module) +\
                          ' in box ' + module.netbox.sysname)
        elif errorType == CN_BOX:
            netbox = nav.db.manage.Netbox(unitid)
            event.subid = None
            event.netboxid = netbox.netboxid
            event.deviceid = netbox.device.deviceid
            event.addVar('unittype','netbox')
            event.addVar('roomid',netbox.room.roomid)
            event.addVar('locationid',netbox.room.location.locationid)
            result.append('Registered error on box ' + netbox.sysname)
        elif errorType == CN_ROOM:
            room = nav.db.manage.Room(unitid)
            event.subid = None
            event.netboxid = None
            event.deviceid = None
            event.addVar('unittype','room')
            event.addVar('roomid',room.roomid)
            event.addVar('locationid',room.location.locationid)
            result.append('Registered error on room ' + room.roomid)
        elif errorType == CN_LOCATION:
            location = nav.db.manage.Location(unitid)
            event.subid = None
            event.netboxid = None
            event.deviceid = None
            event.addVar('unittype','location')
            event.addVar('locationid',location.locationid)
            result.append('Registered error on location '+location.locationid)
        elif errorType == CN_DEVICE:
            event.subid = None
            event.netboxid = None
            event.deviceid = unitid
            event.addVar('unittype','device')
            device = nav.db.manage.Device(unitid)
            serial = device.serial
            result.append("Registered error on device with serial '" +\
                           serial + "'")
        event.post()
        errorType = olderrorType
    return result
