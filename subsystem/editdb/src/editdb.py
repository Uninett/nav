#################################################
## editdb.py

#################################################
## Imports

from mod_python import util,apache
from editdbSQL import *
from socket import gethostbyaddr

import editTables,nav.Snmp

import sys,re,copy,initBox

#################################################
## Constants

BASEPATH = '/editdb/'

EDITPATH = [('Frontpage','/'),('Tools','/toolbox'),('Edit database','/editdb')]

ADDNEW_ENTRY = 'addnew_entry'
UPDATE_ENTRY = 'update_entry'
IGNORE_BOX = 'ignore_this_box'

IMG_SYNTAXOK = '/images/lys/green.png'
IMG_SYNTAXERROR = '/images/lys/red.png'

#################################################
## Templates

from editdbTemplate import editdbTemplate

#################################################
## Functions

def handler(req):
    path = req.uri
    request = re.search('editdb/(.+)$',path).group(1)
    request = request.split('/')

    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)

    output = None
    showHelp = False
    if len(request) == 2:
        if request[0] == 'help':
            showHelp = True
            request = []
            
    if not len(request) > 1:
        output = index(req,showHelp)
    else:
        editid = None
        if len(request) == 3:
            editid = request[2]

        table = request[0]
        action = request[1]
        output = handleSubmit(req,table,action,editid)

    if output:
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND

def index(req,showHelp=False):
    " Shows the index page "

    # Empty body
    class body:
        def __init__(self):
            pass
    
    body.title = 'Modify seed information for the NAV database'
    body.infotext = 'Here you can add, delete or edit seed information ' +\
                    'that are needed for the NAV database. Keep in mind ' +\
                    'that most of the data in  the NAV database are ' +\
                    'collected automatically by NAV background processes.'
    body.showHelp = showHelp
    body.help = [BASEPATH + 'help/','Show help']
    body.nohelp = [BASEPATH,'Hide help']
    
    body.tables = []
    headings = []
    
    # Table for boxes and services
    rows = [['Boxes',
             'Input seed information on the IP-devices you want to ' +\
             'monitor',
            [BASEPATH + 'netbox/edit','Add'],
            [BASEPATH + 'netbox/list','Edit'],
            [BASEPATH + 'bulk/netbox','Bulk import']],
            ['Services',
             'Which services on which servers do you want to monitor?',
            [BASEPATH + 'service/edit','Add'],
            [BASEPATH + 'service/list','Edit'],
            [BASEPATH + 'bulk/service','Bulk import']]]
    body.tables.append(Table('Boxes and services','',headings,rows))

    # Table for rooms and locations 
    rows = [['Room',
             'Register all wiring closets and server rooms that contain ' +\
             'boxes NAV monitors',
            [BASEPATH + 'room/edit','Add'],
            [BASEPATH + 'room/list','Edit'],
            [BASEPATH + 'bulk/room','Bulk import']],
            ['Location',
             'Rooms are organised in locations',
            [BASEPATH + 'location/edit','Add'],
            [BASEPATH + 'location/list','Edit'],
            [BASEPATH + 'bulk/location','Bulk import']]]
    body.tables.append(Table('Rooms and locations','',headings,rows))

    # Table org and usage cat
    rows = [['Organisation',
             'Register all organisational units that are relevant. I.e. ' +\
             'all units that have their own subnet/server facilities.',
            [BASEPATH + 'org/edit','Add'],
            [BASEPATH + 'org/list','Edit'],
            [BASEPATH + 'bulk/org','Bulk import']],
            ['User categories',
            'NAV encourages a structure in the subnet structure. ' +\
             'Typically a subnet has users from an organisational ' +\
             'unit. In addition this may be subdivided into a ' +\
             'category of users, i.e. students, employees, ' +\
             'administration etc.',
            [BASEPATH + 'usage/edit','Add'],
            [BASEPATH + 'usage/list','Edit'],
            [BASEPATH + 'bulk/usage','Bulk import']]]
    body.tables.append(Table('Organisation and user categories','',
                             headings,rows))

    # Table for types, products and vendors
    rows = [['Type',
             'The type describes the type of network device, uniquely ' +\
             'described from the SNMP sysobjectID',
            [BASEPATH + 'type/edit','Add'],
            [BASEPATH + 'type/list','Edit'],
            [BASEPATH + 'bulk/type','Bulk import']],
            ['Product',
             'Similar to type, but with focus on the product number and ' +\
             'description. A product may be a type, it may also be a ' +\
             'component (i.e. module) within an equipment type',
            [BASEPATH + 'product/edit','Add'],
            [BASEPATH + 'product/list','Edit'],
            [BASEPATH + 'bulk/product','Bulk import']],
            ['Vendor',
             'Register the vendors that manufacture equipment that are ' +\
             'represented in your network.',
            [BASEPATH + 'vendor/edit','Add'],
            [BASEPATH + 'vendor/list','Edit'],
            [BASEPATH + 'bulk/vendor','Bulk import']]]
    body.tables.append(Table('Types, products and vendors','',headings,rows))

    # Table for vlans and special subnets
    rows = [['Vlan',
             'Register the vlan number that are in use (this info may ' +\
             'also be derived automatically from the routers)',
            [BASEPATH + 'vlan/edit','Add'],
            [BASEPATH + 'vlan/list','Edit'],
            [BASEPATH + 'bulk/vlan','Bulk import']],
            ['Prefix',
             'Register special ip prefixes. Typically reserved prefixes ' +\
             'or prefixes that are not directly connected to monitored ' +\
             'routers/firewalls fall into this category',
            [BASEPATH + 'prefix/edit','Add'],
            [BASEPATH + 'prefix/list','Edit'],
            [BASEPATH + 'bulk/prefix','Bulk import']]]
    body.tables.append(Table('Vlans and special subnets','',headings,rows))

    nameSpace = {'editList': None, 'editForm': None, 'body': body}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = [('Frontpage','/'),
                     ('Tools','/toolbox'),
                     ('Edit database',None)]
    return template.respond()

# A general class for html tables
class Table:
    def __init__(self,title,infotext,headings,rows):
        self.title = title
        self.infotext = infotext
        self.headings = headings
        self.rows = rows

# Function for handling all submits
def handleSubmit(req, table, action, editid):
    error = None
    if editid:
        selected = [editid]
    else:
        selected = []
    
    # Make a list of selected entries (list of ids)
    if req.form.has_key(selectList.cnameChk):
        if type(req.form[selectList.cnameChk]) is str:
            # only one selected
            selected = [req.form[selectList.cnameChk]]
        elif type(req.form[selectList.cnameChk]) is list:
            # more than one selected
            for s in req.form[selectList.cnameChk]:
                selected.append(s)

    if action == 'edit':
        if req.form.has_key(selectList.cnameEdit):
            if not selected:
                error = 'No entries selected for editing'
                action = 'list' 
        elif req.form.has_key(selectList.cnameDelete):
            action = 'delete'
            if not selected:
                error = 'No entries selected'
                action = 'list'
        else:
            if not selected:
                action = 'add'

    if table == 'location':
        output = editLocation(req,selected,action,error)
    elif table == 'room':
        output = editRoom(req,selected,action,error)
    elif table == 'org':
        output = editOrg(req,selected,action,error)
    elif table == 'type':
        output = editType(req,selected,action,error)
    elif table == 'vendor':
        output = editVendor(req,selected,action,error)
    elif table == 'netbox':
        output = editNetbox(req,selected,action,error)
    elif table == 'usage':
        output = editUsage(req,selected,action,error)
    elif table == 'bulk':
        output = bulkImport(req,action)
    return output

def bulkImportParse(input,table,separator):
    commentChar = '#'
    # Any number of spaces followed by a # is a comment
    comment = re.compile('\s*%s' % commentChar)

    # list of (parsed correctly,data/error)
    parsed = []

    linenr = 0
    for line in input:
        linenr += 1    
        if comment.match(line):
            # This line is a comment
            pass
        elif len(line) > 0:
            fields = re.split(separator,line)
            if not len(fields) == table.num_fields:
                status = False
                data = 'Incorrect number of fields'
            else:
                d = {}
                status = True
                for i in range(0,len(table.fields)):
                    # fieldname,maxlen,required,use
                    fn,ml,req,use = table.fields[i]
                    # missing required field?
                    if req and not len(fields[i]):
                        status = False
                        data = "Required field '" + fn + "' missing"                                  # max field length exceeded?
                    if ml and (len(fields[i]) > ml):
                        status = False
                        data = "Field '" + fn + "' exceeds max field length"
                    # use this field if no syntax error (status==true)
                    # and if it's marked to be used (use == true)
                    if (status == True) and (use == True):
                        d[fn] = fields[i] 
            if status == True:
                data = d
            else:
                data = {'error': data}
            parsed.append((status,data,line,linenr))
    return parsed
            
def bulkImport(req,action):
    # form
    form = editForm()
    form.action = BASEPATH + 'bulk/'
    form.title = 'Bulk import'
    form.textConfirm = 'Preview import'
    form.enctype = 'multipart/form-data'
    form.add(editboxBulk())
    # list
    list = None

    help = """# Rows starting with '#' are comments 
# Select a file to import from, or write here
# For field syntax, select an import type """

    # direct link to a specific table?
    if action:
        if action == 'location':
            help = '# Syntax:\n# locationid:description'
        elif action == 'netbox':
            help = '# Syntax:\n# ip:roomid:orgid:catid:subcat:ro:rw'
            
        form.editboxes[0].fields['table'][0].value = action
    form.editboxes[0].fields['textarea'][0].value = help

    # form  submitted?
    if req.form.has_key(form.cnameConfirm) and len(req.form['table']):
        if len(req.form['file'].value):
            input = req.form['file'].value
            input = input.split('\n')
        else:
            input = req.form['textarea']
            input = input.split('\n')
        # strip cr
        i = []
        for line in input:
            i.append(line.strip('\r'))
        input = i

        if req.form['separator'] == 'colon':
            sep = ':'
        elif req.form['separator'] == 'scolon':
            sep = ';'
        elif req.form['separator'] == 'comma':
            sep = ','

        if req.form['table'] == 'location':
            d = bulkdefLocation()
        elif req.form['table'] == 'room':
            d = bulkdefRoom()
        elif req.form['table'] == 'netbox':
            d = bulkdefNetbox()
        parsed = bulkImportParse(input,d,sep)

        rows = []
        for p in parsed:
            syntax,data,line,linenr = p
            if syntax:
                row = [('<IMG src="' + IMG_SYNTAXOK + '">',False),
                       (linenr,False),
                       (line,False),
                       ('',False)]
            else:
                row = [('<IMG src="' + IMG_SYNTAXERROR + '">',False),
                       (linenr,False),
                       (line,False),
                       ('Syntax error: ' + data['error'],False)]
            rows.append((data,row)) 

        # show list
        list = selectList()
        list.isBulkList = True
        list.hiddenIdValue = req.form['table']
        list.headings = ['','Line','Input','Remark']
        list.rows = rows
        form = None
    elif req.form.has_key(selectList.cnameBulkConfirm):
        # import confirmed after preview
        table = req.form[selectList.cnameHiddenId]
        result = bulkInsert(req,table)

    nameSpace = {'editList': list, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    return template.respond()

#Function for bulk inserting
def bulkInsert(req,table):
    data = []
    if table == 'location':    
        if type(req.form['locationid']) is str:
            row = []
            row.append(('locationid',req.form['locationid']))
            row.append(('descr',req.form['descr'])) 
            data.append(row)
        else:
            for i in range(0,len(req.form['locationid'])):
                row = []
                row.append(('locationid',req.form['locationid'][i]))
                row.append(('descr',req.form['descr'][i]))
                data.append(row)
    if table == 'netbox':
       
        if type(req.form['ip']) is str:
            # Create empty device
            d = editTables.Device()
            d.hw_ver = 'dummy'
            d.save()
            deviceid = d.deviceid
            
            sysname = gethostbyaddr(req.form['ip'])[0]

            row = []
            row.append(('ip',req.form['ip']))
            row.append(('roomid',req.form['roomid'])) 
            row.append(('orgid',req.form['orgid']))
            row.append(('catid',req.form['catid'])) 
            row.append(('subcat',req.form['subcat']))
            row.append(('ro',req.form['ro'])) 
            row.append(('rw',req.form['rw']))
            row.append(('deviceid',str(deviceid)))
            row.append(('sysname',sysname))
            data.append(row)
        else:
            for i in range(0,len(req.form['ip'])):
                # Create empty device
                d = editTables.Device()
                d.hw_ver = 'dummy'
                d.save()
                deviceid = d.deviceid
                
                sysname = gethostbyaddr(req.form['ip'][i])[0]

                row = []
                row.append(('ip',req.form['ip'][i]))
                row.append(('roomid',req.form['roomid'][i])) 
                row.append(('orgid',req.form['orgid'][i]))
                row.append(('catid',req.form['catid'][i])) 
                row.append(('subcat',req.form['subcat'][i]))
                row.append(('ro',req.form['ro'][i])) 
                row.append(('rw',req.form['rw'][i]))
                row.append(('deviceid',str(deviceid)))
                row.append(('sysname',sysname))
                data.append(row)

    result = addEntryBulk(data,table)
    return result    

# Function for handling listing and editing of rooms
def editRoom(req,selected,action,error=None):
    table = 'room'
    idfield = 'roomid'
    templatebox = editboxRoom()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'room/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.editdbRoom
    editList.tablename = 'room'
    editList.orderBy = 'roomid'
    editList.idcol = 'roomid'
    editList.columns = [('Room Id','roomid',True),
                        ('Location','location',False),
                        ('Description','descr',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                addEntry(req,templatebox,table)
                form.status = "Added new room '" + req.form['roomid'] + "'"
                action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected = updateEntry(req,templatebox,table,idfield)
                form.status = 'Updated'
                action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected room(s) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        if len(selected)>1:
            form.title = 'Edit rooms'
        else:
            form.title = 'Edit room'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxRoom(s))
        editList = None
    elif action == 'add':
        form.title = 'Add new room'
        form.textConfirm = 'Add room'
        form.add(editboxRoom())
        editList = None
    elif action == 'delete':
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected room(s)?'
        editList.action = BASEPATH + 'room/edit/'
        editList.fill()
    elif action == 'list':
        editList.title = 'Edit rooms'
        editList.action = BASEPATH + 'room/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    return template.respond()

# Function for handling listing and editing of locations
def editLocation(req,selected,action,error=None):
    table = 'location'
    idfield = 'locationid'
    templatebox = editboxLocation()
    # Define form
    form = editForm()
    form.action = BASEPATH + 'location/edit/'

    # Define list
    editList = selectList()
    editList.table = editTables.editdbLocation
    editList.tablename = 'location'
    editList.orderBy = 'locationid'
    editList.idcol = 'locationid'
    editList.columns = [('Location ID','locationid',True),
                        ('Description','descr',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                addEntry(req,templatebox,table)
                form.status = "Added new location '" + req.form['locationid'] + "'"
                action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected = updateEntry(req,templatebox,table,idfield)
                form.status = 'Updated'
                action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected locations deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        if len(selected)>1:
            form.title = 'Edit locations'
        else:
            form.title = 'Edit location'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxLocation(s))
        editList = None
    elif action == 'add':
        form.title = 'Add new location'
        form.textConfirm = 'Add location'
        form.add(editboxLocation())
        editList = None
    elif action == 'delete':
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected location(s)?'
        editList.action = BASEPATH + 'location/edit/'
        editList.fill()
    elif action == 'list':
        editList.title = 'Edit locations'
        editList.action = BASEPATH + 'location/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    return template.respond()

# Function for handling listing and editing of organisations
def editOrg(req,selected,action,error=None):
    table = 'org'
    idfield = 'orgid'
    templatebox = editboxOrg()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'org/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.Org
    editList.tablename = 'org'
    editList.orderBy = 'orgid'
    editList.idcol = 'orgid'
    editList.columns = [('Org Id','orgid',True),
                        ('Parent','parent',False),
                        ('Description','descr',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                addEntry(req,templatebox,table)
                form.status = "Added new org '" + req.form['orgid'] + "'"
                action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected = updateEntry(req,templatebox,table,idfield)
                form.status = 'Updated'
                action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected organisation(s) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        if len(selected)>1:
            form.title = 'Edit organisations'
        else:
            form.title = 'Edit organisation'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxOrg(s))
        editList = None
    elif action == 'add':
        form.title = 'Add new organisation'
        form.textConfirm = 'Add'
        form.add(editboxOrg())
        editList = None
    elif action == 'delete':
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected organisation(s)?'
        editList.action = BASEPATH + 'org/edit/'
        editList.fill()
    elif action == 'list':
        editList.title = 'Edit organisations'
        editList.action = BASEPATH + 'org/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    return template.respond()

# Function for handling listing and editing of types
def editType(req,selected,action,error=None):
    table = 'type'
    idfield = 'typeid'
    templatebox = editboxType()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'type/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.Type
    editList.tablename = 'type'
    editList.orderBy = 'typename'
    editList.idcol = 'typeid'
    editList.columns = [('Type','typename',True),
                        ('Vendor','vendor',False),
                        ('Description','descr',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                addEntry(req,templatebox,table)
                form.status = "Added new type '" + req.form['typename'] + "'"
                action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected = updateEntry(req,templatebox,table,idfield)
                form.status = 'Updated'
                action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected type(s) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        if len(selected)>1:
            form.title = 'Edit types'
        else:
            form.title = 'Edit type'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxType(s))
        editList = None
    elif action == 'add':
        form.title = 'Add new type'
        form.textConfirm = 'Add'
        form.add(editboxType())
        editList = None
    elif action == 'delete':
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected type(s)?'
        editList.action = BASEPATH + 'type/edit/'
        editList.fill()
    elif action == 'list':
        editList.title = 'Edit types'
        editList.action = BASEPATH + 'type/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    return template.respond()

# Function for handling listing and editing of vendors
def editVendor(req,selected,action,error=None):
    table = 'vendor'
    idfield = 'vendorid'
    templatebox = editboxVendor()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'vendor/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.editdbVendor
    editList.tablename = 'vendor'
    editList.orderBy = 'vendorid'
    editList.idcol = 'vendorid'
    editList.columns = [('Vendor','vendorid',True)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                addEntry(req,templatebox,table)
                form.status = "Added new vendor '" + req.form['vendorid'] + "'"
                action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected = updateEntry(req,templatebox,table,idfield)
                form.status = 'Updated'
                action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected vendor(s) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        if len(selected)>1:
            form.title = 'Edit vendors'
        else:
            form.title = 'Edit vendor'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxVendor(s))
        editList = None
    elif action == 'add':
        form.title = 'Add new vendor'
        form.textConfirm = 'Add'
        form.add(editboxVendor())
        editList = None
    elif action == 'delete':
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected vendor(s)?'
        editList.action = BASEPATH + 'vendor/edit/'
        editList.fill()
    elif action == 'list':
        editList.title = 'Edit vendors'
        editList.action = BASEPATH + 'vendor/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    return template.respond()


def insertNetbox(ip,catid,roomid,orgid,
                 ro,rw,deviceid,serial=None,
                 subcatlist=None,function=None):

    if not deviceid:
        # Make new device first
        if len(serial):
            fields = {'serial': serial}
        else:
            # Don't insert an empty serialnumber (as serialnumbers must be
            # unique in the database)
            fields = {}
        deviceid = addEntryFields(fields,
                                  'device',
                                  ('deviceid','device_deviceid_seq'))

    # Make new netbox
    # Lookup sysname, if not found in dns, sysname = ip
    try:
        sysname = gethostbyaddr(ip)[0]
    except:
        sysname = ip

    fields = {'ip': ip,
              'roomid': roomid,
              'deviceid': deviceid,
              'sysname': sysname,
              'catid': catid,
              'orgid': orgid,
              'ro': ro,
              'rw': rw}

    netboxid = addEntryFields(fields,
                              'netbox',
                              ('netboxid','netbox_netboxid_seq'))
    # If subcatlist and function is given, insert them
    if subcatlist:
        if type(subcatlist) is list:
            for sc in subcatlist:
                fields = {'netboxid': netboxid,
                          'category': sc}
                addEntryFields(fields,'netboxcategory')
        else:
            fields = {'netboxid': netboxid,
                      'category': subcatlist}
            addEntryFields(fields,'netboxcategory')


    if function:
        fields = {'netboxid': netboxid,
                  'key': '',
                  'var': 'function',
                  'val': function}
        addEntryFields(fields,'netboxinfo')

def updateNetbox(req):
    formdata = {}
    idlist = []
    if type(req.form[UPDATE_ENTRY]) is list:
        # editing several entries
        # j is incremented for each category = server
        for i in range(0,len(req.form[UPDATE_ENTRY])):
            entry = {}
            editid = req.form[UPDATE_ENTRY][i]
            idlist.appen(editid)
            entry['ip'] = req.form['ip'][i]
            entry['catid'] = req.form['catid'][i]
            entry['roomid'] = req.form['roomid'][i]
            entry['orgid'] = req.form['orgid'][i]
            entry['ro'] = req.form['ro'][i]
            entry['rw'] = req.form['rw'][i]
            if req.form['catid'][i] == 'SRV':
                if req.form.has_key(editid+'subcat'):
                    entry['subcat'] = req.form[editid+'subcat']
                    entry['function'] = req.form[editid+'function']
            formdata[editid] = entry
    else:
        # editing just one entry
        entry = {}
        editid = req.form[UPDATE_ENTRY]
        idlist = [editid]
        entry['ip'] = req.form['ip']
        entry['catid'] = req.form['catid']
        entry['roomid'] = req.form['roomid']
        entry['orgid'] = req.form['orgid']
        entry['ro'] = req.form['ro']
        entry['rw'] = req.form['rw']
        if req.form['catid'] == 'SRV':
            if req.form.has_key(editid+'subcat'):
                entry['subcatlist'] = req.form[editid+'subcat']
                entry['function'] = req.form[editid+'function']
        formdata[editid] = entry

    for updateid,data in formdata.items():
        # Remove any entries in netboxcategory
        deleteEntry([updateid],'netboxcategory','netboxid')

        # If there exists a 'function' entry in netboxinfo, remove this
        deleteEntry([updateid],'netboxinfo','netboxid',"var='function'")

        # If category = server, add netboxcategories and function
        if data['catid'] == 'SRV' and data.has_key('subcatlist'):
            # If subcatlist and function is given, insert them
            if data['subcatlist']:
                if type(data['subcatlist']) is list:
                    for sc in data['subcatlist']:
                        fields = {'netboxid': updateid,
                                  'category': sc}
                        addEntryFields(fields,'netboxcategory')

                else:
                    fields = {'netboxid': updateid,
                              'category': data['subcatlist']}
                    addEntryFields(fields,'netboxcategory')

            if data['function']:
                fields = {'netboxid': updateid,
                          'key': '',
                          'var': 'function',
                          'val': data['function']}
                addEntryFields(fields,'netboxinfo')

        # Get new sysname (might have changed,hm)
        try:
            sysname = gethostbyaddr(data['ip'])[0]
        except:
            sysname = data['ip']

        # Update other fields
        fields = {'ip': data['ip'],
                  'sysname': sysname,
                  'catid': data['catid'],
                  'roomid': data['roomid'],
                  'orgid': data['orgid'],
                  'ro': data['ro'],
                  'rw': data['rw']}
        updateEntryFields(fields,'netbox','netboxid',updateid)
    return idlist

def addNetbox(req,templateform):
    action = 'add'

    # Is this a server?
    server = False
    if req.form['catid'] == 'SRV':
        server = True

    if req.form.has_key(editForm.CNAME_CONFIRM_SERIAL):
        # User has pressed "Continue"
        subcatlist = None
        function = None
        if server and req.form.has_key('subcat'):
            subcatlist = req.form['subcat']
            function = req.form['function']

        try:
            insertNetbox(req.form['ip'],
                         req.form['catid'],
                         req.form['roomid'],
                         req.form['orgid'],
                         req.form['ro'],
                         req.form['rw'],
                         deviceid = None,
                         serial = req.form['serial'],
                         subcatlist = subcatlist,
                         function = function)
            templateform.status = 'Added new box'
        except Exception,e:
            templateform.error = 'Error: ' + repr(type(e)) + ' ' + repr(e.args)
    else:
        if len(req.form['ro']):
            # Got read community
            try:
                box = initBox.Box(req.form['ip'],req.form['ro'])
                if box:
                    # getDeviceId() cannot return more than one id since
                    # the database doesn't support it (serial must be unique)
                    # this must be updated if the db is updated
                    deviceId = str(box.getDeviceId()[0])
                    if not deviceId:
                        if box.serial:
                            templateform = editForm(editForm.CNAME_CONFIRM_SERIAL)
                            templateform.action = BASEPATH + 'netbox/edit'
                            templateform.add(editboxNetboxSerial(gotRo=True,
                                             serial=box.serial))
                            if server:
                                templateform.add(editboxNetboxServer())
                            templateform.add(editboxNetbox(formData=req.form))
                            action = 'serial' 
                        else:
                            templateform.error = 'No device, no serial'
                    else:
                        # Found this device in the database
                        # insert the netbox
                        try:
                            insertNetbox(req.form['ip'],
                                         req.form['catid'],
                                         req.form['roomid'],
                                         req.form['orgid'],
                                         req.form['ro'],
                                         req.form['rw'],
                                         deviceid = deviceId)
                            templateform.status = 'Device found in database,'+\
                                                  ' added new box'
                        except Exception,e:
                            templateform.error = 'Error: ' + \
                                                 repr(type(e)) + ' ' + \
                                                 repr(e.args)
                else:
                    templateform.error = 'No box from initBox'
            except nav.Snmp.TimeOutException,e:
                templateform.error = repr(e)
        else:
            # Didn't get read community, ask for serial
            templateform = editForm(editForm.CNAME_CONFIRM_SERIAL)
            templateform.action = BASEPATH + 'netbox/edit'
            templateform.add(editboxNetboxSerial(gotRo=False))
            if server:
                templateform.add(editboxNetboxServer())
            templateform.add(editboxNetbox(formData=req.form))
            action = 'serial' 

    return (action,templateform)


# Function for handling listing and editing of netboxes
def editNetbox(req,selected,action,error=None):
    table = 'netbox'
    idfield = 'netboxid'
    templatebox = editboxNetbox()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'netbox/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.editdbNetbox
    editList.tablename = 'netbox'
    editList.orderBy = 'sysname'
    editList.idcol = 'netboxid'
    editList.columns = [('Sysname','sysname',True),
                        ('IP','ip',False),
                        ('Category','catid',False),]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm) or \
        req.form.has_key(editForm.CNAME_CONFIRM_SERIAL):

        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(editForm.CNAME_CONFIRM_SERIAL):
                (action,form) = addNetbox(req,form)
            elif req.form.has_key(ADDNEW_ENTRY):
                # add new netbox
                (action,form) = addNetbox(req,form)
            elif req.form.has_key(UPDATE_ENTRY):
                #error,selected = updateEntry(req,templatebox,table,idfield)
                selected = updateNetbox(req)
                action = 'edit'
                form.status = 'Updated'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected box(es) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        if len(selected)>1:
            form.title = 'Edit boxes'
        else:
            form.title = 'Edit box'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxNetbox(s))
            # Check if this is a server, if it is then show server fields
            if editTables.Netbox(s).cat.catid == 'SRV':
                form.add(editboxNetboxServer(s))
        editList = None
    elif action == 'serial':
        form.title = 'Register box'
        form.textConfirm = 'Continue'
        editList = None
    elif action == 'add':
        form.title = 'Register box'
        form.textConfirm = 'Add'
        form.add(editboxNetbox())
        editList = None
    elif action == 'delete':
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected box(es)?'
        editList.action = BASEPATH + 'netbox/edit/'
        editList.fill()
    elif action == 'list':
        editList.title = 'Edit boxes'
        editList.action = BASEPATH + 'netbox/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = templatebox.path
    return template.respond()

# Function for handling listing and editing of user categories
def editUsage(req,selected,action,error=None):
    table = 'usage'
    idfield = 'usageid'
    templatebox = editboxUsage()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'usage/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.Usage
    editList.tablename = 'usage'
    editList.orderBy = 'usageid'
    editList.idcol = 'usageid'
    editList.columns = [('Usage category','usageid',True),
                        ('Description','descr',True)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                addEntry(req,templatebox,table)
                form.status = "Added new usage category '" + req.form['usageid'] + "'"
                action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected = updateEntry(req,templatebox,table,idfield)
                form.status = 'Updated'
                action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected usage categories deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        if len(selected)>1:
            form.title = 'Edit usage categories'
        else:
            form.title = 'Edit usage categories'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxUsage(s))
        editList = None
    elif action == 'add':
        form.title = 'Add new usage category'
        form.textConfirm = 'Add'
        form.add(editboxUsage())
        editList = None
    elif action == 'delete':
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected usage categories?'
        editList.action = BASEPATH + 'usage/edit/'
        editList.fill()
    elif action == 'list':
        editList.title = 'Edit usage categories'
        editList.action = BASEPATH + 'usage/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    return template.respond()



# Class representing a form, used by the template
class editForm:
    # For the template
    method = 'post'
    action = None
    title = None
    error = None
    status = None
    backlink = None
    enctype = 'application/x-www-form-urlencoded'

    # Text and controlname
    textConfirm = None
    cnameConfirm = 'form_confirm'

    CNAME_CONFIRM_SERIAL = 'cname_confirm_serial'

    # List of editboxes to display
    editboxes = []

    def __init__(self,cnameConfirm=None):
        if cnameConfirm:
            self.cnameConfirm = cnameConfirm
 
        self.editboxes = []

    def add(self,box):
       self.editboxes.append(box)

class inputText:
    type = 'text'
    name = None
    value = ''
    def __init__(self,value='',size=22):
        self.value = value
        self.size = str(size)

class inputSelect:
    type = 'select'
    name = None
    value = ''
    def __init__(self,options=None,table=None):
        self.options = options

        if table:
            self.options = table.getOptions() 

class inputMultipleSelect:
    type = 'multipleselect'
    name = None
    value = []
    def __init__(self,options=None,table=None):
        self.options = options

        if table:
            self.options = table.getOptions() 

class inputFile:
    type = 'file'
    name = None
    value = ''
    def __init__(self):
        pass

class inputTextArea:
    type = 'textarea'
    name = None
    value = ''

    def __init__(self,rows=20,cols=80):
        self.rows = rows
        self.cols = cols


class inputCheckbox:
    type = 'checkbox'
    name = None
    value = False

    def __init__(self):
        self.value = None

class editbox:
    type = None
    boxName = ADDNEW_ENTRY
    boxId = 0

    def fill(self):
        " Fill this form from the database "
        entry = self.table(self.editId)

        self.boxName = UPDATE_ENTRY
        self.boxId = self.editId

        for fieldname,desc in self.fields.items():
            desc[0].value = getattr(entry,fieldname)

    def setControlNames(self):
        " Set controlnames for the inputs to the fieldnames "
        for fieldname,desc in self.fields.items():
            desc[0].name = fieldname

    def hasMissing(self,req):
        """
        Check if any of the required fields are missing in the req.form
        Returns the name the first missing field, or False
        Note: keep_blank_values must be True or empty fields won't
              be present in the form 
        """
        missing = False
        try:
            for field,desc in self.fields.items():
                if type(req.form[field]) is list:
                    # the field is a list, several entries have been edited
                    for each in req.form[field]:
                        if not len(each) and desc[1]:
                            raise Exception(field)
                else:
                    if not len(req.form[field]) and desc[1]:
                        raise Exception(field)
        except Exception, field:
            (missing,) = field.args
        return missing
   
class editboxRoom(editbox):
    type = 'room'
    table = editTables.editdbRoom
            
    def __init__(self,editId=None):
        # Field definitions {field name: [input object, required]}
        f = {'roomid': [inputText(),True],
             'locationid': [inputSelect(table=editTables.editdbLocation),True],
             'descr': [inputText(),False],
             'opt1': [inputText(),False],
             'opt2': [inputText(),False],
             'opt3': [inputText(),False],
             'opt4': [inputText(),False]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

class editboxLocation(editbox):
    type = 'location'
    table = editTables.Location
            
    def __init__(self,editId=None):
        # Field definitions {field name: [input object, required]}
        f = {'locationid': [inputText(),True],
             'descr': [inputText(),False]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

class editboxOrg(editbox):
    type = 'org'
    table = editTables.editdbOrg
            
    def __init__(self,editId=None):
        # Field definitions {field name: [input object, required]}
        o = [('','No parent')]
        for option in self.table.getOptions():
            o.append(option)

        f = {'orgid': [inputText(),True],
             'parent': [inputSelect(options=o),False],
             'descr': [inputText(),False],
             'opt1': [inputText(),False],
             'opt2': [inputText(),False],
             'opt3': [inputText(),False]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

class editboxType(editbox):
    type = 'type'
    table = editTables.editdbType
            
    def __init__(self,editId=None):
        # Field definitions {field name: [input object, required]}
        f = {'typename': [inputText(),True],
             'vendorid': [inputSelect(table=editTables.editdbVendor),True],
             'descr': [inputText(),False],
             'typegroupid': [inputSelect(table=editTables.editdbTypegroup),True],
             'sysobjectid': [inputText(),True],
             'cdp': [inputCheckbox(),True],
             'tftp': [inputCheckbox(),True],
             'frequency': [inputText(),False]}

        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

class editboxVendor(editbox):
    type = 'vendor'
    table = editTables.editdbVendor
            
    def __init__(self,editId=None):
        # Field definitions {field name: [input object, required]}
        f = {'vendorid': [inputText(),True]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

class editboxUsage(editbox):
    type = 'usage'
    table = editTables.Usage
            
    def __init__(self,editId=None):
        # Field definitions {field name: [input object, required]}
        f = {'usageid': [inputText(),True],
             'descr': [inputText(),True]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

class editboxNetboxSerial(editbox):
    type = 'netboxserial'

    def __init__(self,gotRo,serial=''):
        if gotRo:
            if serial:
                self.help = 'Serialnumber retrieved, but no device with ' + \
                            'this serialnumber found in the database. ' + \
                            'If you continue, a new device with this ' + \
                            'serial will be created.'
            else:
                self.help = 'Unable to retrieve serialnumber for this ' + \
                            'device. Enter a serialnumber, or leave blank ' + \
                            'if you don\'t want to register a serial ' +\
                            'for this device.'
        else:
                self.help = 'Unable to retrieve serialnumber since no RO ' +\
                            'community was specified. Enter a serialnumber, ' +\
                            'or leave ' +\
                            'blank if you don\'t want to register a serial '+\
                            'for this device.'

        self.fields = {'serial': [inputText(value=serial),True]}
        self.setControlNames()

class editboxNetboxServer(editbox):
    type = 'netboxserver'
    editId = None

    def __init__(self,editId=None):
        if editId:
            self.editId = editId
            self.help = None
        else:
            # Only show help if we're adding a new box
            self.help = 'You have selected category \'server\'. ' +\
                        'For boxes that are servers, you can select one or ' +\
                        'more subcategories, and enter a description of the ' +\
                        'server\'s function.'

        o = [('AD','AD'),
             ('ADC','ADC'),
             ('BACKUP','BACKUP'),
             ('DNS','DNS'),
             ('FS','FS'),
             ('LDAP','LDAP'),
             ('MAIL','MAIL'),
             ('NOTES','NOTES'),
             ('STORE','STORE'),
             ('TEST','TEST'),
             ('UNIX','UNIX'),
             ('UNIX-STUD','UNIX-STUD'),
             ('WEB','WEB'),
             ('WIN','WIN'),
             ('WIN-STUD','WIN-STUD')]

        if editId:
            # tag fieldnames with the id
            self.fields = {editId + 'subcat': [inputMultipleSelect(options=o),
                                              False],
                           editId + 'function': [inputText(size=40),False]}
        else:
            self.fields = {'subcat': [inputMultipleSelect(options=o),False],
                           'function': [inputText(size=40),False]}
        self.setControlNames()

        if editId:
            # The editboxNetbox has UPDATE_ENTRY, so ignore this
            self.boxName = IGNORE_BOX

            # Get selected netboxcategories
            sql = "SELECT category FROM netboxcategory WHERE netboxid='%s'" \
            % (editId,)
            res = executeSQLreturn(sql)
            selected = []
            for s in res:
               selected.append(s[0])
            self.fields[editId+'subcat'][0].value = selected

            # Get var 'function' from netboxinfo
            sql = "SELECT val FROM netboxinfo WHERE netboxid='%s' " \
                  % (editId,) + \
                  "AND var='function'"
            res = executeSQLreturn(sql)
            if res:
                self.fields[editId+'function'][0].value = res[0][0]


class editboxNetbox(editbox):
    type = 'netbox'
    table = editTables.editdbNetbox
    editId = None

    def __init__(self,editId=None,formData=None):
        if editId:
            self.sysname = editTables.Netbox(editId).sysname
            self.editId = editId
            self.path = EDITPATH + [('Boxes','/editdb/netbox/list'),
                                    ('Edit',False)]
        else:
            self.path = EDITPATH + [('Boxes','/editdb/netbox/list'),
                                    ('Add',False)]
 
        o = [(None,'Select an organisation')]
        for org in editTables.Org.getAllIterator(orderBy='orgid'):
            o.append((org.orgid,org.orgid + ' (' + org.descr + ')'))

        r = [(None,'Select a room')]
        for room in editTables.Room.getAllIterator(orderBy='roomid'):
            r.append((room.roomid,room.roomid + ' (' + room.descr + ')'))

        c = [(None,'Select a category')]
        for cat in editTables.Cat.getAllIterator(orderBy='catid'):
            c.append((cat.catid,cat.catid + ' (' + cat.descr + ')'))

        # Field definitions {field name: [input object, required]}
        f = {'ip': [inputText(),True],
             'catid': [inputSelect(options=c),True],
             'orgid': [inputSelect(options=o),True],
             'roomid': [inputSelect(options=r),True],
             'ro': [inputText(),False],
             'rw': [inputText(),False]}
        self.fields = f
        self.setControlNames()

        if formData:
            # Fill this editbox with data from the form
            # This is used by intermediate steps (like register serial)
            # to remember fieldvalues
            for field,definition in self.fields.items():
                if formData.has_key(field):
                    definition[0].value = formData[field]
            
        if editId:
            # This box is for editing an existing netbox with id = editId
            self.editId = editId
            self.fill()
 
class editboxBulk(editbox):
    type = 'bulk'
    
    def __init__(self):
        tables = [('','Select an import type'),
                  ('location','Locations'),
                  ('room','Rooms'),
                  ('org','Organisations'),
                  ('type','Types'),
                  ('vendor','Vendors'),
                  ('netbox','Boxes'),
                  ('service','Services')]

        sep = [('colon','Colon (:)'),
               ('scolon','Semicolon (;)'),
               ('comma','Comma (,)')]

        f = {'table': [inputSelect(options=tables),False],
             'separator': [inputSelect(options=sep),False],
             'file': [inputFile(),False],
             'textarea': [inputTextArea(),False]}
        self.fields = f
        self.setControlNames()

# Classes describing the fields for bulk import
class bulkdefLocation:
    # number of fields
    num_fields = 2

    syntax = 'locationid:descr'

    # list of (fieldname,max length,not null,use field)
    fields = [('locationid',12,True,True),
              ('descr',0,True,True)]

class bulkdefRoom:
    # number of fields
    num_fields = 7

    syntax = 'roomid:locationid:descr:opt1:opt2:opt3:opt4'

    # list of (fieldname,max length,not null,use field)
    fields = [('roomid',10,True,True),
              ('locationid',12,False,True),
              ('descr',0,False,True),
              ('opt1',0,False,True),
              ('opt2',0,False,True),
              ('opt3',0,False,True),
              ('opt4',0,False,True)]

class bulkdefNetbox:
    " Used to parse netboxes "    
    table = 'netbox'
    # number of fields
    num_fields = 7

    syntax = 'ip:serial:roomid:orgid:catid:ro:rw'

    # list of (fieldname,max length,not null,use field)
    fields = [('ip',0,True,True),
              ('roomid',0,True,True),
              ('orgid',10,True,True),
              ('catid',8,True,True),
              ('subcat',0,False,True),
              ('ro',0,True,True),
              ('rw',0,False,True)]

class bulkdefNetboxOld:
    " Used to parse old nettel.txt seed files " 
    table = 'netbox'
    syntax = 'roomid:ip:orgid:catid:subcat:ro:rw:funksjon'

    # number of fields
    num_fields = 8

     # list of (fieldname,max length,not null,use field)
    fields = [('roomid',10,True,True),
              ('ip',0,True,True),
              ('orgid',10,True,True),
              ('catid',8,True,True),
              ('subcat',0,False,True),
              ('ro',0,False,True),
              ('rw',0,False,True),
              ('funksjon',0,False,False)]
    # 'funksjon' is deprecated so use field = False

# Class representing a list of entries, used by the template
class selectList:
    # Text and controlnames for the action bar
    textAdd = 'Add new'
    textEdit = 'Edit selected'
    textDelete = 'Delete selected'
    cnameAdd = 'submit_add'
    cnameEdit = 'submit_edit'
    cnameDelete = 'submit_delete'
    cnameChk = 'checkbox_id'
    # Delete controls
    cnameDeleteConfirm = 'confirm_delete'
    textDeleteConfirm = 'Delete'
    # Bulk controls
    cnameBulkConfirm = 'confirm_bulk'
    textBulkConfirm = 'Import'
    # Hidden id control
    cnameHiddenId = 'hidden_id'

    def __init__(self):
        # bulk confirm list?
        self.isBulkList = False
        self.hiddenIdValue = None
        # is this a confirm delete list?
        self.isDeleteList = False
        # list of entries to delete
        self.deleteList = []
        # For the template
        self.method = 'post'
        self.action = None
        self.error = None
        self.status = None
        self.backlink = None

        # Variables that must be filled before passing to the template
        self.title = None
        self.headings = []
        self.rows = []

        # Variables used by fill()
        self.table = None
        self.idcol = None
        self.orderBy = None
        self.tablename = ''

    def fill(self):
        " Fill the headings and rows lists "
    
        # fill headings
        self.headings = []
        if not self.isDeleteList:
            self.headings = ['Select']
        for heading,column,link in self.columns:    
            self.headings.append(heading)

        # fill rows
        entries = []
        if not self.isDeleteList:
            entries = self.table.getAllIterator(orderBy=self.orderBy)
        else:
            for id in self.deleteList:
                entries.append(self.table(id))

        for entry in entries:
            id = getattr(entry,self.idcol)

            row = []
            for heading,column,link in self.columns:
                if link:
                    eid = id
                    if not type(eid) is str:
                        eid = str(id)
                    row.append((getattr(entry,column),BASEPATH + self.tablename + '/edit/' + eid))
                else:
                    row.append((getattr(entry,column),None))
            self.rows.append((id,row))

