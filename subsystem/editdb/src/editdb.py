#################################################
## editdb.py

#################################################
## Imports

from mod_python import util,apache
from editdbSQL import *
from socket import gethostbyaddr

import editTables,nav.Snmp,sys,re,copy,initBox
from nav.web.serviceHelper import getCheckers,getDescription
from nav.Snmp import TimeOutException

#################################################
## Constants

BASEPATH = '/editdb/'

EDITPATH = [('Frontpage','/'),('Tools','/toolbox'),('Edit database','/editdb')]

ADDNEW_ENTRY = 'addnew_entry'
UPDATE_ENTRY = 'update_entry'
IGNORE_BOX = 'ignore_this_box'

IMG_SYNTAXOK = '/images/lys/green.png'
IMG_SYNTAXERROR = '/images/lys/red.png'

# REQ_TRUE: a required field
# REQ_FALSE: not required
# REQ_NONEMPTY: not required, but don't insert empty field
REQ_TRUE = 1
REQ_FALSE = 2
REQ_NONEMPTY = 3

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
    rows = [['Subcategory',
             'The main categories of a device are predefined by NAV (i.e. ' +\
             'GW,SW,SRV). You may however create subcategories yourself.',
            [BASEPATH + 'subcat/edit','Add'],
            [BASEPATH + 'subcat/list','Edit'],
            [BASEPATH + 'bulk/subcat','Bulk import']],
            ['Organisation',
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
            None,
            [BASEPATH + 'vlan/list','Edit'],
            None],
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
    elif table == 'product':
        output = editProduct(req,selected,action,error)
    elif table == 'vendor':
        output = editVendor(req,selected,action,error)
    elif table == 'netbox':
        output = editNetbox(req,selected,action,error)
    elif table == 'usage':
        output = editUsage(req,selected,action,error)
    elif table == 'service':
        output = editService(req,selected,action,error)
    elif table == 'prefix':
        output = editPrefix(req,selected,action,error)
    elif table == 'vlan':
        output = editVlan(req,selected,action,error)
    elif table == 'subcat':
        output = editSubcat(req,selected,action,error)
    elif table == 'bulk':
        output = bulkImport(req,action)
    return output

def bulkImportParse(input,bulkdef,separator):
    commentChar = '#'
    # Any number of spaces followed by a # is a comment
    comment = re.compile('\s*%s' % commentChar)

    # list of (parsed correctly,data/error)
    parsed = []

    linenr = 0
    for line in input:
        linenr += 1    
        remark = None
        if comment.match(line):
            # This line is a comment
            pass
        elif len(line) > 0:
            fields = re.split(separator,line)
            data = {}
            if not len(fields) == bulkdef.num_fields:
                status = False
                remark = 'Incorrect number of fields'
            else:
                status = True
                for i in range(0,len(bulkdef.fields)):
                    # fieldname,maxlen,required,use
                    fn,ml,req,use = bulkdef.fields[i]
                    # missing required field?
                    if req and not len(fields[i]):
                        status = False
                        remark = "Syntax error: Required field '" + fn + \
                                 "' missing"
                        break
                    # max field length exceeded?
                    if ml and (len(fields[i]) > ml):
                        status = False
                        remark = "Syntax error: Field '" + fn + \
                                 "' exceeds max field length"
                        break
                    # if this is the id field, check if it's unique in the db
                    if fn == bulkdef.uniqueField:
                        where = bulkdef.uniqueField + "='" + fields[i] + "'"
                        result = bulkdef.table.getAllIDs(where=where)
                        if result:
                            status = False
                            remark = "Not unique: An entry with " + fn + \
                                     "=" + fields[i] + " already exists"
                            break
                    # check the validity of this field with the bulkdefs 
                    # checkValidity function this is for checking things 
                    # like: do ip resolve to a hostname for netbox?
                    (status,validremark) = bulkdef.checkValidity(fn,fields[i])
                    if validremark:
                        remark = validremark
                    if status == False:
                        break
                    # use this field if no syntax error (status==true)
                    # and if it's marked to be used (use == true)                    
                    if (status == True) and (use == True):
                        data[fn] = fields[i] 
            parsed.append((status,data,remark,line,linenr))
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

    help = "# Rows starting with a '#' are comments\n" + \
           "# Select a file to import from, or write here\n" + \
           "# For field syntax, select an import type\n"

    # Dict with the different bulk definitions
    bulkdef = {'location': bulkdefLocation,
               'room': bulkdefRoom,
               'netbox': bulkdefNetbox,
               'org': bulkdefOrg,
               'usage': bulkdefUsage,
               'service': bulkdefService,
               'vendor': bulkdefVendor,
               'subcat': bulkdefSubcat,
               'type': bulkdefType,
               'product': bulkdefProduct,
               'prefix': bulkdefPrefix}

    # direct link to a specific table?
    if action:
        if bulkdef.has_key(action):
            help = bulkdef[action].syntax
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

        separator = req.form['separator']
        table = req.form['table']
        parsed = bulkImportParse(input,bulkdef[table],separator)

        rows = []
        for p in parsed:
            status,data,remark,line,linenr = p
            if status:
                row = [(['<IMG src="' + IMG_SYNTAXOK + '">'],False),
                       ([linenr],False),
                       ([line],False),
                       ([remark],False)]
            else:
                row = [(['<IMG src="' + IMG_SYNTAXERROR + '">'],False),
                       ([linenr],False),
                       ([line],False),
                       ([remark],False)]
            rows.append((data,row)) 
            
        # show list
        list = selectList()
        list.isBulkList = True
        list.title = 'Preview import'
        list.hiddenIdValue = req.form['table']
        list.hiddenData = []
        for p in parsed:
            status,data,remark,line,linenr = p
            if status:
                list.hiddenData.append(line)
        list.headings = ['','Line','Input','Remark']
        list.rows = rows
        form = None
    elif req.form.has_key(selectList.cnameBulkConfirm):
        # import confirmed after preview
        table = req.form[selectList.cnameHiddenId]
        data = req.form[selectList.cnameHiddenData]
        result = bulkInsert(data,bulkdef[table])
        form.status = 'Inserted ' + str(result) + ' rows'

    nameSpace = {'editList': list, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = EDITPATH + [('Bulk import',False)]
    return template.respond()

#Function for bulk inserting
def bulkInsert(data,bulkdef):
    prerowlist = []
    # FIX:
    # THIS IS NOT NECESSARILY ':' !!
    separator = ':'

    if not type(data) is list:
        data = [data]

    for line in data:
        fields = re.split(separator,line)

        row = {}
        for i in range(0,len(bulkdef.fields)):
            # fieldname,maxlen,required,use
            field,ml,req,use = bulkdef.fields[i]
            row[field] = fields[i] 
        prerowlist.append(row)

    # Do table specific things with the data before insterting
    # (create missing devices for netboxes for example)
    if bulkdef.process:
        rowlist = []
        for row in prerowlist:
            row = bulkdef.preInsert(row)
            if row:
                rowlist.append(row)
    else:
        # do nothing, just insert it
        rowlist = prerowlist            

    addEntryBulk(rowlist,bulkdef.tablename)
    return len(rowlist)

# Function for handling listing and editing of rooms
def editRoom(req,selected,action,error=None):
    path = EDITPATH + [('Rooms',BASEPATH+'room/list'),('Add',False)]
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
                        ('Description','descr',False),
                        ('Optional 1','opt1',False),
                        ('Optional 2','opt2',False),
                        ('Optional 3','opt3',False),
                        ('Optional 4','opt4',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                error = addEntry(req,templatebox,table,unique='roomid')
                if not error:
                    editList.status = "Added room '" + req.form['roomid'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,
                                             idfield,unique='roomid')
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Room(s).roomid + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
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
        path = EDITPATH + [('Rooms',BASEPATH+'room/list'),('Edit',False)]
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
        form.add(editboxRoom(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Rooms',BASEPATH+'room/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected room(s)?'
        editList.action = BASEPATH + 'room/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Rooms',False)]
        editList.title = 'Edit rooms'
        editList.action = BASEPATH + 'room/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for handling listing and editing of locations
def editLocation(req,selected,action,error=None):
    path = EDITPATH + [('Locations',BASEPATH+'location/list'),('Add',False)]
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
                error = addEntry(req,templatebox,table,unique='locationid')
                if not error:
                    editList.status = "Added location '" + \
                                  req.form['locationid'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,
                                             idfield,unique='locationid')
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Location(s).locationid + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
                    action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected location(s) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        path = EDITPATH + [('Locations',BASEPATH+'location/list'),('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit locations'
        else:
            form.title = 'Edit location'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxLocation(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Locations',BASEPATH+'location/list'),('Add',False)]
        form.title = 'Add new location'
        form.textConfirm = 'Add location'
        form.add(editboxLocation(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Locations',BASEPATH+'location/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected location(s)?'
        editList.action = BASEPATH + 'location/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Locations',False)]
        editList.title = 'Edit locations'
        editList.action = BASEPATH + 'location/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for handling listing and editing of organisations
def editOrg(req,selected,action,error=None):
    path = EDITPATH + [('Organisations',BASEPATH+'org/list'),('Add',False)]
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
                        ('Description','descr',False),
                        ('Optional 1','opt1',False),
                        ('Optional 2','opt2',False),
                        ('Optional 3','opt3',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                error = addEntry(req,templatebox,table,unique='orgid')
                if not error:
                    editList.status = "Added org '" + req.form['orgid'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,
                                             idfield,unique='orgid')
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Org(s).orgid + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
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
        path = EDITPATH + [('Organisations',BASEPATH+'org/list'),('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit organisations'
        else:
            form.title = 'Edit organisation'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxOrg(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Organisations',BASEPATH+'org/list'),('Add',False)]
        form.title = 'Add new organisation'
        form.textConfirm = 'Add'
        form.add(editboxOrg(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Organisations',BASEPATH+'org/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected organisation(s)?'
        editList.action = BASEPATH + 'org/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Organisations',False)]
        editList.title = 'Edit organisations'
        editList.action = BASEPATH + 'org/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for handling listing and editing of types
def editType(req,selected,action,error=None):
    path = EDITPATH + [('Types',BASEPATH+'type/list'),('Add',False)]
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
    editList.orderBy = ['vendor','typename']
    editList.idcol = 'typeid'
    editList.columns = [('Vendor','vendor',False),
                        ('Typename','typename',True),
                        ('Description','descr',False),
                        ('Sysobjectid','sysobjectid',False),
                        ('Frequency','frequency',False),
                        ('cdp','cdp',False),
                        ('tftp','tftp',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                error = addEntry(req,templatebox,table,
                                 unique=['vendorid','typename'])
                if not error:
                    editList.status = "Added type '" + \
                                  req.form['typename'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,idfield,
                                             staticid=True,
                                             unique=['vendorid','typename'])
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Type(s).typename + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
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
        path = EDITPATH + [('Types',BASEPATH+'type/list'),('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit types'
        else:
            form.title = 'Edit type'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxType(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Types',BASEPATH+'type/list'),('Add',False)]
        form.title = 'Add new type'
        form.textConfirm = 'Add'
        form.add(editboxType(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Types',BASEPATH+'type/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected type(s)?'
        editList.action = BASEPATH + 'type/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Types',False)]
        editList.title = 'Edit types'
        editList.action = BASEPATH + 'type/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for handling listing and editing of products
def editProduct(req,selected,action,error=None):
    path = EDITPATH + [('Products',BASEPATH+'product/list'),('Add',False)]
    table = 'product'
    idfield = 'productid'
    templatebox = editboxProduct()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'product/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.editdbProduct
    editList.tablename = 'product'
    editList.orderBy = 'vendorid'
    editList.idcol = 'productid'
    editList.columns = [('Vendor','vendor',False),
                        ('Productno','productno',True),
                        ('Description','descr',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                error = addEntry(req,templatebox,table,
                                 unique=['productno','vendorid'])
                if not error:
                    editList.status = "Added product '" + \
                                  req.form['productno'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,idfield,
                                             staticid=True,
                                             unique=['productno','vendorid'])
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Product(s).productno + ' '  
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
                    action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected product(s) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        path = EDITPATH + [('Products',BASEPATH+'product/list'),('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit products'
        else:
            form.title = 'Edit products'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxProduct(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Products',BASEPATH+'product/list'),('Add',False)]
        form.title = 'Add new product'
        form.textConfirm = 'Add'
        form.add(editboxProduct(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Products',BASEPATH+'product/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected products(s)?'
        editList.action = BASEPATH + 'product/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Products',False)]
        editList.title = 'Edit products'
        editList.action = BASEPATH + 'product/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for handling listing and editing of vendors
def editVendor(req,selected,action,error=None):
    path = EDITPATH + [('Vendors',BASEPATH+'vendor/list'),('Add',False)]
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
                error = addEntry(req,templatebox,table,unique='vendorid')
                if not error:
                    editList.status = "Added vendor '" + \
                                  req.form['vendorid'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,idfield,
                                             unique='vendorid')
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Vendor(s).vendorid + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
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
        path = EDITPATH + [('Vendors',BASEPATH+'vendor/list'),('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit vendors'
        else:
            form.title = 'Edit vendor'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxVendor(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Vendors',BASEPATH+'vendor/list'),('Add',False)]
        form.title = 'Add new vendor'
        form.textConfirm = 'Add'
        form.add(editboxVendor(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Vendors',BASEPATH+'vendor/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected vendor(s)?'
        editList.action = BASEPATH + 'vendor/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Vendors',False)]
        editList.title = 'Edit vendors'
        editList.action = BASEPATH + 'vendor/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for adding new prefixes
def addPrefix(req):
    error = None
    data = {'nettype': req.form['nettype'],
            'orgid': req.form['orgid'],
            'usageid': req.form['usageid'],
            'description': req.form['description'],
            'netaddr': req.form['netaddr'],
            'netident': req.form['netident'],
            'vlan': req.form['vlannumber']}

    error = insertPrefix(data)
    return error

def insertPrefix(data):
    error = None
    # Is the entered cidr correct? 
    # regexp here

    # Add new vlan
    fields = {'nettype': data['nettype']}

    if len(data['orgid']):
        fields['orgid'] = data['orgid']
    if len(data['usageid']):
        fields['usageid'] = data['usageid']
    if len(data['description']):
        fields['description'] = data['description']
    if len(data['vlan']):
        fields['vlan'] = data['vlan']
    if len(data['netident']):
        fields['netident'] = data['netident']

    vlanid = addEntryFields(fields,
                            'vlan',
                            ('vlanid','vlan_vlanid_seq'))
    # Add new prefix
    fields = {'netaddr': data['netaddr'],
              'vlanid': vlanid}
    try:
        addEntryFields(fields,'prefix')
    except psycopg.ProgrammingError:
        # Invalid cidr
        error = 'Invalid CIDR'
        # Remove vlan entry
        deleteEntry([vlanid],'vlan','vlanid')
    except psycopg.IntegrityError:
        # Already existing cidr
        error = 'Prefix already present in database'
        deleteEntry([vlanid],'vlan','vlanid')
    return error

# Function for updating prefixes
def updatePrefix(req):
    error = None
    formdata = {}
    idlist = []
    if type(req.form[UPDATE_ENTRY]) is list:
        # editing several entries
        for i in range(0,len(req.form[UPDATE_ENTRY])):
            entry = {}
            editid = req.form[UPDATE_ENTRY][i]
            idlist.append(editid)
            entry['netaddr'] = req.form['netaddr'][i]
            entry['description'] = req.form['description'][i]
            entry['netident'] = req.form['netident'][i]
            entry['orgid'] = req.form['orgid'][i]
            entry['nettype'] = req.form['nettype'][i]
            entry['vlan'] = req.form['vlannumber'][i]
            entry['usageid'] = req.form['usageid'][i]
            formdata[editid] = entry
    else:
        # editing just one entry
        entry = {}
        editid = req.form[UPDATE_ENTRY]
        idlist = [editid]
        entry['netaddr'] = req.form['netaddr']
        entry['description'] = req.form['description']
        entry['netident'] = req.form['netident']
        entry['orgid'] = req.form['orgid']
        entry['nettype'] = req.form['nettype']
        entry['vlan'] = req.form['vlannumber']
        entry['usageid'] = req.form['usageid']
        formdata[editid] = entry

    for updateid,data in formdata.items():
        vlanfields = {'description': data['description'],
                      'netident': data['netident'],
                      'orgid': data['orgid'],
                      'nettype': data['nettype'],
                      'usageid': data['usageid']}

        if len(data['vlan']):
            vlanfields['vlan'] = data['vlan']

        prefixfields = {'netaddr': data['netaddr']}
      
        vlanid = editTables.Prefix(updateid).vlan.vlanid 
        updateEntryFields(vlanfields,'vlan','vlanid',str(vlanid))
        updateEntryFields(prefixfields,'prefix','prefixid',updateid)
    return (idlist,error)

# Function for handling listing and editing of prefixes
def editPrefix(req,selected,action,error=None):
    path = EDITPATH + [('Prefixes',BASEPATH+'prefix/list'),('Add',False)]
    table = 'prefix'
    idfield = 'prefixid'
    templatebox = editboxPrefix()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'prefix/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.editdbPrefixVlan
    editList.tablename = 'prefix'
    editList.orderBy = 'netaddr'
    editList.idcol = 'prefixid'
    editList.where = "vlan.nettype='static' or " + \
                     "vlan.nettype='reserved' or " + \
                     "vlan.nettype='scope'"
    editList.columns = [('Prefix/mask','netaddr',True),
                        ('Nettype','nettype',False),
                        ('Org','orgid',False),
                        ('Netident','netident',False),
                        ('Usage','usageid',False),
                        ('Description','description',False),
                        ('Vlan','vlannumber',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                error = addPrefix(req)
                if not error:
                    editList.status = "Added prefix '" + \
                                  req.form['netaddr'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updatePrefix(req)
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Prefix(s).netaddr + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
                    action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected prefix(es) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        path = EDITPATH + [('Prefixes',BASEPATH+'prefix/list'),('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit prefixes'
        else:
            form.title = 'Edit prefix'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxPrefix(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Prefixes',BASEPATH+'prefix/list'),('Add',False)]
        form.title = 'Add new prefix'
        form.textConfirm = 'Add'
        form.add(editboxPrefix(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Prefixes',BASEPATH+'prefix/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected ' + \
                         'prefix(es)?'
        editList.action = BASEPATH + 'prefix/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Prefixes',False)]
        editList.title = 'Edit prefixes'
        editList.action = BASEPATH + 'prefix/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for handling listing and editing of vlans
def editVlan(req,selected,action,error=None):
    path = EDITPATH + [('Vlan',BASEPATH+'vlan/list'),('Add',False)]
    table = 'vlan'
    idfield = 'vlanid'
    templatebox = editboxVlan()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'vlan/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.editdbVlan
    editList.tablename = 'vlan'
    editList.orderBy = ['vlan', 'nettype']
    editList.idcol = 'vlanid'
    editList.where = "nettype != 'static' and nettype != 'reserved' " + \
                     "and nettype != 'scope'"
    editList.columns = [('Vlan','vlan',True),
                        ('Netttype','nettype',True),
                        ('Organisation','orgid',False),
                        ('Usage','usage',False),
                        ('Netident','netident',False),
                        ('Description','description',False),
                        ('Prefixes',(editTables.Prefix,'vlanid','netaddr'),False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,idfield,
                                             staticid=True)
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += 'vlan ' + str(editTables.Vlan(s).vlan) + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
                    action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected prefix(es) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        path = EDITPATH + [('Vlans',BASEPATH+'vlan/list'),('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit vlans'
        else:
            form.title = 'Edit vlan'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxVlan(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Vlans',BASEPATH+'vlan/list'),('Add',False)]
        form.title = 'Add new vlan'
        form.textConfirm = 'Add'
        form.add(editboxVlan())
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Vlans',BASEPATH+'vlan/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected ' + \
                         'vlan(s)?'
        editList.action = BASEPATH + 'vlan/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Vlans',False)]
        editList.title = 'Edit vlans'
        editList.action = BASEPATH + 'vlan/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()


def insertNetbox(ip,sysname,catid,roomid,orgid,
                 ro,rw,deviceid,serial,
                 typeid,snmpversion,subcatlist=None,
                 function=None):

    if not deviceid:
        # Make new device first
        if len(serial):
            fields = {'serial': serial}
        else:
            # Don't insert an empty serialnumber (as serialnumbers must be
            # unique in the database) (ie. don't insert '' for serial)
            fields = {}
        deviceid = addEntryFields(fields,
                                  'device',
                                  ('deviceid','device_deviceid_seq'))

    fields = {'ip': ip,
              'roomid': roomid,
              'deviceid': deviceid,
              'sysname': sysname,
              'catid': catid,
              'orgid': orgid,
              'ro': ro,
              'rw': rw}

    if typeid:
        fields['typeid'] = typeid
    if snmpversion:
        # Only use the first char from initbox, can't insert eg. '2c' in
        # this field
        snmpversion = snmpversion[0]
        fields['snmp_version'] = snmpversion

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


def updateNetbox(req,templateform,selected):
    ADD_TYPE_URL = BASEPATH + 'type/edit/'
    STEP_1 = 1
    STEP_2 = 2
    STEP_3 = 3
    CNAME_STEP = 'step' 
    # Step0: ask for ip,ro,rw,catid,org,room
    # Step1: ask for serial (and sysname,snmpversion and typeid)
    # Step2: ask for subcategory and function
    # Step3: add the box
    message = "Got SNMP response, but can't find type in " + \
              "database. You must <a href=\"" + ADD_TYPE_URL + \
              "?sysobjectid=%s\" " + \
              "target=\"_blank\">add the " + \
              "type</a>  before proceeding (a new window will " + \
              "open, when the new type is added, press " + \
              "Continue to proceed)."

    box = None
    status = None
    action = 'predefined'
    form = req.form
    templateform.title = 'Edit box'
    # Preserve the URL
    templateform.action = BASEPATH + 'netbox/edit/' + selected

    # Add editbox with hidden values for step (and deviceid)
    editboxHidden = editboxHiddenOrMessage()
    templateform.add(editboxHidden)
    # What step are we in?
    step = STEP_1
    if form.has_key(CNAME_STEP):
        step = int(form[CNAME_STEP])
    nextStep = step + 1

    oldBox = editTables.editdbNetbox(selected)

    if step == STEP_1:
        # Look up sysname in DNS
        try:
            sysname = gethostbyaddr(form['ip'])[0]
        except:
            sysname = form['ip']

        # Check if (edited) ip is already present in db
        #if (oldBox.ip != form['ip']) or (oldBox.sysname != sysname):
        if oldBox.ip != form['ip']:
            # If IP differs from the old, then check for uniqueness
            error = None
            where = "ip = '" + form['ip'] + "'"
            box = editTables.Netbox.getAll(where)
            if box:
                error = 'IP already exists in database'
            if not error:
                # If IP isn't duplicate, check if (new) sysname is unique
                where = "sysname = '" + sysname + "'"
                box = editTables.Netbox.getAll(where)
                if box:
                    error = 'Sysname ' + sysname + ' (' + form['ip'] + \
                            ') already exists in database'
            if error:
                templateform.error = error
                templateform.add(editboxNetbox(editId=selected,formData=form))
                return (status,action,templateform)

        if editTables.Cat(form['catid']).req_snmp == True:
            # SNMP required by cat
            if len(form['ro']):
                # RO specified, check SNMP
                box = None
                try:
                    box = initBox.Box(form['ip'],form['ro'])
                except TimeOutException:
                    # No SNMP answer
                    templateform.error = 'No SNMP response, check RO community'
                    templateform.add(editboxNetbox(editId=selected,
                                                   formData=form))
                    return (status,action,templateform)
                except Exception, e:
                    # Other error (no route to host for example)
                    templateform.error = 'Error: ' + str(sys.exc_info()[0]) + \
                                         ': ' + str(sys.exc_info()[1])
                    templateform.add(editboxNetbox(editId=selected,
                                                   formData=form))
                    return (status,action,templateform)
     
                box.getDeviceId()
                templateform.add(editboxNetbox(editId=selected,
                                               formData=form,disabled=True))

                if box.typeid:
                    # Got type
                    if box.serial:
                        serial = box.serial
                    else:
                        serial = oldBox.device.serial
                    templateform.add(editboxNetboxSerial(
                                     gotRo=True,
                                     serial=serial,
                                     sysname=sysname,
                                     typeid=box.typeid,
                                     snmpversion=box.snmpversion,
                                     editSerial=False))
                    if box.serial:
                        # Got serial, go directly to step 2
                        step = STEP_2
                    else:
                        nextStep = STEP_2
                else:
                    # Couldn't find type, ask user to add
                    message = message % (box.sysobjectid,)
                    templateform.add(editboxHiddenOrMessage(message))
            else:
                # RO blank, return error
                templateform.error = 'Category ' + form['catid'] + \
                                     ' requires a RO community'
                templateform.add(editboxNetbox(editId=selected,formData=form))
                nextStep = STEP_1
        else:
            # SNMP not required by cat
            if len(form['ro']):
                # RO specified, check SNMP anyway
                box = None
                try:
                    box = initBox.Box(form['ip'],form['ro'])
                except TimeOutException:
                    templateform.error = 'Error: ' + str(sys.exc_info()[0]) + \
                                         ': ' + str(sys.exc_info()[1])
                    templateform.add(editboxNetbox(editId=selected,
                                                   formData=form))
                    return (action,templateform)
                except Exception, e:
                    # Other error (no route to host for example)
                    templateform.error = 'Error: ' + str(sys.exc_info()[0]) + \
                                         ': ' + str(sys.exc_info()[1])
                    templateform.add(editboxNetbox(editId=selected,
                                                   formData=form))
                    return (action,templateform)

                box.getDeviceId()
                templateform.add(editboxNetbox(editId=selected,
                                               formData=form,
                                               disabled=True))
                if box.typeid:
                    # Got type
                    if box.serial:
                        serial = box.serial
                    else:
                        serial = oldBox.device.serial
                    templateform.add(editboxNetboxSerial(gotRo=True,
                                     serial=serial,
                                     sysname=sysname,
                                     typeid=box.typeid,
                                     snmpversion=box.snmpversion,
                                     editSerial=False))
                    if box.serial:
                        # Got serial, go directly to step 2
                        step = STEP_2
                    else:
                        nextStep = STEP_2
                else:
                    # Unknown type, ask user to add
                    message = message % (box.sysobjectid,)
                    templateform.add(editboxHiddenOrMessage(message))
                    nextStep = STEP_1
            else:
                # RO blank, don't check SNMP, ask for serial
                templateform.add(editboxNetbox(editId=selected,
                                               formData=form,
                                               disabled=True))
                serial = oldBox.device.serial
                templateform.add(editboxNetboxSerial(gotRo=False,
                                                     serial = serial,
                                                     sysname=sysname,
                                                     editSerial=True))
                nextStep = STEP_2
    if step == STEP_2:
        # Always use the old serial
        serial = oldBox.device.serial
            
        if nextStep == STEP_3:
            # We didn't get here by skipping a step (ie. we didn't get
            # serialnumber by SNMP), so we must add the first two boxes
            templateform.add(editboxNetbox(editId=selected,
                                           formData=form,disabled=True))
            templateform.add(editboxNetboxSerial(gotRo=False,
                             serial=req.form['serial'],
                             sysname=req.form['sysname'],
                             typeid=req.form['typeid'],
                             snmpversion=req.form['snmpversion']))
        # If the serial was changed we have to check if it's unique
        if box:
            newSerial = box.serial
        else:
            newSerial = form['serial']

        if serial != newSerial:
            # Any other devices in the database with this serial?
            where = "serial = '" + str(newSerial) + "'"
            device = editTables.Device.getAll(where)
            if device:
                message = 'Can\'t update the serialnumber since another '+\
                          'device with this serial exists in ' + \
                          'the database.'
                templateform.add(editboxHiddenOrMessage(message))
                templateform.showConfirm = False
                return (status,action,templateform)

        # Show subcategory/function editbox 
        # If category has changed, then don't load the old subcatinfo
        if oldBox.catid != form['catid']:
            templateform.add(editboxNetboxCategory(req.form['catid'],
                                                   showHelp=False))
        else:
            templateform.add(editboxNetboxCategory(req.form['catid'],
                                                   selected))
        nextStep = STEP_3

    if step == STEP_3:
        subcatlist = None
        if form.has_key('subcat'):
            subcatlist = form['subcat']
            if not type(subcatlist) is list:
                subcatlist = [subcatlist]
        function = None
        if form.has_key('function'):
            function = req.form['function']
        typeId = None
        if form.has_key('typeid'):
            typeId = req.form['typeid']
        snmpversion = None
        if form.has_key('snmpversion'):
            snmpversion = form['snmpversion']
            # Only use first char of snmpversion, don't insert things like
            # '2c'
            snmpversion = snmpversion[0]

        # Update netbox
        fields = {'ip': form['ip'],
                  'sysname': form['sysname'],
                  'catid': form['catid'],
                  'roomid': form['roomid'],
                  'orgid': form['orgid'],
                  'ro': form['ro'],
                  'rw': form['rw']}

        if typeId:
            fields['typeid'] = typeId
        updateEntryFields(fields,'netbox','netboxid',selected)

        # Update device
        if form['serial'] != oldBox.device.serial:
            # Set new serial, if it has changed
            fields = {'serial': form['serial']}
            deviceId = str(oldBox.device.deviceid)
            updateEntryFields(fields,'device','deviceid',deviceId)

        # Remove old subcat and function entries
        netboxId = oldBox.netboxid
        deleteEntry([netboxId],'netboxcategory','netboxid')
        deleteEntry([netboxId],'netboxinfo','netboxid')

        # If subcatlist and function is given, insert them
        if subcatlist:
            for sc in subcatlist:
                fields = {'netboxid': netboxId,
                          'category': sc}
                addEntryFields(fields,'netboxcategory')

        if function:
            fields = {'netboxid': netboxId,
                      'key': '',
                      'var': 'function',
                      'val': function}
            addEntryFields(fields,'netboxinfo')

        action = 'list'
        status = 'Updated box ' + form['sysname'] + ' (' + \
                 form['ip'] + ')'

    if not step == STEP_3: 
        # Unless this is the last step, set the nextStep
        editboxHidden.addHidden(CNAME_STEP,nextStep) 
    return (status,action,templateform)

def addNetbox(req,templateform):
    ADD_TYPE_URL = BASEPATH + 'type/edit/'
    STEP_1 = 1
    STEP_2 = 2
    STEP_3 = 3
    CNAME_STEP = 'step' 
    # Step0: ask for ip,ro,rw,catid,org,room
    # Step1: ask for serial (and sysname,snmpversion and typeid)
    # Step2: ask for subcategory and function
    # Step3: add the box
    message = "Got SNMP response, but can't find type in " + \
              "database. You must <a href=\"" + ADD_TYPE_URL + \
              "?sysobjectid=%s\" " + \
              "target=\"_blank\">add the " + \
              "type</a>  before proceeding (a new window will " + \
              "open, when the new type is added, press " + \
              "Continue to proceed)."

    box = None
    status = None
    action = 'predefined'
    form = req.form
    templateform.title = 'Add box'

    # Add editbox with hidden values for step (and deviceid)
    editboxHidden = editboxHiddenOrMessage()
    templateform.add(editboxHidden)
    # What step are we in?
    step = STEP_1
    if form.has_key(CNAME_STEP):
        step = int(form[CNAME_STEP])
    nextStep = step + 1

    if step == STEP_1:
        # Look up sysname in DNS
        try:
            sysname = gethostbyaddr(form['ip'])[0]
        except:
            sysname = form['ip']

        # Check if sysname or ip is already present in db
        error = None
        where = "ip = '" + form['ip'] + "'"
        box = editTables.Netbox.getAll(where)
        if box:
            error = 'IP already exists in database'
        if not error:
            # If IP isn't duplicate, check sysname
            where = "sysname = '" + sysname + "'"
            box = editTables.Netbox.getAll(where)
            if box:
                error = 'Sysname ' + sysname + ' (' + form['ip'] + \
                        ') already exists in database'

        if error:
            templateform.error = error
            templateform.add(editboxNetbox(formData=form))
            return (status,action,templateform)

        if editTables.Cat(form['catid']).req_snmp == True:
            # SNMP required by cat
            if len(form['ro']):
                # RO specified, check SNMP
                box = None
                try:
                    box = initBox.Box(form['ip'],form['ro'])
                except TimeOutException:
                    # No SNMP answer
                    templateform.error = 'No SNMP response, check RO community'
                    templateform.add(editboxNetbox(formData=form))
                    return (status,action,templateform)
                except Exception, e:
                    # Other error (no route to host for example)
                    templateform.error = 'Error: ' + str(sys.exc_info()[0]) + \
                                         ': ' + str(sys.exc_info()[1])
                    templateform.add(editboxNetbox(formData=form))
                    return (status,action,templateform)
     
                box.getDeviceId()
                templateform.add(editboxNetbox(formData=form,disabled=True))
                if box.typeid:
                    # Got type
                    templateform.add(editboxNetboxSerial(
                                     gotRo=True,
                                     serial=box.serial,
                                     sysname=sysname,
                                     typeid=box.typeid,
                                     snmpversion=box.snmpversion))
                    if box.serial:
                        # Got serial, go directly to step 2
                        step = STEP_2
                    else:
                        nextStep = STEP_2
                else:
                    # Couldn't find type, ask user to add
                    message = message % (box.sysobjectid,)
                    templateform.add(editboxHiddenOrMessage(message))
                    nextStep = STEP_1
            else:
                # RO blank, return error
                templateform.error = 'Category ' + form['catid'] + \
                                     ' requires a RO community'
                templateform.add(editboxNetbox(formData=form))
                nextStep = STEP_1
        else:
            # SNMP not required by cat
            if len(form['ro']):
                # RO specified, check SNMP anyway
                box = None
                try:
                    box = initBox.Box(form['ip'],form['ro'])
                except TimeOutException:
                    templateform.error = 'No SNMP response, check RO community'
                    templateform.add(editboxNetbox(formData=form))
                    return (action,templateform)
                except Exception, e:
                    # Other error (no route to host for example)
                    templateform.error = 'Error: ' + str(sys.exc_info()[0]) + \
                                         ': ' + str(sys.exc_info()[1])
                    templateform.add(editboxNetbox(formData=form))
                    return (action,templateform)

                box.getDeviceId()
                templateform.add(editboxNetbox(formData=form,disabled=True))
                if box.typeid:
                    # Got type
                    templateform.add(editboxNetboxSerial(gotRo=True,
                                     serial=box.serial,
                                     sysname=sysname,
                                     typeid=box.typeid,
                                     snmpversion=box.snmpversion))
                    if box.serial:
                        # Got serial, go directly to step 2
                        step = STEP_2
                    else:
                        nextStep = STEP_2
                else:
                    # Unknown type, ask user to add
                    message = message % (box.sysobjectid,)
                    templateform.add(editboxHiddenOrMessage(message))
                    nextStep = STEP_1
            else:
                # RO blank, don't check SNMP, ask for serial
                templateform.add(editboxNetbox(formData=form,disabled=True))
                templateform.add(editboxNetboxSerial(gotRo=False,
                                                     sysname=sysname))
                nextStep = STEP_2
    if step == STEP_2:
        if box:
            # If we got here by skipping a step (ie. got serial by SNMP)
            # the serial isn't posted yet, but we still got the box object
            serial = box.serial
        else:
            serial = req.form['serial']
            
        if nextStep == STEP_3:
            # We didn't get here by skipping a step (ie. we didn't get
            # serialnumber by SNMP), so we must add the first two boxes
            templateform.add(editboxNetbox(formData=form,disabled=True))
            templateform.add(editboxNetboxSerial(gotRo=False,
                             serial=req.form['serial'],
                             sysname=req.form['sysname'],
                             typeid=req.form['typeid'],
                             snmpversion=req.form['snmpversion'],
                             formData=form))
        if len(serial):
            # Any devices in the database with this serial?
            where = "serial = '" + str(serial) + "'"
            device = editTables.Device.getAll(where)
            if device:
                # Found a device with this serial
                deviceId = device[0].deviceid
                # Must check if there already is a box with this serial
                where = "deviceid = '" + str(deviceId) + "'"
                box = editTables.Netbox.getAll(where)
                if box:
                    box = box[0]
                    message = 'A box with this serial already exists ' + \
                              '(' + box.sysname + ')'
                    templateform.add(editboxHiddenOrMessage(message))
                    #This doesn't work for some reason:
                    #templateform.add(editboxNetbox(box.netboxid,
                    #                               disabled=True))
                    templateform.showConfirm = False
                    return (status,action,templateform)
            else:
                # Not found, make new device
                deviceId = None
        else:
            # No serial specified
            deviceId = None
        editboxHidden.addHidden('deviceid',deviceId)

        # Show subcategory/function editbox 
        templateform.add(editboxNetboxCategory(req.form['catid']))
        nextStep = STEP_3

    if step == STEP_3:
        subcatlist = None
        if form.has_key('subcat'):
            subcatlist = form['subcat']
        function = None
        if form.has_key('function'):
            function = form['function']
        typeId = None
        if form.has_key('typeid'):
            typeId = form['typeid']
        snmpversion = None
        if form.has_key('snmpversion'):
            snmpversion = form['snmpversion']

        insertNetbox(form['ip'],form['sysname'],
                     form['catid'],form['roomid'],
                     form['orgid'],form['ro'],
                     form['rw'],form['deviceid'],
                     form['serial'],typeId,
                     snmpversion,subcatlist,
                     function)
        action = 'list'
        status = 'Added box ' + form['sysname'] + ' (' + \
                 form['ip'] + ')'

    if not step == STEP_3: 
        # Unless this is the last step, set the nextStep
        editboxHidden.addHidden(CNAME_STEP,nextStep) 
    return (status,action,templateform)

# Function for handling listing and editing of netboxes
def editNetbox(req,selected,action,error=None):
    path = EDITPATH + [('Boxes',BASEPATH+'netbox/list'),('Add',False)]
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
    editList.orderBy = ['roomid','sysname']
    editList.idcol = 'netboxid'
    editList.columns = [('Room','roomid',False),
                        ('Sysname','sysname',True),
                        ('IP','ip',False),
                        ('Category','catid',False),
                        ('Organisation','orgid',False),
                        ('RO','ro',False),
                        ('RW','rw',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                # add new netbox
                (status,action,form) = addNetbox(req,form)
                if action == 'list':
                    editList.status = status
            elif req.form.has_key(UPDATE_ENTRY):
                selected = selected[0]
                (status,action,form) = updateNetbox(req,form,selected)
                if action == 'list':
                    editList.status = status
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected box(es) deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'predefined':
        # Action is predefined by addNetbox() or updateNetbox()
        form.textConfirm = 'Continue'
        editList = None
    elif action == 'edit':
        path = EDITPATH + [('Boxes',BASEPATH+'netbox/list'),('Edit',False)]
        form.title = 'Edit box'
        form.textConfirm = 'Continue'
        # can only edit one
        selected = selected[0]
        form.add(editboxNetbox(selected))
        # preserve path
        form.action = BASEPATH + 'netbox/edit/' + selected
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Boxes',BASEPATH+'netbox/list'),('Add',False)]
        form.title = 'Add box'
        form.textConfirm = 'Continue'
        form.add(editboxNetbox(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Boxes',BASEPATH+'netbox/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected box(es)?'
        editList.action = BASEPATH + 'netbox/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Boxes',False)]
        editList.title = 'Edit boxes'
        editList.action = BASEPATH + 'netbox/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for handling listing and editing of user categories
def editUsage(req,selected,action,error=None):
    path = EDITPATH + [('Usage categories',BASEPATH+'usage/list'),
                       ('Add',False)]
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
                        ('Description','descr',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                error = addEntry(req,templatebox,table,unique='usageid')
                if not error:
                    editList.status = "Added usage category '" + \
                                  req.form['usageid'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,idfield,
                                             unique='usageid')
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Usage(s).usageid + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
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
        path = EDITPATH + [('Usage categories',BASEPATH+'usage/list'),
                           ('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit usage categories'
        else:
            form.title = 'Edit usage categories'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxUsage(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Usage categories',BASEPATH+'usage/list'),
                           ('Add',False)]
        form.title = 'Add new usage category'
        form.textConfirm = 'Add'
        form.add(editboxUsage(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Usage categories',BASEPATH+'usage/list'),
                           ('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected ' + \
                         'usage categories?'
        editList.action = BASEPATH + 'usage/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Usage categories',False)]
        editList.title = 'Edit usage categories'
        editList.action = BASEPATH + 'usage/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

def addService(req,form):
    action = 'add'
    # Check if all required serviceproperties are present
    properties = getDescription(req.form['handler'])
    missing = False
    if properties and properties.has_key('args'):
        for required in properties['args']:
            if not req.form.has_key(required):
                missing = required
            if req.form.has_key(required):
                if not len(req.form[required]):
                    missing = required

    if not missing:
        # Add service entry
        fields = {'netboxid': req.form['netboxid'],
                  'handler': req.form['handler']}
        serviceid = addEntryFields(fields,
                                  'service',
                                  ('serviceid','service_serviceid_seq'))
        # Add serviceproperty entries
        if properties:
            if properties.has_key('args'):
                for property in properties['args']:
                    # Already know that all properties in 'args' are present
                    fields = {'serviceid': serviceid,
                              'property': property,
                              'value': req.form[property]}
                    addEntryFields(fields,
                                   'serviceproperty')
                    action = 'list'
            if properties.has_key('optargs'):
                for property in properties['optargs']:
                    # optargs are optional, must check if they are present
                    if req.form.has_key(property):
                        if len(req.form[property]):
                            fields = {'serviceid': serviceid,
                                      'property': property,
                                      'value': req.form[property]}
                            addEntryFields(fields,
                                           'serviceproperty')
                            action = 'list'
    else:
        checker = req.form['handler']
        form = editForm(editForm.CNAME_CONTINUE)
        form.title = 'Add service'
        form.add(editboxService(formData=req.form,disabled=True))
        form.add(editboxServiceProperties(checker,req.form['netboxid']))
        form.textConfirm = 'Add service'
        form.error = "Missing required property '" + missing + "'"
        action = 'properties'
    return action,form

def updateService(req,form):
    action = 'edit'
    editId = req.form[UPDATE_ENTRY]
    # Check if all required serviceproperties are present
    handler = editTables.Service(editId).handler
    properties = getDescription(handler)
    missing = False
    if properties and properties.has_key('args'):
        for required in properties['args']:
            if not req.form.has_key(required):
                missing = required
            if req.form.has_key(required):
                if not len(req.form[required]):
                    missing = required

    if not missing:
        # Update service entry
        fields = {'netboxid': req.form['netboxid'],
                  'handler': handler}
        updateEntryFields(fields,'service','serviceid',editId)
        # Update serviceproperty entries
        if properties:
            # Delete old properties
            deleteEntry([editId],'serviceproperty','serviceid')
            if properties.has_key('args'):
                for property in properties['args']:
                    # Already know that all properties in 'args' are present
                    fields = {'serviceid': editId,
                              'property': property,
                              'value': req.form[property]}
                    addEntryFields(fields,'serviceproperty')
                    action = 'list'
            if properties.has_key('optargs'):
                for property in properties['optargs']:
                    # optargs are optional, must check if they are present
                    if req.form.has_key(property):
                        if len(req.form[property]):
                            fields = {'serviceid': editId,
                                      'property': property,
                                      'value': req.form[property]}
                            addEntryFields(fields,'serviceproperty')
                            action = 'list'
    else:
        form.error = "Missing required property '" + missing + "'"
        action = 'edit'
    selected = [editId]
    return action,form,selected

# Function for handling listing and editing of services
def editService(req,selected,action,error=None):
    path = EDITPATH + [('Services',BASEPATH+'service/list'),('Add',False)]
    table = 'service'
    idfield = 'serviceid'
    templatebox = editboxService()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'service/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.Service
    editList.tablename = 'service'
    editList.orderBy = 'handler'
    editList.idcol = 'serviceid'
    editList.columns = [('Server','netbox',True),
                        ('Handler','handler',False),
                        ('Version','version',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm) or \
       req.form.has_key(form.CNAME_CONTINUE):
        missing = templatebox.hasMissing(req)
        if not missing:
            if req.form.has_key(form.CNAME_CONTINUE):
                action,form = addService(req,form)
            elif req.form.has_key(ADDNEW_ENTRY):
                checker = req.form['handler']
                # Check if this handler need any properties 
                properties = getDescription(req.form['handler'])
                if properties:
                    form = editForm(editForm.CNAME_CONTINUE)
                    form.title = 'Add service'
                    form.add(editboxService(formData=req.form,disabled=True))
                    form.add(editboxServiceProperties(checker,
                                                      req.form['netboxid']))
                    form.textConfirm = 'Add service'
                    editList = None
                    action = 'properties'
                else:
                    # No properties needed, so just add the service
                    addService(req,form)
                    editList.status = 'Added service'
                    action = 'list'
            elif req.form.has_key(UPDATE_ENTRY):
                action,form,selected = updateService(req,form)
                if action == 'list':
                    editList.status = 'Updated service'
                else:
                    editList = None
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected service(s) deleted'
        action = 'list' 
    
    # Decide what to show
    if action == 'properties':
        editList = None 
    elif action == 'edit':
        path = EDITPATH + [('Services',BASEPATH+'service/list'),('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit services'
        else:
            form.title = 'Edit service'
        form.textConfirm = 'Update'
        # Only allow editing of one service at a time
        selected = selected[0]
        form.add(editboxService(selected))
        checker = editTables.editdbService(selected).handler
        netboxid = editTables.editdbService(selected).netboxid
        properties = getDescription(checker)
        if properties:
            form.add(editboxServiceProperties(checker,netboxid,editId=selected))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Services',BASEPATH+'service/list'),('Add',False)]
        form.title = 'Add service'
        form.textConfirm = 'Continue'
        form.add(editboxService())
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Services',BASEPATH+'service/list'),('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected service(s)?'
        editList.action = BASEPATH + 'service/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Services',False)]
        editList.title = 'Edit services'
        editList.action = BASEPATH + 'service/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
    return template.respond()

# Function for handling listing and editing of organisations
def editSubcat(req,selected,action,error=None):
    path = EDITPATH + [('Subcategories',BASEPATH+'subcat/list'),('Add',False)]
    table = 'subcat'
    idfield = 'subcatid'
    templatebox = editboxSubcat()
    # Form definition
    form = editForm()
    form.action = BASEPATH + 'subcat/edit/'
    # List definition
    editList = selectList()
    editList.table = editTables.editdbSubcat
    editList.tablename = 'subcat'
    editList.orderBy = ['catid','subcatid']
    editList.idcol = 'subcatid'
    editList.columns = [('Subcategory','subcatid',True),
                        ('Category','catid',False),
                        ('Description','descr',False)]

    # Check if the confirm button has been pressed
    if req.form.has_key(form.cnameConfirm):
        missing = templatebox.hasMissing(req) 
        if not missing:
            if req.form.has_key(ADDNEW_ENTRY):
                error = addEntry(req,templatebox,table,unique='subcatid')
                if not error:
                    editList.status = "Added subcategory '" + \
                                  req.form['subcatid'] + "'"
                    action = 'list'
                else:
                    form.error = error
                    action = 'add'
            elif req.form.has_key(UPDATE_ENTRY):
                selected,error = updateEntry(req,templatebox,table,
                                             idfield,unique='subcatid')
                if not error:
                    status = 'Updated '
                    for s in selected:
                        status += editTables.Subcat(s).subcatid + ' ' 
                    editList.status = status
                    action = 'list'
                else:
                    form.error = error
                    action = 'edit'
        else:
            form.error = "Required field '" + missing + "' missing"    
    # Confirm delete pressed?
    if req.form.has_key(selectList.cnameDeleteConfirm):
        deleteEntry(selected,table,idfield)
        editList.status = 'Selected subcategory deleted'
        action = 'list' 
    
    # Decide what to show 
    if action == 'edit':
        path = EDITPATH + [('Subcategories',BASEPATH+'subcat/list'),
                           ('Edit',False)]
        if len(selected)>1:
            form.title = 'Edit subcategory'
        else:
            form.title = 'Edit subcategory'
        form.textConfirm = 'Update'
        for s in selected:
            form.add(editboxSubcat(s))
        editList = None
    elif action == 'add':
        path = EDITPATH + [('Subcategories',BASEPATH+'subcat/list'),
                           ('Add',False)]
        form.title = 'Add new subcategory'
        form.textConfirm = 'Add'
        form.add(editboxSubcat(formData=req.form))
        editList = None
    elif action == 'delete':
        path = EDITPATH + [('Subcategories',BASEPATH+'subcat/list'),
                           ('Delete',False)]
        editList.isDeleteList = True
        editList.deleteList = selected
        editList.title = 'Are you sure you want to delete the selected ' + \
                         'subcategory?'
        editList.action = BASEPATH + 'subcat/edit/'
        editList.fill()
    elif action == 'list':
        path = EDITPATH + [('Subcategories',False)]
        editList.title = 'Edit subcategories'
        editList.action = BASEPATH + 'subcat/edit/'
        editList.error = error
        editList.fill()
        # don't display the form
        form = None

    nameSpace = {'editList': editList, 'editForm': form}
    template = editdbTemplate(searchList=[nameSpace])
    template.path = path
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
    showConfirm = True

    # Used by edit netbox in the intermediate
    CNAME_CONTINUE = 'cname_continue'

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
    maxlength = None
    def __init__(self,value='',size=22,maxlength=None,disabled=False):
        self.value = value
        self.disabled = disabled
        self.size = str(size)
        if maxlength:
            self.maxlength = str(maxlength)

class inputSelect:
    type = 'select'
    name = None
    
    def __init__(self,options=None,table=None,attribs=None,disabled=False):
        self.value = ''
        self.options = options
        self.attribs = attribs
        self.disabled = disabled

        if table:
            self.options = table.getOptions() 

class inputMultipleSelect:
    type = 'multipleselect'
    name = None
    value = []
    def __init__(self,options=None,table=None,disabled=False):
        self.options = options
        self.disabled = disabled

        if table:
            self.options = table.getOptions() 

class inputFile:
    type = 'file'
    name = None
    value = ''
    disabled = False
    def __init__(self):
        pass

class inputTextArea:
    type = 'textarea'
    name = None
    value = ''
    disabled = False

    def __init__(self,rows=20,cols=80):
        self.rows = rows
        self.cols = cols


class inputCheckbox:
    type = 'checkbox'
    name = None
    # A value of 1 when selected is nice for boolean fields in the db
    # this is repleaced by fill() though, so this is explicitly set in
    # the template for checkboxes (bad)
    value = "1"

    def __init__(self,disabled=False):
        self.value = "1"
        self.disabled = disabled

class inputHidden:
    type = 'hidden'
    name = None
    disabled = False

    def __init__(self,value):
        self.value = value

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
            value = getattr(entry,fieldname)
            if value:
                desc[0].value = str(value)

    def setControlNames(self,controlList=None):
        " Set controlnames for the inputs to the fieldnames "
        if not controlList:
            controlList = self.fields

        for fieldname,desc in controlList.items():
            desc[0].name = fieldname

    def hasMissing(self,req):
        """
        Check if any of the required fields are missing in the req.form
        Returns the name the first missing field, or False
        Note: keep_blank_values must be True or empty fields won't
              be present in the form 
        """
        missing = False
        for field,desc in self.fields.items():
            # Keep blank values must be switched on, or else the next line
            # will fail, could easily be more robust
            if req.form.has_key(field):
                if type(req.form[field]) is list:
                    # the field is a list, several entries have been edited
                    for each in req.form[field]:
                        if desc[1] == REQ_TRUE:
                            # this field is required
                            if not len(each):
                                missing = field
                                break
                else:
                    if desc[1] == REQ_TRUE:
                        # tihs field is required
                        if not len(req.form[field]):
                            missing = field
                            break
        return missing

    def addHidden(self,fieldname,value):
        self.hiddenFields[fieldname] = [inputHidden(value),False]
        self.hiddenFields[fieldname][0].name = fieldname

    def addDisabled(self):
        # Since fields are disabled, they aren't posted (stupid HTML)
        # so we must add them as hidden fields
        # This only goes for textinputs (?!) so we must also change
        # controlnames to avoid getting double values for selects, etc.
        for fieldname,definition in self.fields.items():
            if not definition[0].type=='hidden':
                self.addHidden(fieldname,definition[0].value)
                definition[0].name = definition[0].name + '_disabled'

    def formFill(self,formData):
        # Fill this editbox with data from the form
        # This is used by intermediate steps (like register serial)
        # to remember fieldvalues
        for field,definition in self.fields.items():
            if formData.has_key(field):
                definition[0].value = formData[field]

class editboxServiceProperties(editbox):
    type = 'serviceproperties'
    table = editTables.Serviceproperty

    def __init__(self,checker,boxId,editId=None):
        self.show = False
        properties = getDescription(checker)

        self.args = {}
        self.optargs = {}
        if properties:
            self.show = True
            self.title = "Properties for '" + properties['description'] + \
                         "' on " + editTables.Netbox(boxId).sysname

            if properties.has_key('args'):
                for a in properties['args']:
                    self.args[a] = [inputText(),REQ_TRUE]
                    self.setControlNames(self.args)
            if properties.has_key('optargs'):
                for a in properties['optargs']:
                    self.optargs[a] = [inputText(),REQ_FALSE]
                    self.setControlNames(self.optargs)

            if editId:
                sql = "SELECT * FROM serviceproperty WHERE " + \
                      "serviceid='" + editId + "'"
                result = executeSQLreturn(sql)
                for entry in result:
                    property = entry[1]
                    value = entry[2]
                    if self.args.has_key(property):
                        self.args[property][0].value = value
                    if self.optargs.has_key(property):
                        self.optargs[property][0].value = value

        # The editboxNetbox has UPDATE_ENTRY (which holds the id) or ADDNEW, 
        # don't need to repeat it here 
        self.boxName = IGNORE_BOX

class editboxService(editbox):
    type = 'service'
    table = editTables.editdbService
            
    def __init__(self,editId=None,formData=None,disabled=False):
        self.hiddenFields = {}
        self.help = ''
        if not editId and not formData:
            self.help = 'Select a server and a service handler'

        servers = [('','Select a server')]
        t = editTables.Netbox
        for s in t.getAllIterator(where="catid='SRV'",orderBy='sysname'):
            servers.append((str(s.netboxid),s.sysname))

        handlers = [('','Select a handler')]
        checkers = []
        for c in getCheckers():
            checkers.append((c,c))
        checkers.sort()
        handlers += checkers

        disabledHandler = disabled
        if editId:
            disabledHandler = True
        f = {'netboxid': [inputSelect(options=servers,disabled=disabled),
                         REQ_TRUE],
             'handler': [inputSelect(options=handlers,disabled=disabledHandler),
                        REQ_TRUE]}

        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

        if formData:
            self.formFill(formData)

        if disabled:
            self.addDisabled()
 
 
class editboxRoom(editbox):
    type = 'room'
    table = editTables.editdbRoom
            
    def __init__(self,editId=None,formData=None):
        # Field definitions {field name: [input object, required]}
        f = {'roomid': [inputText(),REQ_TRUE],
             'locationid': [inputSelect(table=editTables.editdbLocation),REQ_TRUE],
             'descr': [inputText(),REQ_FALSE],
             'opt1': [inputText(),REQ_FALSE],
             'opt2': [inputText(),REQ_FALSE],
             'opt3': [inputText(),REQ_FALSE],
             'opt4': [inputText(),REQ_FALSE]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()
        
        if formData:
            self.formFill(formData)

class editboxLocation(editbox):
    type = 'location'
    table = editTables.Location
            
    def __init__(self,editId=None,formData=None):
        # Field definitions {field name: [input object, required]}
        f = {'locationid': [inputText(),REQ_TRUE],
             'descr': [inputText(),REQ_TRUE]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()
        
        if formData:
            self.formFill(formData)

class editboxOrg(editbox):
    type = 'org'
    table = editTables.Org
            
    def __init__(self,editId=None,formData=None):
        # Field definitions {field name: [input object, required]}
        o = [('','No parent')]

        for org in self.table.getAllIterator():
            o.append((org.orgid,org.orgid + \
                      ' (' + str(org.descr) + ')'))

        f = {'orgid': [inputText(maxlength=10),REQ_TRUE],
             'parent': [inputSelect(options=o),REQ_NONEMPTY],
             'descr': [inputText(),REQ_FALSE],
             'opt1': [inputText(),REQ_FALSE],
             'opt2': [inputText(),REQ_FALSE],
             'opt3': [inputText(),REQ_FALSE]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

        if formData:
            self.formFill(formData)

class editboxType(editbox):
    type = 'type'
    table = editTables.editdbType
            
    def __init__(self,editId=None,formData=None):
        # Field definitions {field name: [input object, required]}
        f = {'typename': [inputText(maxlength=10),REQ_TRUE],
             'vendorid': [inputSelect(table=editTables.editdbVendor),REQ_TRUE],
             'descr': [inputText(),REQ_TRUE],
             'sysobjectid': [inputText(),REQ_TRUE],
             'cdp': [inputCheckbox(),REQ_FALSE],
             'tftp': [inputCheckbox(),REQ_FALSE],
             'frequency': [inputText(),REQ_FALSE]}

        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

        if formData:
            self.formFill(formData)


class editboxProduct(editbox):
    type = 'product'
    table = editTables.editdbProduct

    def __init__(self,editId=None,formData=None):
        # Field definitions {field name: [input object, required]}
        f = {'vendorid': [inputSelect(table=editTables.editdbVendor),REQ_TRUE],
             'productno': [inputText(),REQ_TRUE],
             'descr': [inputText(),REQ_FALSE]}

        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

        if formData:
            self.formFill(formData)

class editboxVendor(editbox):
    type = 'vendor'
    table = editTables.editdbVendor
            
    def __init__(self,editId=None,formData=None):
        # Field definitions {field name: [input object, required]}
        f = {'vendorid': [inputText(maxlength=15),REQ_TRUE]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

        if formData:
            self.formFill(formData)

class editboxUsage(editbox):
    type = 'usage'
    table = editTables.Usage
            
    def __init__(self,editId=None,formData=None):
        # Field definitions {field name: [input object, required]}
        f = {'usageid': [inputText(),REQ_TRUE],
             'descr': [inputText(),REQ_TRUE]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

        if formData:
            self.formFill(formData)

class editboxPrefix(editbox):
    type = 'prefix'
    table = editTables.editdbPrefixVlan
            
    def __init__(self,editId=None,formData=None):
        nettypes = [('static','static'),
                    ('reserved','reserved'),
                    ('scope','scope')]

        orgs = [('','No organisation')]
        for option in editTables.editdbOrg.getOptions():
            orgs.append(option)

        usageids = [('','No usage')]
        for usage in editTables.Usage.getAllIterator():
            usageids.append((usage.usageid,usage.usageid + ' (' + \
                            usage.descr + ')'))

        # Field definitions {field name: [input object, required]}
        f = {'netaddr': [inputText(),REQ_TRUE],
             'nettype': [inputSelect(options=nettypes),REQ_TRUE],
             'orgid': [inputSelect(options=orgs),REQ_NONEMPTY],
             'netident': [inputText(),REQ_FALSE],
             'description': [inputText(),REQ_FALSE],
             'vlannumber': [inputText(size=5),REQ_NONEMPTY],
             'usageid': [inputSelect(options=usageids),REQ_NONEMPTY]}
             
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill() 

        if formData:
            self.formFill(formData)

class editboxVlan(editbox):
    type = 'vlan'
    table = editTables.editdbVlan
            
    def __init__(self,editId=None):
        nettypes = [('core','core'),
                    ('elink','elink'),
                    ('lan','lan'),
                    ('link','link'),
                    ('loopback','loopback'),
                    ('private','private')]

        orgs = [('','No organisation')]
        for option in editTables.editdbOrg.getOptions():
            orgs.append(option)

        usageids = [('','No usage')]
        for usage in editTables.Usage.getAllIterator():
            usageids.append((usage.usageid,usage.usageid + ' (' + \
                            usage.descr + ')'))

        # Field definitions {field name: [input object, required]}
        f = {'nettype': [inputSelect(options=nettypes),REQ_TRUE],
             'orgid': [inputSelect(options=orgs),REQ_FALSE],
             'netident': [inputText(),REQ_FALSE],
             'description': [inputText(),REQ_FALSE],
             'vlan': [inputText(size=5),REQ_FALSE],
             'usageid': [inputSelect(options=usageids),REQ_FALSE]}
             
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill() 

# This editbox can display a message and contain hidden inputs
class editboxHiddenOrMessage(editbox):
    type = 'hiddenormessage'

    def __init__(self,message=None):
        self.hiddenFields = {}
        self.message = message

        # The editboxNetbox has UPDATE_ENTRY (which holds the id) or ADDNEW, 
        # don't need to repeat it here 
        self.boxName = IGNORE_BOX


class editboxNetboxSerial(editbox):
    type = 'netboxserial'

    def __init__(self,gotRo,serial='',sysname=None,typeid=None,
                 snmpversion=None,formData=None,editSerial=False):
        self.hiddenFields = {}
        # Set info fields
        self.sysname = sysname
        if typeid:
            self.typename = editTables.Type(typeid).typename
        else:
            self.typename = 'n/a'
        if snmpversion:
            self.snmpversion = snmpversion
        else:
            self.snmpversion = 'n/a'

        disabled = False
        self.help = None
        if gotRo:
            # RO was specified, so the box has been queried by SNMP
            if serial:
                # It returned a serialnumber
                disabled = True
                self.help = 'Serialnumber retrieved by SNMP.'
            else:
                self.help = 'Unable to retrieve serialnumber for this ' + \
                            'device by SNMP. ' + \
                            'Enter a serialnumber, or leave blank ' + \
                            'if you don\'t want to register a serial ' +\
                            'for this device.'
        else:
            if serial:
                # Serial was entered manually
                self.help = ''
                disabled = True
            else:   
                self.help = 'Enter a serialnumber, or leave ' +\
                            'blank if you don\'t want to register ' + \
                            'a serial for this device.'

        # If editSerial = True, override help text and always enable editing
        if editSerial:
            disabled = False
            # Should be some help text here
            self.help = ''

        self.fields = {'serial': [inputText(value=serial,disabled=disabled),
                                  REQ_TRUE]}
        self.setControlNames()

        self.addHidden('sysname',sysname)
        self.addHidden('typeid',typeid)
        self.addHidden('snmpversion',snmpversion)

        if formData:
            self.formFill(formData)

        if disabled:
            self.addDisabled()
        
        # The editboxNetbox has UPDATE_ENTRY (which holds the id) or ADDNEW, 
        # don't need to repeat it here 
        self.boxName = IGNORE_BOX

class editboxNetboxCategory(editbox):
    type = 'netboxcategory'
    editId = None

    def __init__(self,catid,editId=None,showHelp=True):
        self.hiddenFields = {}
        subcategories = False
        if len(editTables.Subcat.getAll(where="catid='" + catid + "'")):
            subcategories = True

        self.help = None
        if editId:
            self.editId = editId
        elif showHelp:
            # Only show help if we're adding a new box
            if subcategories:
                self.help = 'You can select one or more subcategories for '+\
                            'boxes with the selected category. You can also '+\
                            'add an optional description of the function of '+\
                            'this box.'
            else:
                self.help = 'You can add an optional description of the ' + \
                            'function of this box.'

        o = []
        for subcat in editTables.Subcat.getAllIterator(where="catid='" + \
                                                       catid + "'"):
            o.append((subcat.subcatid,subcat.subcatid + ' (' + \
                      subcat.descr + ')'))
        if editId:
            if subcategories:
                self.fields = {'subcat': \
                              [inputMultipleSelect(options=o),REQ_FALSE],
                              'function': [inputText(size=40),REQ_FALSE]}
            else:
                self.fields = {'function': [inputText(size=40),REQ_FALSE]}
        else:
            if subcategories:
                self.fields = {'subcat': [inputMultipleSelect(options=o),
                                         REQ_FALSE],
                               'function': [inputText(size=40),REQ_FALSE]}
            else:
                self.fields = {'function': [inputText(size=40),REQ_FALSE]}
 
        self.setControlNames()

        if editId:
            # Get selected netboxcategories
            sql = "SELECT category FROM netboxcategory WHERE netboxid='%s'" \
            % (editId,)
            res = executeSQLreturn(sql)
            selected = []
            for s in res:
               selected.append(s[0])
               if subcategories:
                   # A subcat field is present for this box with this cat
                   self.fields['subcat'][0].value = selected

            # Get var 'function' from netboxinfo
            sql = "SELECT val FROM netboxinfo WHERE netboxid='%s' " \
                  % (editId,) + \
                  "AND var='function'"
            res = executeSQLreturn(sql)
            if res:
                self.fields['function'][0].value = res[0][0]
        
        # The editboxNetbox has UPDATE_ENTRY (which holds the id), 
        # don't need to repeat it here 
        self.boxName = IGNORE_BOX

class editboxNetbox(editbox):
    type = 'netbox'
    table = editTables.editdbNetbox
    editId = None

    def __init__(self,editId=None,formData=None,disabled=False):
        self.hiddenFields = {}
        if editId:
            # Preserve the selected id
            self.addHidden(selectList.cnameChk,editId)
            self.sysname = editTables.Netbox(editId).sysname
            self.editId = editId
            self.path = EDITPATH + [('Boxes','/editdb/netbox/list'),
                                    ('Edit',False)]
        else:
            self.path = EDITPATH + [('Boxes','/editdb/netbox/list'),
                                    ('Add',False)]
 
        o = [(None,'Select an organisation')]
        for org in editTables.Org.getAllIterator(orderBy='orgid'):
            o.append((org.orgid,org.orgid + ' (' + str(org.descr) + ')'))

        r = [(None,'Select a room')]
        for room in editTables.Room.getAllIterator(orderBy='roomid'):
            loc = editTables.Location(room.location).descr
            r.append((room.roomid,room.roomid + ' (' + loc + ':' + \
                      str(room.descr) + ')'))

        c = [(None,'Select a category')]
        for cat in editTables.Cat.getAllIterator(orderBy='catid'):
            c.append((cat.catid,cat.catid + ' (' + str(cat.descr) + ')'))

        # Field definitions {field name: [input object, required]}
        f = {'ip': [inputText(disabled=disabled),REQ_TRUE],
             'catid': [inputSelect(options=c,disabled=disabled),REQ_TRUE],
             'orgid': [inputSelect(options=o,disabled=disabled),REQ_TRUE],
             'roomid': [inputSelect(options=r,disabled=disabled),REQ_TRUE],
             'ro': [inputText(disabled=disabled),REQ_FALSE],
             'rw': [inputText(disabled=disabled),REQ_FALSE]}
        self.fields = f
        self.setControlNames()

        if editId:
            # This box is for editing an existing netbox with id = editId
            self.editId = editId
            self.fill()

        if formData:
            self.formFill(formData)

        if disabled:
            self.addDisabled()

 
class editboxSubcat(editbox):
    type = 'subcat'
    table = editTables.editdbSubcat
            
    def __init__(self,editId=None,formData=None):
        # Field definitions {field name: [input object, required]}
        o = [('','Select a category')]
        for cat in editTables.Cat.getAllIterator():
            o.append((cat.catid,cat.catid + ' (' + cat.descr + ')'))

        f = {'subcatid': [inputText(),REQ_TRUE],
             'catid': [inputSelect(options=o),REQ_TRUE],
             'descr': [inputText(),REQ_TRUE]}
        self.fields = f
        self.setControlNames()

        if editId:
            self.editId = editId
            self.fill()

        if formData:
            self.formFill(formData) 

class editboxBulk(editbox):
    type = 'bulk'

    help = 'Import multiple entries by selecting a file, or pasting ' +\
           'into the textarea. Select an import type to see syntax ' + \
           'for this type.'
    
    def __init__(self):
        tables = [('','Select an import type'),
                  ('location','Locations'),
                  ('room','Rooms'),
                  ('org','Organisations'),
                  ('usage','Usage categories'),
                  ('subcat','Subcategories'),
                  ('type','Types'),
                  ('product','Products'),
                  ('vendor','Vendors'),
                  ('netbox','Boxes'),
                  ('service','Services'),
                  ('vlan','Vlans'),
                  ('prefix','Prefixes')]

        sep = [(':','Colon (:)'),
               (';','Semicolon (;)'),
               (',','Comma (,)')]

        f = {'table': [inputSelect(options=tables),REQ_FALSE],
             'separator': [inputSelect(options=sep),REQ_FALSE],
             'file': [inputFile(),REQ_FALSE],
             'textarea': [inputTextArea(),REQ_FALSE]}
        self.fields = f
        self.setControlNames()

# Classes describing the fields for bulk import
class bulkdefLocation:
    # number of fields
    tablename = 'location'
    table = editTables.Location
    uniqueField = 'locationid'
    num_fields = 2

    process = False
    syntax = '#locationid:descr'

    # list of (fieldname,max length,not null,use field)
    fields = [('locationid',12,True,True),
              ('descr',0,True,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)


class bulkdefRoom:
    # number of fields
    tablename = 'room'
    table = editTables.Room
    uniqueField = 'roomid'
    num_fields = 7

    process = False
    syntax = '#roomid:locationid:descr:opt1:opt2:opt3:opt4'

    # list of (fieldname,max length,not null,use field)
    fields = [('roomid',10,True,True),
              ('locationid',12,False,True),
              ('descr',0,False,True),
              ('opt1',0,False,True),
              ('opt2',0,False,True),
              ('opt3',0,False,True),
              ('opt4',0,False,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)

class bulkdefOrg:
    tablename = 'org'
    table = editTables.Org
    uniqueField = 'orgid'
    num_fields = 6

    process = False
    syntax = '#orgid:parent:description:optional1:optional2:optional3'

    # list of (fieldname,max length,not null,use field)
    fields = [('orgid',10,True,True),
              ('parent',10,False,True),
              ('descr',0,False,True),
              ('opt1',0,False,True),
              ('opt2',0,False,True),
              ('opt3',0,False,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)

class bulkdefUsage:
    # number of fields
    tablename = 'usage'
    table = editTables.Usage
    uniqueField = 'usageid'
    num_fields = 2

    process = False
    syntax = '#usageid:descr'

    # list of (fieldname,max length,not null,use field)
    fields = [('usageid',10,True,True),
              ('descr',0,True,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)

class bulkdefVendor:
    # number of fields
    tablename = 'vendor'
    table = editTables.Vendor
    uniqueField = 'vendorid'
    num_fields = 1

    process = False
    syntax = '#vendorid'

    # list of (fieldname,max length,not null,use field)
    fields = [('vendorid',15,True,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)

class bulkdefSubcat:
    tablename = 'subcat'
    table = editTables.Subcat
    uniqueField = 'subcatid'
    num_fields = 3

    process = False
    syntax = '#subcatid:catid:description'

    # list of (fieldname,max length,not null,use field)
    fields = [('subcatid',0,True,True),
              ('catid',8,True,True),
              ('descr',0,True,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)


class bulkdefType:
    # number of fields
    tablename = 'type'
    table = editTables.Type
    uniqueField = 'typename'
    num_fields = 7

    process = False
    syntax = '#vendorid:typename:sysoid:description:frequency:cdp:tftp'

    # list of (fieldname,max length,not null,use field)
    fields = [('vendorid',15,True,True),
              ('typename',10,True,True),
              ('sysobjectid',0,True,True),
              ('descr',0,False,True),
              ('frequency',0,False,True),
              ('cdp',0,False,True),
              ('tftp',0,False,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)

class bulkdefProduct:
    # number of fields
    tablename = 'product'
    table = editTables.Product
    uniqueField = 'productno'
    num_fields = 4

    process = True
    syntax = '#vendorid:productno:description'

    # list of (fieldname,max length,not null,use field)
    fields = [('vendorid',15,True,True),
              ('productno',0,True,True),
              ('descr',0,False,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)

    def preInsert(cls,row):
        # if cdp or tftp has any value, set it to "1" which is appropriate
        # for the boolean fields in the database
        if row.has_key('cdp'):
            row['cdp'] = '1'
        if row.has_key('tftp'):
            row['tftp'] = '1'
        return row
    preInsert = classmethod(preInsert)

class bulkdefNetbox:
    " For parsing netboxes "    
    tablename = 'netbox'
    table = editTables.Netbox
    uniqueField = 'ip'
    # number of fields
    num_fields = 7

    process = True
    syntax = '#roomid:ip:orgid:catid:ro:rw:serial'

    # list of (fieldname,max length,not null,use field)
    fields = [('roomid',0,True,True),
              ('ip',0,True,True),
              ('orgid',10,True,True),
              ('catid',8,True,True),
              ('ro',0,False,True),
              ('rw',0,False,True),
              ('serial',0,False,False)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        if field == 'ip':
            try:
                sysname = gethostbyaddr(data)[0]
            except:
                remark = "DNS lookup failed, using '" + data + "' as sysname"

        if field == 'serial':
            if len(data):
                where = "serial='" + data + "'"
                device = editTables.Device.getAll(where)
                if device:
                    remark = "Duplicate serialnumber '" + data + "', skipping"
                    status = False
        return (status,remark)
    checkValidity = classmethod(checkValidity)

    def preInsert(cls,row):
        try:
            sysname = gethostbyaddr(row['ip'])[0]
        except:
            sysname = row['ip'] 
        row['sysname'] = sysname

        deviceid = None
        box = None
        if len(row['ro']):
            try:
                box = initBox.Box(row['ip'],row['ro'])
                deviceid = box.getDeviceId()
            except:
                # If initBox fails, always make a new device
                deviceid = None

        if deviceid:
            row['deviceid'] = deviceid
        else:
            if box:
            # if we got serial from initbox, set this
                if box.serial:
                    row['serial'] = box.serial
            # Make new device
            if len(row['serial']):
                fields = {'serial': row['serial']}
            else:
                # Don't insert an empty serialnumber (as serialnumbers must be
                # unique in the database)
                fields = {}
            deviceid = addEntryFields(fields,
                                      'device',
                                      ('deviceid','device_deviceid_seq'))
            row['deviceid'] = deviceid
        return row
    preInsert = classmethod(preInsert)

class bulkdefService:
    tablename = 'service'
    table = editTables.Service
    uniqueField = None
    num_fields = 2

    process = False
    syntax = '#sysname/ip:handler'

    # list of (fieldname,max length,not null,use field)
    fields = [('netboxid',0,True,True),
              ('handler',0,True,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        return (status,remark)
    checkValidity = classmethod(checkValidity)

class bulkdefPrefix:
    tablename = 'prefix'
    table = editTables.Prefix
    uniqueField = 'prefixid'
    num_fields = 7

    process = False
    syntax = '#prefix/mask:nettype:org:netident:usage:description'

    # list of (fieldname,max length,not null,use field)
    fields = [('netaddr',0,True,True),
              ('nettype',0,False,True),
              ('org',0,False,True),
              ('netident',0,False,True),
              ('usage',0,False,True),
              ('description',0,False,True)]

    def checkValidity(cls,field,data):
        status = True
        remark = None
        # check if cidr is valid here
        return (status,remark)
    checkValidity = classmethod(checkValidity)


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
    cnameHiddenData = 'hidden_data'
    # List rows where
    where = None

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
            entries = self.table.getAllIterator(orderBy=self.orderBy,
                                                where=self.where)
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
                    row.append(([getattr(entry,column)],BASEPATH + self.tablename + '/edit/' + eid))
                else:
                    text = []
                    if type(column) is str:
                        text = [getattr(entry,column)]
                    else:
                        sectable,secidfield,sectextfield = column
                        iter = sectable.getAllIterator(where=secidfield + \
                                        "='" + eid + "'")
                        for i in iter:
                            text.append(getattr(i,sectextfield)) 
                    row.append((text,None))
            self.rows.append((id,row))
