# -*- coding: ISO8859-1 -*-
# $Id$
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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#
"""
Contains all the functions and custom classes used 
by the deviceTracker, and is also the default handler.
"""

#################################################
## Imports

import nav.db.manage
import mx.DateTime
import re
import forgetSQL
import psycopg

from mod_python import util,apache
from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate
#from deviceManagementTemplate import deviceManagementTemplate
from nav.web.TreeSelect import TreeSelect,Select,UpdateableSelect,Option,SimpleSelect
from nav.web import urlbuilder,SearchBox

import logging
logger = logging.getLogger('nav.web.devicemanager')

#################################################
## Constants (read from config file)

BASEPATH = '/devicemanagement/'
DATEFORMAT = '%d-%m-%Y'
TIMEFORMAT = '%d-%m-%Y %H:%M'
TIMESTAMP = '%Y-%m-%d %H:%M:%S'
INFINITY = mx.DateTime.DateTime(999999,12,31,0,0,0)
MAX_NUMBER_OF_DEVICES_ORDERED = 20
NUMBER_OF_ARRIVED_SERIALS = 10
DELETE_TIME_THRESHOLD = mx.DateTime.TimeDelta(hours=48)

MAIN_MENU = [['Device history',BASEPATH,'Browse and view device history'],
             ['Order devices',BASEPATH + 'order/','Order new devices and register arrivals of devices with serials'],
             ['Register devices',BASEPATH + 'register/','Register new devices with serials'],
             ['Register RMA',BASEPATH + 'rma/','Register a RMA request'],
             ['Register error event',BASEPATH + 'error/','Register an error event with a comment on a location, room, box or module'], 
             ['Module delete',BASEPATH + 'delete/','Manually delete any modules that are flagged as down']]

CURRENT_PATH = [('Home', '/'),
                ('Device Management', BASEPATH)]

# Controlnames for TreeSelect
CN_LOCATION = 'location'
CN_ROOM = 'room'
CN_BOX = 'box'
CN_MODULE = 'module'
CN_DEVICE = 'device'

##
## Default handler
##

def handler(req):
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)
    path = req.uri.split(BASEPATH)[1]
    path = path.split('/')

    if path[0] == 'error':
        output = error(req)
    elif path[0] == 'order':
        output = order(req,path)
    elif path[0] == 'delete':
        output = delete(req,path)
    elif path[0] == 'rma':
        output = rma(req,path)
    elif path[0] == 'register':
        output = register(req,path)
    else:
        # Default 
        output = history(req)

    if output:
        req.content_type = "text/html"
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND

##
## Pages
##

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
                    try:
                        sequence = ('deviceid',
                                    'public.device_deviceid_seq')
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
    page.title = 'Register devices'
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


CN_ADD_DEVICE = 'r_dadd'
CN_ADD_RMA = 'r_radd'
CN_RMANUMBER = 'r_number'
CN_RMACOMMENT = 'r_comment'
CN_RMARETAILER = 'r_retailer'
CN_ADDED_DEVICES = 'r_added'
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

    if not subpath:
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

CN_ERRCOMMENT = 'e_comment'
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

# Constants
CN_YEAR = 'o_year'
CN_MONTH = 'o_month'
CN_DAY = 'o_day'
CN_RETAILER = 'o_retailer'
CN_COMMENT = 'o_comment'
CN_ORDERNUMBER = 'o_ordernumber'
CN_PRODUCT = 'o_product'
CN_AMOUNT = 'o_amount'
CN_ADD_SUBMIT = 'o_asubmit'
CN_ADD_CONFIRM = 'o_confirm'
CN_UPDATE_SUBMIT = 'o_usubmit'
CN_UPDATE_CONFIRM = 'o_uconfirm'
CN_CANCEL = 'o_cancel'
CN_ORG = 'o_org'
CN_DELETE_CONFIRM = 'o_dconfirm'
#
CN_ARRIVE_CONFIRM = 'o_arsubmit'
CN_STATE = 'o_action'
CN_SERIAL = 'o_serial'
CN_PENDING = 'o_pending'
CN_ARRIVED = 'o_arrived'
CN_CANCELLED = 'o_cancelled'
#
# Delete module
CN_DELETE_MODULE = 'd_delete'
CN_DELETE_MODULE_CONFIRM = 'd_confirm'
CN_MODULE_SELECT = 'd_moduleid'
CN_MOVETO = 'd_moveto'
CN_INVENTORY_MOVE = 'd_imoveto'
CN_INACTIVE_MOVE = 'd_inmoveto'

def order(req,path):
    subpath = path[1]
    page = Page()
    form = req.form
    alternativeOutput = None

    submenu = [('Active orders','Show and edit active orders',
                BASEPATH+'order/'),
                ('Add order','Add new order',BASEPATH+'order/add'),
                ('Order history','Show closed orders',
                BASEPATH+'order/history'),
                ('Add product','Add new product to the database',
                '/editdb/product/edit/')]
    page.submenu = submenu

    if not subpath or form.has_key(CN_CANCEL):
        subpath = 'main'

    addOrderKeys = [CN_YEAR,CN_MONTH,CN_DAY,CN_RETAILER,CN_COMMENT,
                    CN_ORDERNUMBER,CN_PRODUCT,CN_AMOUNT,CN_ORG]
    formData = {}
    for key in addOrderKeys:
        if form.has_key(key):
            formData[key] = form[key]
        else:
            formData[key] = None

    page.name = 'order'
    page.widgets = {} 
    page.title = 'Order devices'
    page.action = ''

    showConfirmButton = False
    
    orderAction = 'add'
    if form.has_key(CN_UPDATE_SUBMIT) or form.has_key(CN_UPDATE_CONFIRM):
        orderAction = 'edit'
        
    if form.has_key(CN_ADD_SUBMIT) or form.has_key(CN_ADD_CONFIRM) or \
       form.has_key(CN_UPDATE_SUBMIT) or form.has_key(CN_UPDATE_CONFIRM):
        # Validate order form
        if form[CN_PRODUCT]:
            if form[CN_ORG]:
                if len(form[CN_AMOUNT]):
                    validAmount = True
                    try:
                        amount = int(form[CN_AMOUNT])                    
                    except ValueError:
                        validAmount = False
                        amount = 0
                        page.errors.append('Invalid amount')
                        subpath = orderAction

                    if (amount < 1) and orderAction == 'add':
                        validAmount = False
                        page.errors.append('Invalid amount')
                        subpath = orderAction
                    elif (amount < 0):
                        # If updating, 0 is a valid amount
                        validAmount = False
                        page.errors.append('Invalid amount')
                        subpath = orderAction

                    if (amount > MAX_NUMBER_OF_DEVICES_ORDERED) and \
                       not (form.has_key(CN_ADD_CONFIRM) or \
                       form.has_key(CN_UPDATE_CONFIRM)):
                        validAmount = False
                        showConfirmButton = True
                        page.messages.append('Are you sure you want to ' +\
                                             'order this many devices?')
                        subpath = orderAction
                    
                    validDate = True
                    try:
                        testDate = mx.DateTime.Date(int(formData[CN_YEAR]),
                                                    int(formData[CN_MONTH]),
                                                    int(formData[CN_DAY]))
                    except mx.DateTime.RangeError:
                        validDate = False
                        page.errors.append('Invalid date')
                        subpath = orderAction
                    
                    if validDate and validAmount:
                        # Form validated, add new order                       
                        if orderAction == 'edit':
                            updateOrder(req,formData)
                            page.messages.append('Updated order')
                        else:
                            registerOrder(req,formData)
                            page.messages.append('Added order')
                else:
                    page.errors.append('You must enter an amount')
                    subpath = orderAction
            else:
                page.errors.append('You must select an organisation')
                subpath = orderAction
        else:
            page.errors.append('You must select a product')
            subpath = orderAction
    elif form.has_key(CN_DELETE_CONFIRM):
        # Confirm delete pressed
        deviceorderid = form['deviceorderid']
        page = deleteOrder(deviceorderid,page)
   
    if subpath == 'add' or subpath == 'edit':
        page.action = BASEPATH + 'order/'
        if subpath == 'add':
            page.description = 'Add new order. Product, amount and ' +\
                               'organisation is required to add an order.'
            page.subname = 'add'        
            if showConfirmButton:
                page.widgets['submit'] = Widget(CN_ADD_CONFIRM,
                                                'submit','Cofirm')
            else:
                page.widgets['submit'] = Widget(CN_ADD_SUBMIT,
                                                'submit','Add order')
        elif subpath == 'edit':
            if len(path) > 2:
                deviceorderid = path[2]
                page.hiddenInputs.append(('deviceorderid',deviceorderid))
                getDbOrder = True
            else:
                # No orderid from path, get from form
                deviceorderid = form['deviceorderid']
                page.hiddenInputs.append(('deviceorderid',deviceorderid))
                getDbOrder = False
            page.description = 'Edit an existing order. The amount is ' +\
                               'number of devices not yet ' +\
                               'registered as arrived. Decreasing the ' +\
                               'amount will not remove any devices that are ' +\
                               'already registered. Setting amount to zero ' +\
                               'will close the order.'
            page.subname = 'edit'
            if showConfirmButton:
                page.widgets['submit'] = Widget(CN_UPDATE_CONFIRM,
                                                'submit','Cofirm')
            else:
                page.widgets['submit'] = Widget(CN_UPDATE_SUBMIT,
                                                'submit','Update order')
            if getDbOrder:
                # Lookup order
                amountsql = "SELECT count(*) FROM device WHERE " +\
                            "device.deviceorderid=deviceorder.deviceorderid"
                arrivedsql = "SELECT count(*) FROM device WHERE " +\
                             "device.deviceorderid=deviceorder.deviceorderid"+\
                             " AND device.active=true"

                sql = "SELECT ordered,ordernumber,comment,retailer," +\
                      "productid,orgid,(%s),(%s) " % (amountsql,arrivedsql)+\
                      "FROM deviceorder " +\
                      "WHERE deviceorderid='%s'" % (deviceorderid,)
                result = executeSQL(sql,fetch=True)
                if result:
                    result = result[0]
                    formData[CN_YEAR] = str(result[0].year)
                    formData[CN_MONTH] = str(result[0].month)
                    formData[CN_DAY] = str(result[0].day)
                    formData[CN_AMOUNT] = str(result[6] - result[7])
                    formData[CN_ORDERNUMBER] = result[1]
                    formData[CN_COMMENT] = result[2]
                    formData[CN_RETAILER] = result[3]
                    formData[CN_PRODUCT] = str(result[4])
                    formData[CN_ORG] = result[5]
                else:
                    page.errors.append('Order does not exist')

        # Create widgets
        page.widgets['orderdate'] = Widget([CN_DAY,CN_MONTH,CN_YEAR],'date',
                                           'Order date',
                                           [formData[CN_YEAR],
                                            formData[CN_MONTH],
                                            formData[CN_DAY]])
        page.widgets['retailer'] = Widget(CN_RETAILER,'text','Retailer',
                                          formData[CN_RETAILER])
        page.widgets['amount'] = Widget(CN_AMOUNT,'text','Amount',
                                        formData[CN_AMOUNT],
                                        options={'size': '5'},required=True)
        page.widgets['comment'] = Widget(CN_COMMENT,'text','Comment',
                                         formData[CN_COMMENT],
                                         options={'style': 'width: 100%;'})
        page.widgets['ordernumber'] = Widget(CN_ORDERNUMBER,'text',
                                             'Ordernumber',
                                             formData[CN_ORDERNUMBER])
        # Make orglist
        memberOrgs = req.session['user'].getOrgIds()
        where = ''
        first = True
        for org in memberOrgs:
            if not first:
                where += "OR "
            where += "orgid='" + org + "' "
            first = False
        orgOptions = [(None,'Select an organisation',True)]
        if not len(memberOrgs):
            page.errors.append('You must be member of an organisation ' +\
                               'to add an order')
        else:
            orgs = nav.db.manage.Org.getAllIterator(where=where)
            for org in orgs:
                orgOptions.append((org.orgid,org.descr + ' (' + org.orgid + ')',
                                   False)) 
        page.widgets['org'] = Widget(CN_ORG,'select','Organisation',
                                     formData[CN_ORG],
                                     options={'options': orgOptions,
                                              'style': 'width: 100%;'},
                                     required=True)
        # Make productlist
        products = nav.db.manage.Product.getAllIterator()
        options = [(None,'Select a product',True)]
        for product in products:
            options.append((str(product.productid),
                            product.productno + ' (' + product.descr + ')',
                            False))
        page.widgets['product'] = Widget(CN_PRODUCT,'select','Product',
                                         formData[CN_PRODUCT],
                                         options={'options': options},
                                         required=True)
        page.widgets['cancel'] = Widget(CN_CANCEL,'submit','Cancel')
    elif subpath == 'arrival' and not form.has_key(CN_CANCEL):
        page.subname = 'arrival'

        deviceorderid = path[2]
        if form.has_key(CN_ARRIVE_CONFIRM):
            registerDevices(form,deviceorderid,req.session['user'].login,
                            page)

        page.orderFound = False
        if deviceorderid:
            # Lookup order
            amountsql = "SELECT count(*) FROM device WHERE " +\
                        "device.deviceorderid=deviceorder.deviceorderid"
            arrivedsql = "SELECT count(*) FROM device WHERE " +\
                         "device.deviceorderid=deviceorder.deviceorderid " +\
                         "AND device.active=true"
            sql = "SELECT productno,descr,ordernumber,(%s),(%s) " %\
                  (amountsql,arrivedsql) +\
                  "FROM deviceorder,product WHERE " +\
                  "deviceorder.productid=product.productid AND " +\
                  "deviceorderid='%s'" % deviceorderid
            result = executeSQL(sql,fetch=True)
            if result:
                result = result[0]
                productno,descr,ordernumber,amount,arrived = result
                if (amount-arrived) > 0:
                    page.orderFound = True
                    page.productName = productno + ' (' + descr + ')'
                    if ordernumber:
                        page.tableTitle = "Ordernumber '" + ordernumber +\
                                          "', " + str(arrived) + " of " +\
                                          str(amount) + " registered"
                    else:
                        page.tableTitle = str(arrived) + " of " +\
                                          str(amount) + " registered"

                    page.description = 'Register serials for devices upon' +\
                                       ' arrival.'
                    pending = amount-arrived
                    page.numberOfInputs = min(NUMBER_OF_ARRIVED_SERIALS,pending)
                else:
                    # No more device to register, close order
                    arrivedstamp = mx.DateTime.now().strftime(TIMESTAMP)
                    fields = {'arrived': arrivedstamp}
                    updateFields(fields,'deviceorder','deviceorderid',
                                 deviceorderid)
                    page.messages.append('Order closed')
                    subpath = 'main'
            else:
                page.description = 'Order not found'

        options = [(CN_PENDING,'Pending',True),
                   (CN_ARRIVED,'Arrived',False),
                   (CN_CANCELLED,'Cancelled',False)]
        page.widgets['arrivaldate'] = Widget([CN_DAY,CN_MONTH,CN_YEAR],'date',
                                              'Arrival date',
                                              [formData[CN_YEAR],
                                               formData[CN_MONTH],
                                               formData[CN_DAY]])
        page.widgets['action'] = Widget(CN_STATE,'select','State',
                                        options={'options': options})
        page.widgets['serial'] = Widget(CN_SERIAL,'text','Serial')
        page.widgets['submit'] = Widget(CN_ARRIVE_CONFIRM,'submit','Register')
        page.widgets['cancel'] = Widget(CN_CANCEL,'submit','Cancel')
    elif subpath=='delete' or subpath=='details':
        deviceorderid = path[2]
        page.hiddenInputs.append(('deviceorderid',deviceorderid))
        page.action = BASEPATH + 'order/'
        if subpath == 'delete':
            page.subname = 'delete'        
            page.description = 'Are you sure you want to delete this order? ' +\
                               'If any of the devices from this order are ' +\
                               'already registered as arrived'+\
                               ', they will not be deleted and the order '+\
                               'will be closed.'
        else:
            page.subname = 'details'
            page.description = ''
        page.widgets['confirm'] = Widget(CN_DELETE_CONFIRM,'submit','Confirm')
        page.widgets['cancel'] = Widget(CN_CANCEL,'submit','Cancel')
        # Get orderdata
        amountsql = "SELECT count(*) FROM device WHERE " +\
                    "device.deviceorderid=deviceorder.deviceorderid"
        arrivedsql = "SELECT count(*) FROM device WHERE " +\
                     "device.deviceorderid=deviceorder.deviceorderid " +\
                     "AND device.active=true"
        sql = "SELECT productno,descr,ordernumber,(%s),(%s)," %\
              (amountsql,arrivedsql) +\
              "ordered,comment,retailer,registered,username," +\
              "orgid,updatedby,lastupdated,arrived " +\
              "FROM deviceorder,product WHERE " +\
              "deviceorder.productid=product.productid AND " +\
              "deviceorderid='%s'" % deviceorderid
        result = executeSQL(sql,fetch=True)
        if result:
            result = result[0]
            lastupdated = ''
            if result[12]:
                lastupdated = result[12].strftime(DATEFORMAT)
            closed = None
            if result[13] != INFINITY:
                closed = result[13].strftime(DATEFORMAT)
         
            orderData = {'product': ('Product',result[0]+' ('+result[1]+')'),
                         'ordernumber': ('Ordernumber',result[2]),
                         'amount': ('Amount ordered',result[3]),
                         'arrived': ('Amount arrived',result[4]),
                         'ordered': ('Order date',
                                     result[5].strftime(DATEFORMAT)),
                         'comment': ('Comment',result[6]),
                         'retailer': ('Retailer',result[7]),
                         'registered': ('Date registered',
                                        result[8].strftime(DATEFORMAT)),
                         'username': ('Ordered by',result[9]),
                         'org': ('Organisation',result[10]),
                         'updatedby': ('Last updated by',result[11]),
                         'lastupdated': ('Last updated',lastupdated)}
            if closed:
                orderData['closed'] = ('Closed',closed)
            page.orderData = orderData
            page.orderDataHead = 'Order details'
        else:
            page.errors.append('Order not found')
            subpath = 'main'
    elif subpath == 'history':
        deviceorderid = None
        if len(path) > 2:
            deviceorderid = path[2]
            alternativeOutput = history(req,deviceorderid)
        page.description = 'Closed orders. Select details for more ' +\
                           'information on a specific order. Select ' +\
                           'device history to view event history for ' +\
                           'all devices in an order.'
        page.subname = 'main'
        amountsql = "SELECT count(*) FROM device WHERE device.deviceorderid="+\
                    "deviceorder.deviceorderid"
        arrivedsql = "SELECT count(*) FROM device WHERE device.deviceorderid="+\
                     "deviceorder.deviceorderid AND device.active=true"
        sql = "SELECT registered,ordered,ordernumber,retailer,comment," +\
              "username,product.productno,product.descr,deviceorderid," +\
              "(%s),(%s),orgid,arrived " % (amountsql,arrivedsql) +\
              "FROM deviceorder,product WHERE " +\
              "deviceorder.productid=product.productid AND " +\
              "arrived!='infinity' ORDER BY arrived DESC"
        colformat = [['$1$'],
                     ['$12$'],
                     ['$2$'],
                     ['$6$ ($7$)'],
                     ['$9$'],
                     ['$5$'],
                     ['$11$'],
                     [['url','Details',BASEPATH+'order/details/$8$/']],
                     [['url','Device history',BASEPATH+'order/history/$8$/']]]
                
        headings = [('Ordered',None),
                    ('Closed',None),
                    ('Ordernumber',None),
                    ('Product',None),
                    ('Amount',None),
                    ('Ordered by',None),
                    ('Organisation',None),
                    ('',None),
                    ('',None)]

        page.orderList = FormattedList('orders','Order history',headings,
                                       colformat,sql)

    if subpath=='main':
        # Main page
        page.description = 'Currently active orders. Register arrival of ' +\
                           'devices in an order by selecting arrival. '
        page.subname = 'main'
        amountsql = "SELECT count(*) FROM device WHERE device.deviceorderid="+\
                    "deviceorder.deviceorderid"
        arrivedsql = "SELECT count(*) FROM device WHERE device.deviceorderid="+\
                     "deviceorder.deviceorderid AND device.active=true"
        sql = "SELECT registered,ordered,ordernumber,retailer,comment," +\
              "username,product.productno,product.descr,deviceorderid," +\
              "(%s),(%s),orgid " % (amountsql,arrivedsql) +\
              "FROM deviceorder,product WHERE " +\
              "deviceorder.productid=product.productid AND " +\
              "arrived='infinity' ORDER BY ordered"
        colformat = [['$1$'],
                     ['$2$'],
                     ['$6$ ($7$)'],
                     ['$9$'],
                     ['$10$'],
                     ['$5$'],
                     ['$11$'],
                     [['url','Details',BASEPATH+'order/details/$8$/']],
                     [['url','Arrival',BASEPATH+'order/arrival/$8$/']],
                     [['url','Edit',BASEPATH+'order/edit/$8$/']],
                     [['url','Delete',BASEPATH+'order/delete/$8$/']]]
                
        headings = [('Ordered',None),
                    ('Ordernumber',None),
                    ('Product',None),
                    ('Amount',None),
                    ('Arrived',None),
                    ('Ordered by',None),
                    ('Organisation',None),
                    ('',None),
                    ('',None),
                    ('',None),
                    ('',None)]

        page.orderList = FormattedList('orders','Active orders',headings,
                                       colformat,sql)

    # Set menu
    page.menu = makeMainMenu(selected=1)

    if not alternativeOutput:
        nameSpace = {'page': page}
        template = deviceManagementTemplate(searchList=[nameSpace])
        template.path = CURRENT_PATH
        output = template.respond()
    else:
        output = alternativeOutput
    return output

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
                BASEPATH+'delete/inventory'),
                ('Inactive devices','Show devices which have been removed',
                BASEPATH+'delete/inactive')]
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
    elif form.has_key(CN_INVENTORY_MOVE):
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
    elif form.has_key(CN_INACTIVE_MOVE):
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
        page.action = BASEPATH+'inventory/'
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
        page.action = BASEPATH+'inactive/'
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

##
## Help functions
##

def newWidget(oldWidget):
    # Creates a copy of a general widget object
    widget = Widget(oldWidget.controlname,
                    oldWidget.type,
                    oldWidget.name,
                    oldWidget.value,
                    oldWidget.options,
                    oldWidget.required)
    return widget

def registerDevices(form,orderid,username,page):
    if type(form[CN_SERIAL]) in (str, unicode, util.StringField):
        serialList = [form[CN_SERIAL]]
    else:
        serialList = form[CN_SERIAL]
    if type(form[CN_STATE]) in (str, unicode, util.StringField):
        stateList = [form[CN_STATE]]
    else:
        stateList = form[CN_STATE]

    sql = "SELECT deviceid FROM device WHERE deviceorderid='%s' " % orderid +\
          "AND active='f'"
    result = executeSQL(sql,fetch=True)
    if result:
        deviceidList = []
        for row in result:
            deviceidList.append(row[0])
        if len(serialList) > len(deviceidList):
            page.errors.append('More serials than devices')
        else:
            count = 0
            for i in range(0,len(serialList)):
                if len(serialList[i]) and (stateList[i] == CN_ARRIVED):
                    # Update serial
                    fields = {'serial': serialList[i],
                              'active': 'true'}
                    try:
                        updateFields(fields,'device','deviceid',deviceidList[i])
                        count += 1
                        # Send deviceactive event
                        event = DeviceEvent('deviceActive')
                        event.state = DeviceEvent.STATE_START
                        event.deviceid = deviceidList[i]
                        event.addVar('serial',serialList[i])
                        arrivaldate = form[CN_YEAR] + '-' +\
                                      form[CN_MONTH] + '-' + \
                                      form[CN_DAY]
                        event.addVar('arrivaldate',arrivaldate)
                        event.addVar('source','registered')
                        event.post()
                        # Send devicestate event
                        event = DeviceEvent('deviceState','deviceOnShelf')
                        event.state = DeviceEvent.STATE_START
                        event.deviceid = deviceidList[i]
                        event.addVar('username',username)
                        event.post()
                    except psycopg.IntegrityError:
                        page.errors.append("A device with the serial '%s' " %\
                                           serialList[i] +\
                                           "already exists in the database")
            if count == 1:
                page.messages.append('Registered ' + str(count) + ' device')
            else:
                page.messages.append('Registered ' + str(count) + ' devices')
    else:
        page.errors.append('All devices from this order are already registered')

def deleteOrder(deviceorderid,page):
    # Check if any of the devices are registered
    amountsql = "SELECT count(*) FROM device WHERE " +\
                "deviceorderid='%s'" % (deviceorderid,) +\
                "AND active=true"
    result = executeSQL(amountsql,fetch=True)
    arrived = result[0][0]
    if arrived > 0:
        # Only delete inactive devices and close order
        sql = "DELETE FROM device WHERE deviceorderid='%s' " % \
              (deviceorderid,) +\
              "AND active=false"
        executeSQL(sql) 
        fields = {'arrived': mx.DateTime.now().strftime(TIMESTAMP)}
        updateFields(fields,'deviceorder','deviceorderid',deviceorderid)
        page.messages.append('Deleted inactive devices and closed order')
    else:
        # Delete entire order
        sql = "DELETE FROM deviceorder WHERE deviceorderid='%s' " \
              % (deviceorderid,)
        executeSQL(sql)
        page.messages.append('Order deleted')
    return page

def updateOrder(req,formData):
    form = req.form
    deviceorderid = form['deviceorderid']

    # Add or delete devices
    amountsql = "SELECT count(*) FROM device WHERE " +\
                "deviceorderid='%s'" % (deviceorderid,) +\
                "AND device.active=false"
    result = executeSQL(amountsql,fetch=True)
    oldamount = result[0][0]
    
    amount = int(formData[CN_AMOUNT])
    if amount > oldamount:
        # Make new devices
        fields = {}
        fields['productid'] = formData[CN_PRODUCT]
        fields['deviceorderid'] = deviceorderid
        fields['active'] = 'false'

        for i in range(0,amount-oldamount):
            insertFields(fields,'device')

    elif amount < oldamount:
        # Delete devices, first get all deviceids from this order
        deleteAmount = oldamount-amount
        sql = "SELECT deviceid FROM device WHERE " +\
              "deviceorderid='%s' " % (deviceorderid,) +\
              "AND device.active=false"
        result = executeSQL(sql,fetch=True)
        deviceidList = []
        i = 1
        for row in result:
            deviceidList.append(row[0])
            if i == deleteAmount:
                break
            i += 1
        sql = "DELETE FROM device WHERE "
        first = True
        for id in deviceidList:
            if not first:
                sql += "OR "
            sql += "deviceid='%d' " % (id,)
            first = False
        executeSQL(sql)

    # Update deviceorder
    orderdate = formData[CN_YEAR] + '-' + formData[CN_MONTH] + '-' + \
                formData[CN_DAY]
    fields = {}
    now = mx.DateTime.now()
    if amount == 0:
        # Close the order
        fields['arrived'] = now.strftime(TIMESTAMP) 
    fields['productid'] = formData[CN_PRODUCT]
    fields['updatedby'] = req.session['user'].login
    lastupdated = str(now.year) + '-' + str(now.month) + '-' + \
                  str(now.day)
    fields['lastupdated'] = lastupdated
    fields['orgid'] = formData[CN_ORG]
    orderdate = formData[CN_YEAR] + '-' + formData[CN_MONTH] + '-' + \
                formData[CN_DAY]
    fields['ordered'] = orderdate
    if formData.has_key(CN_RETAILER):
        fields['retailer'] = formData[CN_RETAILER]
    if formData.has_key(CN_ORDERNUMBER):
        fields['ordernumber'] = formData[CN_ORDERNUMBER]
    if formData.has_key(CN_COMMENT):
        fields['comment'] = formData[CN_COMMENT]
    updateFields(fields,'deviceorder','deviceorderid',deviceorderid)


def registerOrder(req,formData):
    # Create deviceorder
    fields = {}
    fields['productid'] = formData[CN_PRODUCT]
    fields['username'] = req.session['user'].login
    fields['orgid'] = formData[CN_ORG]
    orderdate = formData[CN_YEAR] + '-' + formData[CN_MONTH] + '-' + \
                formData[CN_DAY]
    fields['ordered'] = orderdate
    if formData.has_key(CN_RETAILER):
        fields['retailer'] = formData[CN_RETAILER]
    if formData.has_key(CN_ORDERNUMBER):
        fields['ordernumber'] = formData[CN_ORDERNUMBER]
    if formData.has_key(CN_COMMENT):
        fields['comment'] = formData[CN_COMMENT]

    sequence = ('deviceorderid','public.deviceorder_deviceorderid_seq')
    orderid = insertFields(fields,'deviceorder',sequence)

    # Create devices
    fields = {}
    fields['productid'] = formData[CN_PRODUCT]
    fields['deviceorderid'] = orderid
    fields['active'] = 'false'

    for i in range(0,int(formData[CN_AMOUNT])):
        insertFields(fields,'device')

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

def executeSQL(sql,fetch=False):
    connection = nav.db.getConnection('devicemanagement','manage')
    database = connection.cursor()
    # Clean sql string
    database.execute(sql)
    result = None
    if fetch:
        result = database.fetchall()
    return result

def updateFields(fields,table,idfield,updateid):
    sql = 'UPDATE ' + table + ' SET '
    first = True
    for field,value in fields.items():
        if not first:
            sql += ','
        sql += field + "='" + value + "'"
        first = False
    sql += ' WHERE ' + idfield + "='" + str(updateid) + "'"
    executeSQL(sql)

def insertFields(fields,table,sequence=None):
    # Add a new entry using the dict fields which contain
    # key,value pairs 

    # Sequence is a tuple (idfield,sequencename). If given, get
    # the nextval from sequence and set the idfield to this value
    nextid = None
    if sequence:
        idfield,seq = sequence
        sql = "SELECT nextval('%s')" % (seq,)
        result = executeSQL(sql,fetch=True)
        nextid = str(result[0][0])
        fields[idfield] = nextid

    sql = 'INSERT INTO ' + table + ' ('
    first = True
    for field,value in fields.items():
        if not first:
            sql += ','
        sql += field
        first = False
    sql += ') VALUES ('
    first = True
    for field,value in fields.items():
        if not first:
            sql += ','
        sql += "'" + value + "'"
        first = False
    sql += ')'
    executeSQL(sql)
    return nextid


def makeMainMenu(selected):
    menu = []

    i = 0
    for item in MAIN_MENU:
        path = item[1]
        if i == selected:
            path = None
        menu.append([item[0],path,item[2]])
        i += 1
    return menu

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


def makeTreeSelect(req,serialSearch=False,size=20):
    # Make the searchbox
    searchbox = SearchBox.SearchBox(req,
                'Type a room id, an ip or a (partial) sysname',
                title='Quicksearch')
    if serialSearch:
        searchbox.addSearch('serial',
                            'serialnumber',
                            'Device',
                            {'devices': ['device','deviceid']},
                            like = 'serial')
    searchbox.addSearch('host',
                        'ip or hostname',
                        'Netbox',
                        {'rooms': ['room','roomid'],
                         'locations': ['room','location','locationid'],
                         'netboxes': ['netboxid']},
                        call = SearchBox.checkIP)
    searchbox.addSearch('room',
                        'room id',
                        'Room',
                        {'rooms': ['roomid'],
                         'locations': ['location','locationid']},
                        where = "roomid = '%s'")
    sr = searchbox.getResults(req)

    # Make treeselect
    selectbox = TreeSelect()
    multiple = False

    if not sr.has_key('devices'):
        sr['devices'] = []

    if len(sr['devices']):
        select = SimpleSelect(CN_DEVICE,
                              "Devices matching serial '%s'" % \
                              (searchbox.getQuery(req),),
                              initTable='Device', 
                              initTextColumn='serial',
                              initIdColumn='deviceid',
                              initIdList = sr['devices'],
                              multiple = True,
                              multipleSize = size,
                              optionFormat = '$d',
                              orderByValue = True)

        selectbox.addSelect(select)
    else:
        select = Select(CN_LOCATION,
                        'Location',
                        multiple = True,
                        multipleSize = size,
                        initTable='Location', 
                        initTextColumn='descr',
                        initIdColumn='locationid',
                        preSelected = sr['locations'],
                        optionFormat = '$v ($d)',
                        orderByValue = True)

        select2 = UpdateableSelect(select,
                                   CN_ROOM,
                                   'Room',
                                   'Room',
                                   'descr',
                                   'roomid',
                                   'locationid',
                                   multiple=True,
                                   multipleSize=size,
                                   preSelected = sr['rooms'],
                                   optionFormat = '$v ($d)',
                                   orderByValue = True)

        select3 = UpdateableSelect(select2,
                                   CN_BOX,
                                   'Box',
                                   'Netbox',
                                   'sysname',
                                   'netboxid',
                                   'roomid',
                                   multiple=multiple,
                                   multipleSize=size,
                                   preSelected = sr['netboxes'])

        select4 = UpdateableSelect(select3,
                                   CN_MODULE,
                                   'Module',
                                   'Module',
                                   'module',
                                   'moduleid',
                                   'netboxid',
                                   multiple=multiple,
                                   multipleSize=size,
                                   onchange='',
                                   optgroupFormat = '$d') 
        # onchange='' since this doesn't update anything

        selectbox.addSelect(select)
        selectbox.addSelect(select2)
        selectbox.addSelect(select3)
        selectbox.addSelect(select4)

    selectbox.update(req.form)

    return (searchbox,selectbox)

##
## Classes
##

class FormattedList:
    def __init__(self,name,title,headings,colformat,sql,limit=None,offset=None):
        self.title = title
        self.headings = headings
        self.rows = []
        
        result = executeSQL(sql,fetch=True)
        # Regexp matching $1i$,$2$,...
        regexp = re.compile("\$(\d+)\$")

        for resultrow in result:
            testDate = mx.DateTime.now()
            tmprow = list(resultrow)
            resultrow = []
            for data in tmprow:
                ## UGLY!
                if type(data) == type(testDate):
                    data = data.strftime(DATEFORMAT)
                elif not type(data) is str:
                    data = str(data)
                elif not data:
                    data = ''
                resultrow.append(data)
            row = []
            for formatstring in colformat:
                column = []
                for part in formatstring:
                    if type(part) is list:
                        # This part of the formatstring is on the format
                        # [string:type,string:data] where string:type can
                        # be 'url','image','widget'
                        partType = part[0]
                        tempcol = []
                        tempcol.append(partType)
                        if partType == 'widget':
                            # Format the value of the widget
                            # Make a copy of the general widget
                            widget = newWidget(part[1])
                            col = widget.value
                            while regexp.search(col):
                                match = regexp.search(col).groups()[0]
                                col = col.replace('$' + match + '$',
                                                  resultrow[int(match)])
                            widget.value = col
                            tempcol.append(widget)
                            column.append(tempcol)
                        else:
                            for i in range(1,len(part)):
                                col = part[i]
                                while regexp.search(col):
                                    match = regexp.search(col).groups()[0]
                                    col = col.replace('$' + match + '$',
                                                      resultrow[int(match)])
                                tempcol.append(col)
                            column.append(tempcol)
                    elif type(part) is str:
                        col = part
                        while regexp.search(col):
                            match = regexp.search(col).groups()[0]
                            col = col.replace('$' + match + '$',
                                              resultrow[int(match)])
                        column.append(col)
                row.append(column)
            self.rows.append(row)

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


class Widget:
    MONTHS = ['January','February','March','April','May','June','July',
              'August','September','October','November','December']

    # Widget 'struct' for the template
    def __init__(self,controlname,type,name=None,value=None,options=None,
                 required=False):
        self.controlname = controlname
        self.type = type
        self.name = name
        if options is None: options = {}
        self.options = options
        self.required = required
        self.value = value

        if type == 'date':
            # date widget
            self.valueY = self.value[0]
            self.valueM = self.value[1]
            self.valueD = self.value[2]
            now = mx.DateTime.now()
            if options.has_key('startyear'):
                startYear = options['startyear']
            else:
                startYear = now.year - 1
            if options.has_key('endyear'):
                endYear = options['endyear']
            else:
                endYear = now.year
            if options.has_key('setdate'):
                setdate = options['setdate']
            else:
                setdate = mx.DateTime.now()

            monthOptions = []
            for i, month in enumerate(self.MONTHS):
                i += 1
                thisMonth = False
                if self.valueM:
                    if self.valueM == str(i):
                        thisMonth = True
                else:
                   if setdate.month == i:
                       thisMonth = True
                monthOptions.append((str(i),month,thisMonth))

            dayOptions = []
            for d in range(1,32):
                thisDay = False
                if self.valueD:
                    if self.valueD == str(d):
                        thisDay = True
                else:
                    if d == setdate.day:
                        thisDay = True
                dayOptions.append((str(d),str(d),thisDay))

            yearOptions = []
            for y in range(startYear,endYear+1):
                thisYear = False
                if self.valueY:
                    if self.valueY == str(y):
                        thisYear = True
                else:
                    if y == setdate.year:
                        thisYear = True
                yearOptions.append((str(y),str(y),thisYear))

            self.options['months'] = monthOptions
            self.options['days'] = dayOptions
            self.options['years'] = yearOptions


class Page:
    errors = []
    messages = []
    
    searchbox = None
    treeselect = None

    def __init__(self):
        self.errors = []
        self.messages = []
        self.searchbox = None
        self.treeselect = None
        self.hiddenInputs = []
        self.submenu = None
        self.subname = None
        self.description = None

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

class RMAList:
    headings = [('Serial',''),
                ('Product',''),
                ('Hardware version',''),
                ('Software version','')]

    def __init__(self,title,rows):
        self.title = title
        self.rows = rows

# Global
G_EVENTTYPE = '%et%'
G_ALERTTYPE = '%at%'
G_ALLVARS = '%av%'

# deviceActive
# deviceState
# deviceNotice
DN_E_USERNAME = '$dn_e_u$'
DN_E_COMMENT = '$dn_e_c$'
DN_E_UNITTYPE = '$dn_e_ut$'
DN_E_LOCATIONID = '$dn_e_l$'
DN_E_ROOMID = '$dn_e_r$'
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

class GetEvents:
    def __init__(self,eventtypeId,alerttype,where=None,orderBy=None,limit=None):
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

        # get active orders
        connection = nav.db.getConnection('devicemanagement','manage')
        database = connection.cursor()
        sql = "SELECT alerthist.alerthistid,alerthist.source," +\
              "alerthist.deviceid,alerthist.netboxid,alerthist.subid," +\
              "alerthist.start_time,alerthist.end_time," +\
              "alerthist.eventtypeid,alerthist.value,alerthist.severity," +\
              "alerthist.alerttypeid,alerttype.alerttype " +\
              "FROM alerthist,alerttype WHERE " +\
              "alerthist.alerttypeid=alerttype.alerttypeid AND " +\
              "alerthist.eventtypeid='%s' " % (eventtypeId,) + \
              "AND alerttype.alerttype='%s' " % (alerttype,)

        if where:
            sql += "AND " + where
        if orderBy:
            sql += " ORDER BY " + orderBy
        if limit:
            sql += " LIMIT " + str(limit)

        database.execute(sql)
        result = database.fetchall() 

        events = []
        if result:
            for row in result:
                event = DeviceEvent(row[EVENTTYPEID],
                                    row[ALERTTYPE])
                event.alerthistid = row[ALERTHISTID]
                event.source = row[SOURCE]
                event.netboxId = row[NETBOXID]
                event.subId = row[SUBID]
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
        self.events = events

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
                deviceDescr = str(dt.device.deviceid)
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

def registerErrorOld(req,deviceId=None):
    """
    Only called by deviceTracker/error/device/XXXX
    """
    errorDevice = None
    try:
        if deviceId:
            device = dtTables.Device(deviceId).load()
            if req.form.has_key('cn_error'):
                if len(req.form['cn_error']):
                    errorEvent = DeviceEvent(eventTypeId='deviceError',
                                             deviceId=deviceId)
                    errorEvent.state = DeviceEvent.STATE_NONE
                    
                    username = req.session['user'].login
                    vars = {'comment': req.form['cn_error'],
                            'username': username}
                    errorEvent.addVars(vars)
                    errorEvent.postEvent()
                    redirect(req,BASEPATH)
            # No error registered yet
            errorDevice = History(deviceId)
        else:
            redirect(req,BASEPATH)
    except forgetSQL.NotFound:
        redirect(req,BASEPATH)

    args = {}
    args['returnpath'] = {'url': BASEPATH + 'error/',
                          'text': 'Return'}
    args['errordevice'] = errorDevice
    args['action'] = BASEPATH + 'error/device/' + str(deviceId)

    nameSpace = {'page': 'error', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    return template.respond()

   
def historyOld(req,deviceId):
    args = {}

    where = ['deviceid=%s' % (deviceId,)]
    module = dtTables.Module.getAll(where)
    netbox = dtTables.Netbox.getAll(where)

    moduleId = None
    netboxId = None
    if module:
        moduleId = module[0].moduleid
    elif netbox:
        netboxId = netbox[0].netboxid

    args['deviceHistList'] = [History(deviceId,
                                      netboxId=netboxId,
                                      moduleId=moduleId)]
    if req.form.has_key('return'):
        args['returnpath'] = {'url': req.form['return'],
                              'text': 'Return'}
    else:
        args['returnpath'] = None

    nameSpace = {'page': 'history', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    return template.respond()

def orderOld(req):
    args = {}
    args['path'] = [('Home','/'),
                    ('Tools','/toolbox'),
                    ('Device Management',BASEPATH),
                    ('Order management',False)]

    # get all active and old order events
    orderBy = 'start_time'
    allEvents=GetEvents('deviceChanged','deviceOrdered',orderBy=orderBy).events

    allOrders = {}
    for event in allEvents:
        orderId = event.subId
        if not allOrders.has_key(orderId):
            # First time we see this orderId
            allOrders[orderId] = [1,event]
        else:
            if event.end_time == INFINITY:
                # This is an active order
                # If at least one of the order events are still active,
                # the whole order is listed as active
                allOrders[orderId][1] = event
            # Increase ordered amount by one
            allOrders[orderId][0] += 1

    activeOrders = []
    oldOrders = []
    for value in allOrders.values():
        amount = value[0]
        event = value[1]

        # Get variables from the Alerthistvar table
        usernameOrdered = event.getVar('username',state='s')
        orgId = event.getVar('orgid',state='s')
        retailer = event.getVar('retailer',state='s')
        orderNr = event.getVar('orderid',state='s')
        usernameRegistered = event.getVar('username',state='e')

        device = nav.db.manage.Device(event.deviceId)
        productname = device.product.vendor.vendorid + ' ' + \
                      device.product.productno
        productid = device.product.productid
        o = Order(event.subId,
                  event.start_time.strftime(DATEFORMAT),
                  event.end_time.strftime(DATEFORMAT),
                  productname,
                  productid,
                  amount,
                  usernameOrdered,
                  orgId,
                  retailer,
                  orderNr)

        if (event.end_time == INFINITY):
            activeOrders.append(o)
        else:
            oldOrders.append(o)

    args['activeOrders'] = activeOrders
    args['oldOrders'] = oldOrders
    args['returnpath'] = {'url': BASEPATH,
                          'text': 'Return'}
    args['update'] = BASEPATH + 'order/'

    nameSpace = {'page': 'order', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = args['path']
    return template.respond()

def addOrder(req):
    form = req.form
    args = {}
    args['path'] = [('Home','/'),
                    ('Tools','/toolbox'),
                    ('Device Management',BASEPATH),
                    ('Order management',BASEPATH + 'order/'),
                    ('Add order',None)]

    args['action'] = BASEPATH + 'order/add'
    args['error'] = ''

    # submit button pressed?
    if form.has_key('cn_submit'):
        if len(form['cn_prodid']) and len(form['cn_org']):
            if form.has_key('cn_number'):
                try:
                    ci_number = int(form['cn_number'])
                except ValueError:
                    ci_number = 0
                if ci_number > 0:
                    ci_prodid = form['cn_prodid']
                    ci_orgid = form['cn_org']
                    ci_retailer = form['cn_retailer']
                    ci_ordernr = form['cn_ordernr']

                    connection = nav.db.getConnection('devicemanagement',
                                                      'manage')
                    database = connection.cursor()
                    firstDevice = True
                    # Create devices
                    for i in range(0,ci_number):
                        sql = "INSERT INTO device (productid) VALUES (%s)" \
                        % ci_prodid
                        database.execute(sql)

                        # get the new deviceid
                        sql = "SELECT currval('device_deviceid_seq')"
                        database.execute(sql)
                        connection.commit()
                        deviceId = int(database.fetchone()[0])

                        # The orderid is set to the first deviceid in the order
                        if firstDevice:
                            orderId = deviceId
                            firstDevice = False

                        # create a deviceOrdered event and post it to the eventq
                        de = DeviceEvent(eventtypeId='deviceChanged',
                                         alerttype='deviceOrdered',
                                         deviceId=deviceId)
                        de.subId = orderId
                        de.state = DeviceEvent.STATE_START
                        # variables
                        username = req.session['user'].login
                        vars = {'username': username,
                                'orgid': ci_orgid,
                                'retailer': ci_retailer,
                                'orderid': ci_ordernr}
                        de.addVars(vars)
                        de.postEvent()

                    redirect(req,BASEPATH + 'order/')
                else:
                    args['error'] = 'Amount must be positive'
            else:
                args['error'] = 'You must enter an amount'
        else:
            if not len(form['cn_org']):
                args['error'] = 'You must select an organisation'
            if not len(form['cn_prodid']):
                args['error'] = 'You must select a product'

    # make list of orgs and products for the selects
    orgs = nav.db.manage.Org()
    orgList = [('','Select an organisation')]
    where = memberoforg(req)
    for org in orgs.getAllIterator(where):
        orgList.append((org.orgid,'(' + org.orgid + ') ' + org.descr))
    args['orgList'] = orgList
    
    products = nav.db.manage.Product()
    productList = [('','Select a product')]
    for product in products.getAllIterator():
        productList.append((product.productid,product.vendor.vendorid + ' ' + \
        product.productno + ' ' + product.descr))
    args['productList'] = productList
    args['returnpath'] = {'url': BASEPATH + 'order/',
                          'text': 'Return to order overview'}

    nameSpace = {'page': 'addOrder', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = args['path']
    return template.respond()


def registerOrderOld(req,orderId):
    STATE_ARRIVED = 'st_arr'
    STATE_PENDING = 'st_pen'
    STATE_CANCELLED = 'st_can'

    args = {}
    args['error'] = None

    if not orderId:
        redirect(req,BASEPATH + 'order/')
    
    alerthist = dtTables.AlerthistDt
    where = ["eventtypeid='deviceOrdered'","subid=%s" % (orderId,)]
    orderedEvents = alerthist.getAll(where)

    if not orderedEvents:
        redirect(req,BASEPATH + 'order/')
 
    # Store the orderid somewhere for the heading in the template
    args['orderid'] = orderedEvents[0].getVar("orderid","s")
 
    # Init preselected states and serials (state=arrived, serial=None)
    states = []
    serials = []
    for event in orderedEvents:
        states.append('st_arr')
        serials.append(None)

    try:
        if req.form.has_key('cn_state'):
            states = req.form['cn_state']
            serials = req.form['cn_serial']
            if type(states) in (str, unicode, util.StringField):
                states = [states]
                serials = [serials]

            # Are serials entered for all devices with state = arrived?
            for i in range(0,len(states)):
                if states[i] == STATE_ARRIVED:
                    if not serials[i]:
                        raise 'serial','Missing serial number for arrived item'

            device = dtTables.Device

            i = 0
            cancelled = []
            for event in orderedEvents:
                if not event.device.serial:
                    if states[i] == STATE_ARRIVED:
                        # state = arrived, set serial number for device
                        deviceId = event.device.deviceid
                        d = device(deviceId)
                        d.serial = serials[i]
                        d.save()
                        # send deviceOrdered, state=end to the eventq
                        # create a deviceOrdered event and post it to the eventq
                        de = DeviceEvent('deviceOrdered')
                        de.deviceId = deviceId
                        de.subId = orderId
                        de.state = DeviceEvent.STATE_END
                        # create variable dict
                        username = req.session['user'].login
                        vars = {'username': username}
                        de.addVars(vars)
                        de.postEvent()
                    if states[i] == STATE_PENDING:
                        # state = pending, do nothing
                        pass
                    if states[i] == STATE_CANCELLED:
                        # state = cancelled, this device must be deleted
                        # but not before everything else is OK
                        cancelled.append(event.device.deviceid) 
                    i += 1
        
            # Delete devices where state = cancelled
            for id in cancelled:
                row = device(id)
                row.delete()

            # Finished with this order for now, redirect to order page
            redirect(req, BASEPATH + 'order/')

    except 'serial',e:
        args['error'] = e                    
    except psycopg.IntegrityError,e:
        # duplicate serial number, must reset the serial number of this instance
        # even if it isn't saved to the database
        args['error'] = "Duplicate serial number '" + d.serial + "'"
        d.serial = None

    args['states'] = states
    args['serials'] = serials
    args['action'] = BASEPATH + 'order/register/' + orderId
    args['events'] = orderedEvents
    args['statelist'] = [(STATE_ARRIVED,'Arrived'),
                         (STATE_PENDING,'Pending'),
                         (STATE_CANCELLED,'Cancelled')]
    args['returnpath'] = {'url': BASEPATH + 'order/',
                          'text': 'Return to order overview'}


    nameSpace = {'page': 'registerOrder', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    return template.respond()

def registerOld(req):
    args = {}
    args['error'] = None
    args['path'] = [('Home','/'),
                    ('Tools','/toolbox'),
                    ('Device Management',BASEPATH),
                    ('Register new device',False)]

    try:
        if req.form.has_key('cn_submit'):
            serial = req.form['cn_serial']
            productId = req.form['cn_prodid']
            
            if not len(serial):
                raise "noserial","You must enter a serialnumber"
            # Make new device
            d = dtTables.Device()
            d.serial = serial
            d.product = dtTables.Product(productId)
            d.save()
            deviceId = int(d._getID()[0])
            
            ## FIX: funker det å slå den opp igjen?
            d = dtTables.Device(deviceId)
            # send deviceRegistered to the eventq
            de = DeviceEvent('deviceRegistered')
            de.deviceId = deviceId
            de.state = DeviceEvent.STATE_NONE
            # create variable dict
            username = req.session['user'].login
            vars = {'username': username}
            de.addVars(vars)
            de.postEvent()

    except 'noserial',e:
        args['error'] = e                    
    except psycopg.IntegrityError,e:
        # duplicate serial number, must reset the serial number of this instance
        # even if it isn't saved to the database
        args['error'] = "Duplicate serial number '" + d.serial + "'"
        d.serial = None

    # Make a list of products
    products = dtTables.Product()
    productList = []
    for product in products.getAllIterator():
        productList.append((product.productid,product.vendor.vendorid + ' ' + \
        product.productno,product.descr))
    args['productList'] = productList
    args['action'] = BASEPATH + 'register/'
    args['returnpath'] = {'url': BASEPATH,
                          'text': 'Return'}

    nameSpace = {'page': 'register', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = args['path']
    return template.respond()

def redirect(req, url):
    req.headers_out.add("Location", url)
    raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY

def makewherelist(orglist):
    whereList = ''
    if orglist:
        first = True
        for org in orglist:
            if not first:
                whereList += ' or '
            whereList += "orgid='" + org + "'"
            first = False
        return whereList
    else:
        return None

def memberoforg(req):
    where = makewherelist(req.session['user'].getOrgIds())

    # if superuser, no restrictions based on orgids
    superuser = False
    #for group in req.session['user'].getGroups():
    #    if group.id == 1:
    #        superuser = True
    #        break

    if superuser == True:
        where = []
    return where

class Order:
    """
    Represents an order
    """

    # orderId equals the deviceid of the first device in the order

    def __init__(self,
                 orderId,
                 orderTime,
                 arrivedTime,
                 product,
                 productId,
                 amount,
                 orderedByPerson,
                 orderedByOrg,
                 retailer,
                 orderNumber):

        self.orderId = orderId
        self.orderTime = orderTime
        self.arrivedTime = arrivedTime
        self.product = product
        self.productId = productId
        self.amount = amount
        self.orderedByPerson = orderedByPerson
        self.orderedByOrg = orderedByOrg
        self.retailer = retailer
        self.orderNumber = orderNumber
        return

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


