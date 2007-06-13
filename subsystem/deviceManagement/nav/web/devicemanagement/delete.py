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
Delete page of Device Management
"""

### Imports

try:
    from mod_python import util
except:
    pass # To allow use of pychecker

from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate

from nav.web.devicemanagement.constants import *
from nav.web.devicemanagement.common import *
from nav.web.devicemanagement.deviceevent import DeviceEvent
from nav.web.devicemanagement.formattedlist import FormattedList
from nav.web.devicemanagement.page import Page
from nav.web.devicemanagement.widget import Widget

### Functions

def delete(req,path):
    subpath = path[1]

    page = Page()
    form = req.form

    page.name = 'delete'
    page.widgets = {} 
    page.title = 'Module delete'
    page.action = BASEPATH+'delete/'

    submenu = [('Modules down','Show and delete modules that are down',
                BASEPATH+'delete/'),
                ('Device inventory','Show devices on shelf',
                BASEPATH+'delete/inventory/'),
                ('Inactive devices','Show devices which have been removed',
                BASEPATH+'delete/inactive/')]
    page.submenu = submenu

    if form.has_key(CN_DELETE_MODULE):
        # Delete module pressed
        if form.has_key(CN_MODULE_SELECT):
            deviceidList = form[CN_MODULE_SELECT]
            if type(deviceidList) in (str, unicode, util.StringField):
                deviceidList = [deviceidList]
            subpath = 'confirmdelete'
        else:
            page.errors.append('No modules selected')
    elif form.has_key(CN_DELETE_MODULE_CONFIRM):
        if form.has_key(CN_MODULE_SELECT):
            deviceidList = form[CN_MODULE_SELECT]
            if type(deviceidList) in (str, unicode, util.StringField):
                deviceidList = [deviceidList]
            if len(form[CN_MOVETO]):
                action = form[CN_MOVETO]
                if action == 'shelf':
                    for deviceid in deviceidList:
                        for deviceid in deviceidList:
                            # Delete module
                            sql = "DELETE FROM module WHERE " +\
                                  "deviceid='%s'" % (deviceid,)
                            executeSQL(sql)

                            # Send deviceState onShelf start
                            event = DeviceEvent('deviceState','deviceOnShelf')
                            event.state = DeviceEvent.STATE_START
                            event.deviceid = deviceid
                            event.addVar('username',req.session['user'].login)
                            event.post()
                elif action == 'inactive':
                    for deviceid in deviceidList:
                        # Delete module
                        sql = "DELETE FROM module WHERE " +\
                              "deviceid='%s'" % (deviceid,)
                        executeSQL(sql)
                        # Set device inactive
                        fields = {'active': 'false'}
                        updateFields(fields,'device','deviceid',deviceid)
                        # Send device active end event
                        event = DeviceEvent('deviceActive')
                        event.state = DeviceEvent.STATE_END
                        event.deviceid = deviceid
                        event.addVar('username',req.session['user'].login)
                        event.post()
                page.messages.append('Deleted')
            else:
                page.errors.append('You must select an action')
                subpath = 'confirmdelete'
        else:
            page.errors.append('No modules selected')
    elif form.has_key(CN_INVENTORY_MOVE):
        if form.has_key(CN_MODULE_SELECT):
            deviceidList = form[CN_MODULE_SELECT]
            if type(deviceidList) in (str, unicode, util.StringField):
                deviceidList = [deviceidList]
            for deviceid in deviceidList:
                # Set device inactive
                fields = {'active': 'false'}
                updateFields(fields,'device','deviceid',deviceid)
                # Send deviceState onShelf end
                event = DeviceEvent('deviceState','deviceOnShelf')
                event.state = DeviceEvent.STATE_END
                event.deviceid = deviceid
                event.post()
                # Send device active end event
                event = DeviceEvent('deviceActive')
                event.state = DeviceEvent.STATE_END
                event.deviceid = deviceid
                event.addVar('username',req.session['user'].login)
                event.post()
            page.messages.append('Set as inactive')
        else:
            page.errors.append('No modules selected')
    elif form.has_key(CN_INACTIVE_MOVE):
        if form.has_key(CN_MODULE_SELECT):
            deviceidList = form[CN_MODULE_SELECT]
            if type(deviceidList) in (str, unicode, util.StringField):
                deviceidList = [deviceidList]
            for deviceid in deviceidList:
                # Set device active
                fields = {'active': 'true'}
                updateFields(fields,'device','deviceid',deviceid)
                # Send device active start event
                event = DeviceEvent('deviceActive')
                event.state = DeviceEvent.STATE_START
                event.addVar('source','inventory')
                event.deviceid = deviceid
                event.post()
                # Send deviceState onShelf start
                event = DeviceEvent('deviceState','deviceOnShelf')
                event.state = DeviceEvent.STATE_START
                event.addVar('username',req.session['user'].login)
                event.deviceid = deviceid
                event.post()
            page.messages.append('Moved to inventory')
        else:
            page.errors.append('No modules selected')

    if subpath == 'confirmdelete':
        page.subname = 'confirmdelete'
        page.description = 'Select between moving device to inventory or ' +\
                           'setting it inactive before confirming.'
        options = [('','Select action',True),
                   ('shelf','Move to inventory',False),
                   ('inactive','Set as inactive',False)]
        page.widgets['moveto'] = Widget(CN_MOVETO,'select','Not shown',
                                         options={'options': options},
                                         required=True)
        page.widgets['confirm'] = Widget(CN_DELETE_MODULE_CONFIRM,'submit',
                                         'Confirm')
        # Make list of selected modules
        sql = "SELECT module,descr,netbox.sysname " +\
              "FROM module,netbox,alerthist WHERE " +\
              "module.netboxid=netbox.netboxid AND " +\
              "alerthist.deviceid=module.deviceid AND " +\
              "module.up='n' AND alerthist.eventtypeid='moduleState' AND " +\
              "alerthist.end_time='infinity' AND ("

        first = True
        for id in deviceidList:
            if not first:
                sql += "OR "
            first = False
            page.hiddenInputs.append((CN_MODULE_SELECT,id))
            sql += "module.deviceid='%s' " % (id,)
        sql += ")"

        colformat = [['$2$'],
                     ['$0$'],
                     ['$1$']]

        headings = [('Sysname',None),
                    ('Module',None),
                    ('Description',None)]

        page.moduleList = FormattedList('modules','Selected modules',headings,
                                        colformat,sql)
    elif subpath == 'inventory':
        page.description = 'List of devices that are in the inventory but ' +\
                           'not in operation in a stack.'

        page.subname = 'inventory'
        page.action = BASEPATH+'delete/inventory/'
        page.widgets['move'] = Widget(CN_INVENTORY_MOVE,'submit',
                                      'Set inactive')
        sql = "SELECT product.productno,product.descr,serial," +\
              "hw_ver,sw_ver,device.deviceid " +\
              "FROM product,device,alerthist,alerttype WHERE " +\
              "device.active='true' AND " +\
              "device.productid=product.productid AND " +\
              "alerthist.deviceid=device.deviceid AND " +\
              "alerthist.eventtypeid='deviceState' AND " +\
              "alerttype.alerttype='deviceOnShelf' AND " +\
              "alerthist.alerttypeid=alerttype.alerttypeid AND " +\
              "alerthist.end_time='infinity' AND device.active='true' " +\
              "ORDER BY alerthist.start_time "

        colformat = [[['widget',Widget(CN_MODULE_SELECT,'checkbox',
                                       value='$5$')]],
                     ['$2$'],
                     ['$0$ ($1$)'],
                     ['$3$'],
                     ['$4$']]

        headings = [('',None),
                    ('Serial',None),
                    ('Product',None),
                    ('Hardware version',None),
                    ('Software version',None)]

        page.moduleList = FormattedList('devices','Device inventory',headings,
                                        colformat,sql)
    elif subpath == 'inactive':
        page.subname = 'inactive'
        page.action = BASEPATH+'delete/inactive/'
        page.description = 'List of modules that have been set as ' +\
                           'inactive. Normally this indicates that ' +\
                           'the device has reached its end of life, but ' +\
                           'these devices can be reactived by moving them ' +\
                           'to the inventory.'

        page.widgets['move'] = Widget(CN_INACTIVE_MOVE,'submit',
                                      'Move to inventory')

        sql = "SELECT product.productno,product.descr,serial," +\
              "hw_ver,sw_ver,device.deviceid " +\
              "FROM product,device WHERE " +\
              "device.active='true' AND " +\
              "device.productid=product.productid AND " +\
              "device.active='false' " +\
              "ORDER BY product.productno,product.descr"

        colformat = [[['widget',Widget(CN_MODULE_SELECT,'checkbox',
                                       value='$5$')]],
                     ['$2$'],
                     ['$0$ ($1$)'],
                     ['$3$'],
                     ['$4$']]

        headings = [('',None),
                    ('Serial',None),
                    ('Product',None),
                    ('Hardware version',None),
                    ('Software version',None)]

        page.moduleList = FormattedList('modules','Inactive devices',headings,
                                        colformat,sql)
    else:
        page.description = 'Select modules to delete from modules that are ' +\
                           'down. When deleting a module, a choice will be ' +\
                           'given to either move the device to the ' +\
                           'inventory or to set it as inactive.'

        sql = "SELECT module,descr,netbox.sysname,alerthist.start_time," +\
              "now()-alerthist.start_time,module.deviceid " +\
              "FROM module,netbox,alerthist,device WHERE " +\
              "module.deviceid=device.deviceid AND " +\
              "module.netboxid=netbox.netboxid AND " +\
              "alerthist.deviceid=module.deviceid AND " +\
              "module.up='n' AND alerthist.eventtypeid='moduleState' AND " +\
              "alerthist.end_time='infinity' " +\
              "ORDER BY alerthist.start_time "

        page.widgets['delete'] = Widget(CN_DELETE_MODULE,'submit','Next')
        colformat = [[['widget',Widget(CN_MODULE_SELECT,'checkbox',
                                       value='$5$')]],
                     ['$2$'],
                     ['$0$'],
                     ['$1$'],
                     ['$3$'],
                     ['$4$']]

        headings = [('',None),
                    ('Sysname',None),
                    ('Module',None),
                    ('Description',None),
                    ('Down since',None),
                    ('Downtime',None)]

        page.moduleList = FormattedList('modules','Modules down',headings,
                                        colformat,sql)


    # Set menu
    page.menu = makeMainMenu(selected=5)

    nameSpace = {'page': page}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = CURRENT_PATH
    return template.respond()
