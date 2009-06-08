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
Order page with helper classes of Device Management
"""

### Imports

import mx.DateTime
import psycopg2

try:
    from mod_python import util
except:
    pass # To allow use of pychecker

import nav.db.manage
from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate

from nav.web.devicemanagement.constants import *
from nav.web.devicemanagement.common import *
from nav.web.devicemanagement import db as dtTables
from nav.web.devicemanagement.formattedlist import FormattedList
from nav.web.devicemanagement.history import *
from nav.web.devicemanagement.page import Page
from nav.web.devicemanagement.widget import Widget

### Functions

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
                '/seeddb/product/edit/')]
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
    else:
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

    sequence = ('deviceorderid','deviceorder_deviceorderid_seq')
    orderid = insertFields(fields,'deviceorder',sequence)

    # Create devices
    fields = {}
    fields['productid'] = formData[CN_PRODUCT]
    fields['deviceorderid'] = orderid
    fields['active'] = 'false'

    for i in range(0,int(formData[CN_AMOUNT])):
        insertFields(fields,'device')

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
                    except psycopg2.IntegrityError:
                        page.errors.append("A device with the serial '%s' " %\
                                           serialList[i] +\
                                           "already exists in the database")
            if count == 1:
                page.messages.append('Registered ' + str(count) + ' device')
            else:
                page.messages.append('Registered ' + str(count) + ' devices')
    else:
        page.errors.append('All devices from this order are already registered')

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
