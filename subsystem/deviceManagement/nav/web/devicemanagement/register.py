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
Register page of Device Management
"""

### Imports

import psycopg

try:
    from mod_python import util
except:
    pass # To allow use of pychecker

import nav.db.manage
from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate

from nav.web.devicemanagement.constants import *
from nav.web.devicemanagement.common import *
from nav.web.devicemanagement.deviceevent import DeviceEvent
from nav.web.devicemanagement.page import Page
from nav.web.devicemanagement.widget import Widget

### Functions

def register(req,path):
    page = Page()
    form = req.form
    subpath = path[1]

    product = None
    if form.has_key(CN_PRODUCT):
        product = form[CN_PRODUCT]

    if form.has_key(CN_ARRIVE_CONFIRM):
        if form.has_key(CN_SERIAL):
            if len(form[CN_SERIAL]):
                if len(form[CN_PRODUCT]):
                    serial = form[CN_SERIAL]
                    # Create devices
                    fields = {}
                    fields['productid'] = form[CN_PRODUCT]
                    fields['active'] = 'true'
                    fields['serial'] = serial
                    deviceid = None
                    try:
                        sequence = ('deviceid',
                                    'device_deviceid_seq')
                        deviceid = insertFields(fields,'device',sequence)
                        page.messages.append("Added device with serial '" +\
                                             serial + "'")
                    except psycopg.IntegrityError:
                        page.errors.append("A device with serial '" +\
                                             serial + "' already exists")
                    # Send device active start event
                    event = DeviceEvent('deviceActive')
                    event.state = DeviceEvent.STATE_START
                    event.deviceid = deviceid
                    event.addVar('serial',serial)
                    event.addVar('source','registered')
                    event.post()
                    # Send deviceState onShelf start
                    event = DeviceEvent('deviceState','deviceOnShelf')
                    event.state = DeviceEvent.STATE_START
                    event.addVar('username',req.session['user'].login)
                    event.deviceid = deviceid
                    event.post()
                else:
                    page.errors.append('Missing product')
        else:
            page.errors.append('Missing serial')

    # Set menu
    page.menu = makeMainMenu(selected=2)

    page.name = 'register'
    page.title = 'Register serial numbers'
    page.description = 'Create new devices by entering serialnumbers.'
    page.widgets = {}
    page.action = BASEPATH+'register/'

    page.widgets['serial'] = Widget(CN_SERIAL,'text','Serial')
    page.widgets['submit'] = Widget(CN_ARRIVE_CONFIRM,'submit','Register')
    # Make productlist
    products = nav.db.manage.Product.getAllIterator()
    options = [(None,'Select a product',False)]
    for product in products:
        options.append((str(product.productid),
                        product.productno + ' (' + product.descr + ')',
                        False))
    page.widgets['product'] = Widget(CN_PRODUCT,'select','Product',
                                     product,                                
                                     options={'options': options},
                                     required=True)

    nameSpace = {'page': page}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = CURRENT_PATH
    return template.respond()
