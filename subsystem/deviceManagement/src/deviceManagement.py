"""
$Id$

This file id part of the NAV project.

This module contains all the functions and custom classes used 
by the deviceTracker, and is also the default handler.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
"""

#################################################
## Imports

import nav.db,deviceManagementTables,mx.DateTime,re,forgetSQL

from mod_python import util,apache
from nav.web.templates.deviceManagementTemplate import deviceManagementTemplate
#from miscUtils import memberoforg
from nav.web.TreeSelect import TreeSelect,Select,UpdateableSelect,Option
from nav.web import urlbuilder,SearchBox


#################################################
## Constants (read from config file)

# fix, s&r dtTables
dtTables = deviceManagementTables
BASEPATH = '/devicemanagement/'
DATEFORMAT = '%d-%m-%Y'
TIMEFORMAT = '%d-%m-%Y %H:%M'
INFINITY = mx.DateTime.DateTime(999999,12,31,0,0,0)
DELETE_TIME_THRESHOLD = mx.DateTime.TimeDelta(hours=48)

#################################################
## Default handler

def handler(req):
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)
    path = req.uri.split(BASEPATH)[1]
    path = path.split('/')

    if path[0] == 'order':
        if not path[1]:
            output = order(req)
        elif path[1] == 'add':
            output = addOrder(req)
        elif path[1] == 'register':
            output = registerOrder(req,path[2])
    elif path[0] == 'browse':
        if path[1] == 'history':
            output = browse(req,path[1])
        elif path[1] == 'error':
            output = browse(req,path[1])
        elif path[1] == 'rma':
            output = browse(req,path[1])
    elif path[0] == 'history':
        if path[1] == 'device':
            output = history(req,deviceId=path[2])
        elif path[1] == 'netbox':
            output = history(req,netboxId=path[2])
        else:
            output = browse(req,path[0])
    elif path[0] == 'register':
        output = register(req)
    elif path[0] == 'error':
        if path[1] == 'device':
            output = registerError(req,deviceId=path[2])
        else:
            output = browse(req,path[0])
    elif path[0] == 'delete':
        output = delete(req)
    elif path[0] == 'rma':
        if path[1] == 'device':
            if path[2]:
                output = registerRma(req,deviceId=path[2])
            else:
                output = registerRma(req)
        if path[1] == 'returned':
            if path[2]:
                rmaReturned(req,path[2])
            else:
                output = registerRma(req)
        if path[1] == 'returnednew':
            if path[2]:
                new = True
                rmaReturned(req,path[2],new)
            else:
                output = registerRma(req)
        else:
            output = registerRma(req)
    else:
        output = index(req)

    if output:
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND


def index(req):

    body = """
    <a href="browse/history/">Device history</a><br>
    <a href="order/">Orders (add new, register arrivals)</a><br>
    <a href="register/">Register new device (without adding an order)</a><br>
    <a href="browse/error/">Register error event</a><br>
    <a href="rma/">Register return of merchandise</a><br>
    <a href="delete/">Module delete</a><br>
    """

    args = {}
    args['body'] = body
    args['path'] = [('Home','/'),
                    ('Tools','/toolbox'),
                    ('Device Management',False)]
    args['title'] = 'Device Management'

    nameSpace = {'page': 'index', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = args['path']
    return template.respond()
    

def delete(req):
    """
    Manual module delete
    """
    args = {}
    args['path'] = [('Home','/'),
                    ('Tools','/toolbox'),
                    ('Device Management',BASEPATH),
                    ('Module delete',False)]

    timestamp = mx.DateTime.now() - DELETE_TIME_THRESHOLD
    where = 'downsince <' + str(psycopg.TimestampFromMx(timestamp))

    if req.form.has_key('cn_delete') and req.form.has_key('cn_moduleid'):
        if len(req.form['cn_moduleid']): 
            moduleId = req.form['cn_moduleid']
            module = dtTables.Module(moduleId)

            deviceId = module.device.deviceid

            # Create a deviceInOperation-end event
            # and post it to the eventq
            de = DeviceEvent(eventTypeId='deviceInOperation',
                             deviceId=deviceId)
            de.subId = moduleId
            de.addVar("username",req.session['user'].login)
            de.postEvent()
            # And delete the module
            module.delete()

    # Get modules which have been down for
    # longer than the threshold
    modules = dtTables.Module.getAll(where)
    deleteList = []
    for module in modules:
        deleteList.append((module.moduleid,
                           module.module,
                           module.netbox.sysname,
                           module.downsince.strftime(TIMEFORMAT)))

    args['action'] = BASEPATH + 'delete/'
    args['deleteList'] = deleteList
    args['threshold'] = str(DELETE_TIME_THRESHOLD.hours).split('.')[0]
    args['returnpath'] = {'url': BASEPATH,
                          'text': 'Return'}

    nameSpace = {'page': 'delete', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = args['path']
    return template.respond()

def browse(req,path):
    # Args holds everything for the template
    args = {}
    # Common path for all browse views
    args['path'] = [('Home','/'),
                    ('Tools','/toolbox'),
                    ('Device Management',BASEPATH)]

    # Make the searchbox
    searchbox = SearchBox.SearchBox(req,
                'Type a room id, an ip or a (partial) sysname')
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
    args['searchbox'] = searchbox
    sr = searchbox.getResults(req)
    
    args['action'] = BASEPATH + 'browse/' + path + '/'
    args['returnpath'] = {'url': BASEPATH,
                          'text': 'Return'}
    if path == 'rma':
        args['returnpath'] = {'url': BASEPATH + 'rma/',
                              'text': 'Return'}
 
    args['error'] = None
    selectbox = TreeSelect()
    args['formname'] = selectbox.formName

    multiple = False
    if path == 'history':
        multiple = True

    select = Select('cn_location',
                    'Location',
                    multiple = True,
                    multipleSize = 20,
                    initTable='Location', 
                    initTextColumn='descr',
                    initIdColumn='locationid',
                    preSelected = sr['locations'],
                    optionFormat = '$v ($d)',
                    orderByValue = True)

    select2 = UpdateableSelect(select,
                               'cn_room',
                               'Room',
                               'Room',
                               'descr',
                               'roomid',
                               'locationid',
                               multiple=True,
                               multipleSize=20,
                               preSelected = sr['rooms'],
                               optionFormat = '$v ($d)',
                               orderByValue = True)

    select3 = UpdateableSelect(select2,
                               'cn_netbox',
                               'Box',
                               'Netbox',
                               'sysname',
                               'netboxid',
                               'roomid',
                               multiple=multiple,
                               multipleSize=20,
                               preSelected = sr['netboxes'])

    select4 = UpdateableSelect(select3,
                               'cn_module',
                               'Module',
                               'Module',
                               'module',
                               'moduleid',
                               'netboxid',
                               multiple=multiple,
                               multipleSize=20,
                               onchange='',
                               optgroupFormat = '$d') 
    # onchange='' since this doesn't update anything

    selectbox.addSelect(select)
    selectbox.addSelect(select2)
    selectbox.addSelect(select3)
    selectbox.addSelect(select4)

    validSelect = False
    
    # Update the selectboxes based on form data
    selectbox.update(req.form)
    # Not allowed to go on, unless at least a netbox is selected
    if len(select3.selectedList):
        validSelect = True

    # View history clicked?
    deviceHistList = []
    if req.form.has_key('cn_submit_history'):
        if req.form.has_key('cn_module'):
            # one or more modules selected
            if len(req.form['cn_module']):
                modules = req.form['cn_module']
                if type(modules) is str:
                    # only one selected, convert str to list
                    modules = [modules] 
                # get deviceid for these modules
                for moduleid in modules:
                    deviceid = dtTables.Module(moduleid).device.deviceid
                    deviceHistList.append(History(deviceid,moduleId=moduleid))
                args['returnpath'] = {'url': BASEPATH + 'history/',
                                      'text': 'Return'}
        elif req.form.has_key('cn_netbox'):
            # one or more netboxes selected            
            if len(req.form['cn_netbox']):
                netboxes = req.form['cn_netbox']
                if type(netboxes) is str:
                    # only one selected, convert str to list
                    netboxes = [netboxes] 
                # get deviceid for these netboxes
                for netboxid in netboxes:
                    deviceid = dtTables.Netbox(netboxid).device.deviceid
                    deviceHistList.append(History(deviceid,netboxId=netboxid))
                args['returnpath'] = {'url': BASEPATH + 'history/',
                                      'text': 'Return'}
    # Register error clicked?
    errorDevice = None
    if req.form.has_key('cn_submit_error'):
        if req.form.has_key('cn_module'):
            if len(req.form['cn_module']):
                moduleid = req.form['cn_module']
                deviceid = dtTables.Module(moduleid).device.deviceid
                # Uses History(), should have been a Device() class
                # (subclass of forgetSQL.Device())
                errorDevice = History(deviceid,moduleId=moduleid)
        elif req.form.has_key('cn_netbox'):
            if len(req.form['cn_netbox']):
                netboxid = req.form['cn_netbox']
                deviceid = dtTables.Netbox(netboxid).device.deviceid
                errorDevice = History(deviceid,netboxId=netboxid)
        args['action'] = BASEPATH + 'error/device/' + str(deviceid)
       
    rmaDevice = None 
    # Register rma clicked?
    if req.form.has_key('cn_submit_rma'):
        if req.form.has_key('cn_module'):
            moduleid = req.form['cn_module']
            deviceid = dtTables.Module(moduleid).device.deviceid
            rmaDevice = History(deviceid,moduleId=moduleid)
        elif req.form.has_key('cn_netbox'):
            netboxid = req.form['cn_netbox']
            deviceid = dtTables.Netbox(netboxid).device.deviceid
            rmaDevice = History(deviceid,netboxId=netboxid)
        args['action'] = BASEPATH + 'rma/device/' + str(deviceid)

    # Submit buttons, title and path for the different views
    if path == 'history':
        args['path'].append(('View history',False))
        args['title'] = 'View history - select a box or a module'
        args['submit'] = {'control': 'cn_submit_history',
                          'value': 'View history',
                          'enabled': validSelect}
    elif path == 'error':
        args['path'].append(('Register error',False))
        args['title'] = 'Register error - select a box or a module'
        args['submit'] = {'control': 'cn_submit_error',
                          'value': 'Register error',
                          'enabled': validSelect}
    elif path == 'rma':
        args['path'].append(('Register RMA',False))
        args['title'] = 'Register RMA - select a box or a module'
        args['submit'] = {'control': 'cn_submit_rma',
                          'value': 'Register RMA',
                          'enabled': validSelect}

    args['selectbox'] = selectbox
    args['deviceHistList'] = deviceHistList
    args['errorDevice'] = errorDevice
    args['rmaDevice'] = rmaDevice

    nameSpace = {'page': 'browse', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    template.path = args['path']
    return template.respond()

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

def registerError(req,deviceId=None):
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

   
def history(req,deviceId):
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

def order(req):
    args = {}
    args['path'] = [('Home','/'),
                    ('Tools','/toolbox'),
                    ('Device Management',BASEPATH),
                    ('Order management',False)]

    alerthist = dtTables.AlerthistDt
    where = ["eventtypeid='deviceOrdered'"]
    allOrders = {}
    for oe in alerthist.getAllIterator(where,orderBy='start_time'):
        if not allOrders.has_key(oe.subid):
            # first time we see this order
            allOrders[oe.subid] = [1,oe]
        else:
            if oe.end_time == INFINITY:
                # This is an active order
                # If at least one of the order events are still active,
                # the whole order is listed as active
                allOrders[oe.subid][1] = oe
            # increase amount by one
            allOrders[oe.subid][0] += 1

    activeOrders = []
    oldOrders = []
    for key,value in allOrders.items():
        amount = value[0]
        oe = value[1]

        # Get variables from the Alerthistvar table
        usernameOrdered = oe.getVar('username',state='s')
        orgId = oe.getVar('orgid',state='s')
        dealer = oe.getVar('dealer',state='s')
        orderNr = oe.getVar('orderid',state='s')
        usernameRegistered = oe.getVar('username',state='e')

        o = Order(oe.subid,
                  oe.start_time.strftime(DATEFORMAT),
                  oe.end_time.strftime(DATEFORMAT),
                  oe.device.product.vendor.vendorid + ' ' + 
                  oe.device.product.productno,
                  oe.device.product.productid,
                  amount,
                  usernameOrdered,
                  orgId,
                  dealer,
                  orderNr)

        if (oe.end_time == INFINITY):
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
    args['action'] = BASEPATH + 'order/add'
    args['error'] = ''

    # submit button pressed?
    if form.has_key('cn_submit'):
        if form.has_key('cn_number'):
            try:
                ci_number = int(form['cn_number'])
            except ValueError:
                ci_number = 0
            if ci_number > 0:
                ci_prodid = form['cn_prodid']
                ci_orgid = form['cn_org']
                ci_dealer = form['cn_dealer']
                ci_ordernr = form['cn_ordernr']

                connection = nav.db.getConnection('devicemanagement','manage')
                database = connection.cursor()
                firstDevice = True
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
                    de = DeviceEvent(eventTypeId='deviceOrdered',deviceId=deviceId)
                    de.subId = orderId
                    de.state = DeviceEvent.STATE_START
                    # variables
                    username = req.session['user'].login
                    vars = {'username': username,
                            'orgid': ci_orgid,
                            'dealer': ci_dealer,
                            'orderid': ci_ordernr}
                    de.addVars(vars)
                    de.postEvent()

                connection.close()
                redirect(req,BASEPATH + 'order/')
            else:
                args['error'] = 'Number must be larger than zero'
        else:
            args['error'] = 'You must enter a number'
    

    # make list of orgs and products for the selects
    orgs = dtTables.Org()
    orgList = []
    where = memberoforg(req)
    for org in orgs.getAllIterator(where):
        orgList.append((org.orgid,org.descr))
    args['orgList'] = orgList
    
    products = dtTables.Product()
    productList = []
    for product in products.getAllIterator():
        productList.append((product.productid,product.vendor.vendorid + ' ' + \
        product.productno,product.descr))
    args['productList'] = productList
    args['returnpath'] = {'url': BASEPATH + 'order/',
                          'text': 'Return to order overview'}

    nameSpace = {'page': 'addOrder', 'args': args}
    template = deviceManagementTemplate(searchList=[nameSpace])
    return template.respond()


def registerOrder(req,orderId):
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
            if type(states) is str:
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

def register(req):
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

class DeviceEvent:
    """
    An event which can be added to the eventq
    """

    STATE_NONE = 'x'
    STATE_START = 's'
    STATE_END = 'e'
    
    source = 'deviceTracker'
    target = 'eventEngine'
    severity = 0

    deviceId = 'NULL'
    netboxId = 'NULL'
    subId = 'NULL'
    state = STATE_NONE
    start_time = None
    end_time = None

    def __init__(self,eventTypeId=None,deviceId=None):
        self.eventTypeId = eventTypeId
        self.deviceId = deviceId
        self.vars = {}

    def postEvent(self):
        connection = nav.db.getConnection('devicemanagement','manage')
        database = connection.cursor()

        # post event to eventq
        sql = """INSERT INTO eventq (source,target,deviceid,netboxid,subid,
        eventtypeid,state,severity) VALUES \
        ('%s','%s', %s, %s, %s, '%s', '%s' ,%s)""" %\
        (self.source, self.target, self.deviceId, self.netboxId, self.subId,\
        self.eventTypeId, self.state, self.severity)
        database.execute(sql)
        connection.commit()

        # get the new eventqid
        sql = "SELECT currval('eventq_eventqid_seq')"
        database.execute(sql)
        connection.commit()
        eventqId = int(database.fetchone()[0])

        # post eventvars to eventqvar
        for varName,value in self.vars.items():
            sql = "INSERT INTO eventqvar (eventqid,var,val) VALUES \
            (%s,'%s','%s')" %\
            (eventqId,varName,value)
            database.execute(sql)

        connection.commit()
        connection.close()

    def addVar(self, key, value):
        self.vars[key] = value

    def addVars(self, values):
        for key,value in values.items():
            self.vars[key] = value

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
                 dealer,
                 orderNumber):

        self.orderId = orderId
        self.orderTime = orderTime
        self.arrivedTime = arrivedTime
        self.product = product
        self.productId = productId
        self.amount = amount
        self.orderedByPerson = orderedByPerson
        self.orderedByOrg = orderedByOrg
        self.dealer = dealer
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
                             de.vars['dealer'])}
                        sort_key = de.start_time
                        self.addEvent(sort_key,e)
                    elif eventtype == 'deviceOrdered' and de.end_time != INFINITY:
                        # A deviceOrdered end event
                        # start
                        e = {'eventType': 'Ordered',
                             'time': de.start_time.strftime(DATEFORMAT),
                             'descr': 'Ordered by %s for %s from %s' %
                             (de.getVar('username','s'),de.getVar('orgid','s'),
                             de.getVar('dealer','s'))}
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


