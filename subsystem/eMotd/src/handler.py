#################################################
## blapp.py

#################################################
## Imports
from mod_python import util, apache
from mx import DateTime
from time import strftime
import sys,os,re,copy,string
import nav
import nav.db.manage 
from nav import db
from nav.db.manage import Emotd, Emotd_related, Maintenance 
from nav.db.manage import Room, Service, Netbox 
from nav.web.TreeSelect import TreeSelect, Select, UpdateableSelect
from nav.web import SearchBox,EmotdSelect,redirect

#################################################
## Templates

from nav.web.templates.EmotdTemplate import EmotdTemplate
from nav.web.templates.EmotdStandardTemplate import EmotdStandardTemplate
from nav.web.templates.EmotdFrontpage import EmotdFrontpage
from nav.web.templates.EmotdMessageTemplate import EmotdMessageTemplate
from nav.web.templates.MaintenanceTemplate import MaintenanceTemplate
from nav.web.templates.MaintListTemplate import MaintListTemplate
from nav.web.templates.MaintTimeTemplate import MaintTimeTemplate
from nav.web.templates.TreeSelectTemplate import TreeSelectTemplate

#################################################
## Module constants

title = 'Massage of the day'
menu = ''

EmotdTemplate.path =  [("Frontpage", "/"), ("eMotd", "/emotd")]
DATEFORMAT = "%Y-%m-%d %H:%M"
BASEPATH = '/emotd/'
LANG1 = "Norwegian"
LANG2 = "English"

connection = db.getConnection('webfront','manage')
database = connection.cursor()

#################################################
# Elements 
 
def handler(req):
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)
    path = req.uri.split(BASEPATH)[1]
    path = path.split('/')

    if path[0] == 'search':
        output = search(req)
    elif path[0] == 'edit':
        output = edit(req)
    elif path[0] == 'view':
        output = view(req)
    elif path[0] == 'viewall':
        output = viewall(req)
    elif path[0] == 'maintenance':
        output = maintlist(req)
    elif path[0] == 'add':
        output = maintenance(req)
    elif path[0] == 'commit':
        output = commit(req)
    elif path[0] == 'time':
        output = mainttime()
    else:
        output = show_active(req)

    if output:
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND

## def handler(req):
##     path = req.uri
##     filename = re.search('/([^/]+)$',path).group(1)
##     keep_blank_values = True
##     req.form = util.FieldStorage(req,keep_blank_values)
##     if filename == 'index':
##         output = show_active(req)
##     elif filename == 'edit':
##         output = edit(req)
##     elif filename == 'search':
##         output = search(req)
##     elif filename == 'view':
##         output = view(req)
##     elif filename == 'viewall':
##         output = viewall(req)
##     elif filename == 'show_active':
##         output = show_active(req)
##     elif filename == 'commit':
##         output = commit(req)
##     elif filename == 'rssfeed':
##         output = feed(req)
##     elif filename == 'maintenance':
##         output = maintenance(req)
##     else:
##         output = show_active(req)
##     if output:
##         req.write(output)
##         return apache.OK
##     else:
##         return apache.HTTP_NOT_FOUND

class MenuItem:

    def __init__(self,link,text):
        self.link = link
        self.text = text
        
def getMenu(req):
    # Only show menu if logged in user
    # Should have some fancy icons and shit
    menu = []
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        menu.append(MenuItem("edit","New"))
    menu.append(MenuItem("show_active","Active"))
    menu.append(MenuItem("viewall","History"))
    menu.append(MenuItem("maintenance?list=active","Maintenance"))
    return menu

def editlinks(req,id):
    ''' return a set of links to put into a dict '''
    res = []
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        if Emotd(id).author == req.session['user'].login:
            # give user change-permissions
            res.append("change")
        else:
            # give user followup-permissions
            res.append("followup")
        if Emotd(id).publish_end > DateTime.now():
            res.append("outdate")
    return res


def search(req):
    ''' Free-text search in MOTD-db '''
    title = 'MOTD freetext search'
    EmotdTemplate.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Search","")]
    menu = getMenu(req)
    body = None
    motd = None
    searchBox = None
    nameSpace = {'title': title,'motd': motd,'menu': menu, 'searchBox': searchBox,'body': body , 'form': ''}
    page = EmotdStandardTemplate(searchList=[nameSpace])
    return page.respond()


class Message:
    def __init__(self, mess, equipment):# emotdid, last_changed, author, title, description, detail, affected, downtime, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd, key, value):
        #raise(repr(args))
        (emotdid, last_changed, author, title, description, detail, affected, downtime, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd) = mess[0:16]
        self.emotdid = emotdid
        if not isinstance(last_changed, str):
            last_changed = strftime("%Y-%m-%d %H:%M",last_changed.tuple())
        self.last_changed = last_changed
        self.author = author
        self.title = title
        self.description = description
        self.detail = detail
        self.affected = affected
        self.downtime = downtime
        self.title_en = title_en
        self.description_en = description_en
        self.detail_en = detail_en
        self.affected_en = affected_en
        self.downtime_en = downtime_en
        self.replaces_emotd = replaces_emotd
        self.equipment = equipment
                 
def show_active(req):
    ''' Show all active MOTD (as in not outdated )'''
    page = EmotdFrontpage() #searchList=[nameSpace]
    page.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Current active messages","")]
    page.title = 'Current active messages'
    body = ''
    form = ''
    emotds = []
    page.menu = getMenu(req)
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        sql = "select emotdid, key, value from emotd left outer join emotd_related using (emotdid) where publish_end > now() order by publish_end desc"
        database.execute(sql)

        equipment = {}
        for (emotdid, key, value) in database.fetchall():
            if not equipment.has_key(emotdid):
                equipment[emotdid] = {}
            if not equipment[emotdid].has_key(key):
                equipment[emotdid][key] = []
            equipment[emotdid][key].append(value)
            
        sql = "select emotdid, last_changed, author, title, description, detail, affected, downtime, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd from emotd where publish_end > now() order by publish_end desc"
        database.execute(sql)
        eq = {}
        for emotd in database.fetchall():
            emotdid = emotd[0]
            if equipment.has_key(emotdid):
                eq = equipment[emotdid]
                #raise repr(eq)
            emotds.append(Message(emotd,equipmentformat(eq)))
        page.access = True
    else:
        page.access = False
        page.emotds = EmotdSelect.getAllActive()
        for emotd in page.emotds:
            emotd = formatEmotd(emotd)
    page.emotds = emotds
    #page.menu = menu
    #nameSpace = {'title': title, 'emotds': motd, 'menu': menu, 'access': access}#
    #if access:
    #    page.access = True
    return page.respond()

def equipmentlist(emotdid = None):

    whereextra = ""
    if emotdid:
        whereextra = "and emotdid=%d" % int(emotdid)
    sql = "select emotdid, key, value from emotd left outer join emotd_related using (emotdid) where publish_end > now() %s order by publish_end desc" % whereextra
    database.execute(sql)
    
    equipment = {}
    for (emotdid, key, value) in database.fetchall():
        if not equipment.has_key(emotdid):
            equipment[emotdid] = {}
        if not equipment[emotdid].has_key(key):
            equipment[emotdid][key] = []
        equipment[emotdid][key].append(value)

    for a,b in equipment.items():
        equipment[emotdid] = equipmentformat(equipment[emotdid])
        
    return equipment

def equipmentformat(eqdict):
    resdict = {}
    if eqdict:
        if eqdict.has_key("location"):
            resdict["location"] = []
            for l in eqdict["location"]:
                database.execute("select descr from location where locationid = '%s'" % l)
                resdict["location"].append("%s (%s)" % (l,database.fetchone()[0]))
        if eqdict.has_key("room"):
            resdict["room"] = []
            for l in eqdict["room"]:
                database.execute("select descr from room where roomid = '%s'" % l)
                resdict["room"].append("%s (%s)" % (l,database.fetchone()[0]))
        if eqdict.has_key("netbox"):
            resdict["netbox"] = []
            for l in eqdict["netbox"]:
                database.execute("select sysname from netbox where netboxid = '%s'" % l)
                resdict["netbox"].append(database.fetchone()[0])
        if eqdict.has_key("service"):
            resdict["service"] = []
            for l in eqdict["service"]:
                database.execute("select sysname from handler, netbox inner join service using (netboxid) where serviceid = '%s'" % l)
                resultat = database.fetchone()
                resdict["service"].append("%s (%s)" % (resultat[0], resultat[1]))
    return resdict

def maintparse(maintdict):
    maints = []
    for maint in maintdict.keys():
        mstart = maintdict[maint][0]['maint_start'].strftime(DATEFORMAT)
        mend   = maintdict[maint][0]['maint_end'].strftime(DATEFORMAT)
        emotdid = maintdict[maint][0]['emotdid']
        title = Emotd(emotdid).title
        ##emotdurl = "<a href=/emotd/view?id=%s> %s </a>" % (emotdid,title) 
        for f in range(len(maintdict[maint])):
            # One maintenance, can keep severel rooms,netbox,services
            entry = maintdict[maint][f]
            if entry['key'] == 'room':
                entry['roomid'] = Room(entry['value']).roomid 
                entry['roomdesc'] = Room(entry['value']).descr
                entry['netboxid'] = None
                entry['serviceid'] = None
            if entry['key'] == 'netbox':
                entry['roomid'] = Netbox(entry['value']).room.roomid
                entry['roomdesc'] = Netbox(entry['value']).room.descr         
                entry['netboxid'] = Netbox(entry['value']).sysname
                entry['serviceid'] = None
            if entry['key'] == 'service':
                entry['roomid'] = Service(entry['value']).netbox.room.roomid
                entry['roomdesc'] = Service(61).netbox.room.descr ##Service(entry['value']).handler??
                entry['netboxid'] = Service(entry['value']).netbox.sysname
                entry['serviceid'] = Service(entry['value']).handler
            entry['mstart'] = mstart
            entry['mend'] = mend
            entry['title'] = title
            entry['emotdid'] = emotdid
            maints.append(entry)
    return maints

def wrap(s,lines=None,cols=74):
    ''' Wrap object of string for pretty printing
        Either full part of 's' or number of lines 
        Default wraps 's' into lines of 74 characters
        Example usage: wrap(s,3,74) 
    '''
    if lines==None:
        # Don't delete lines - show everything, but wrapped
        pass
    else:
        # Wrap 's' into 'lines' number of lines
        pass
    return s

def viewall(req,orderby=None):
    ''' Show all MOTDs available for current user '''
    title = 'All published messages'
    EmotdFrontpage.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Published messages","")]
    menu = getMenu(req)
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        emotds = EmotdSelect.fetchAll(access=True)
        for emotd in emotds:
            emotd = formatEmotd(emotd)
        access = True
    else:
        access = False
        emotds = EmotdSelect.fetchAll()
        for emotd in emotds:
            emotd = formatEmotd(emotd)
    nameSpace = {'title': title, 'emotds': emotds, 'menu': menu, 'access': access }
    page = EmotdFrontpage(searchList=[nameSpace])
    if access:
        page.access = True
    return page.respond()

def feed(req):
    ''' 
       RDF/RSS feed-generator  
       Suggest using http://diveintomark.org/projects/feed_parser/feedparser.py as
       parser for python-clients - very sweet!
    '''
    body = ''
    cursor = Emotd.cursor

    if req.form.has_key('client'):
        # try to find any
        client = req.form['client']
        if client == "html":
            body += '<html><body><pre>'
        # where do we store client-info?
        cursor.execute('select * from emotd where date_end > now() and date_start < now()')
    else:
        # if client is not supplied, show all
        cursor.execute('select * from emotd where date_end > now() and date_start < now()') 

    # the following will always follow the feed - please do not touch this..
    body += '<?xml version="1.0" encoding="iso-8859-1"?> \n'
    body += '<rdf:RDF \n'
    body += 'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" \n'
    body += 'xmlns="http://my.netscape.com/rdf/simple/0.9/"> \n'
    body += '\n'
    rows = cursor.dictfetchall()
    if len(rows) < 1:
        body += '<item>'
        body += '<title>No emotd currently active</title>'
        body += '<link>http://isbre.itea.ntnu.no</link>'
        body += '</item>'
    else:
        for row in rows:
            body += '<item>\n'
            body += '<title>%(title)s </title>' % row
            body += '<link>http://isbre.itea.ntnu.no/emotd/view?id=%(emotdid)s </link>' % row
            body += '</item>\n'
    # and this will be the tail of the feed
    body += '</rdf:RDF>\n\n'
    if client:
        if client == "html":
            body += '</pre></body></html>'
    return body


def mainttime(req):

    page = MaintTimeTemplate()
    return page.respond()


def maintenance(req):
    ''' Put locations,rooms,netboxes,modules,services on maintenance to prevent 
        alerts being sent while doing maintenance. Also views current/ongoing 
        maintenance.
    '''
    args = {}
    form = ''
    body = ''
    title = 'Set on maintenance'
    menu = getMenu(req)

    args['path'] = [('Frontpage','/'),
                    ('Tools','/toolbox'),
                    ('Messages',BASEPATH)]
    if not hasattr(req,"emotdid"):
        req.emotdid = 0
        if req.form.has_key('id'):
            req.emotdid = req.form['id']
    emotdid = req.emotdid

        
    searchBox = SearchBox.SearchBox(req,'Type a room id, an ip,a (partial) sysname or servicename')
    selectBox = TreeSelect()
    # search
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
    searchBox.addSearch('service',
                        'serviceid or partial servicename',
                        'Service',
                        {'rooms':['netbox','room','roomid'],
                         'netboxes':['netbox','netboxid'],
                         'locations': ['netbox','room','location','locationid'],
                         'services':['serviceid']},
                        where = "serviceid ='%s'")

    args['searchbox'] = searchbox
    sr = searchbox.getResults(req)
    
    args['action'] = BASEPATH + 'add'# + path + '/'
    args['returnpath'] = {'url': BASEPATH,
                          'text': 'Return'}
    args['error'] = None
    selectbox = TreeSelect()
    args['formname'] = selectbox.formName

    multiple = True

    select = Select('cn_location',
                    'Location',
                    multiple = True,
                    multipleSize = 10,
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
                               multipleSize=10,
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
                               multiple=True,
                               multipleSize=10,
                               preSelected = sr['netboxes'])

    select4 = UpdateableSelect(select3,
                               'cn_service',
                               'Module/Service',
                               'Service',
                               'handler',
                               'serviceid',
                               'netboxid',
                               multiple = True,
                               multipleSize=10,
                               onchange='',
                               optgroupFormat = '$d') 
    #                           preSelected = sr['services'])


    selectbox.addSelect(select)
    selectbox.addSelect(select2)
    selectbox.addSelect(select3)
    selectbox.addSelect(select4)

    validSelect = False
    
    # Update the selectboxes based on form data
    selectbox.update(req.form)
    # Not allowed to go on, unless at least a netbox is selected
    buttontext = "Add to message"
    buttonkey = "cn_add"
    if len(select3.selectedList):
        validSelect = True
        buttontext = "Add netbox(es) to message"
        buttonkey = "cn_add_netboxes"
    elif len(select2.selectedList):
        validSelect = True
        buttontext = "Add room(s) to message"
        buttonkey = "cn_add_rooms"
    elif len(select.selectedList):
        validSelect = True
        buttontext = "Add location(s) to message"
        buttonkey = "cn_add_locations"

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
##     # Register error clicked?
##     errorDevice = None
##     if req.form.has_key('cn_add_boxes'):
##         if req.form.has_key('cn_module'):
##             if len(req.form['cn_module']):
##                 moduleid = req.form['cn_module']
##                 deviceid = dtTables.Module(moduleid).device.deviceid
##                 # Uses History(), should have been a Device() class
##                 # (subclass of forgetSQL.Device())
##                 errorDevice = History(deviceid,moduleId=moduleid)
##         elif req.form.has_key('cn_netbox'):
##             if len(req.form['cn_netbox']):
##                 netboxid = req.form['cn_netbox']
##         args['action'] = BASEPATH + 'emotd/add'
    # Register error clicked?
    errorDevice = None
    if req.form.has_key('cn_add_boxes'):
        #if req.form.has_key('cn_module'):
        #    if len(req.form['cn_module']):
        #        moduleid = req.form['cn_module']
        #        deviceid = dtTables.Module(moduleid).device.deviceid
                # Uses History(), should have been a Device() class
                # (subclass of forgetSQL.Device())
        #        errorDevice = History(deviceid,moduleId=moduleid)
        #elif req.form.has_key('cn_netbox'):
        #    if len(req.form['cn_netbox']):
        #        netboxid = req.form['cn_netbox']
        args['action'] = BASEPATH + 'maintenance'
       
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
##     if path == 'history':
##         args['path'].append(('View history',False))
##         args['title'] = 'View history - select a box or a module'
##         args['submit'] = {'control': 'cn_submit_history',
##                           'value': 'View history',
##                           'enabled': validSelect}
##     elif path == 'error':
##    args['path'].append(('Register error',False))
##    args['title'] = 'Register error - select a box or a module'
    args['submit'] = {'control': buttonkey,
                      'value': buttontext,
                      'enabled': validSelect}
##     elif path == 'rma':
##         args['path'].append(('Register RMA',False))
##         args['title'] = 'Register RMA - select a box or a module'
##         args['submit'] = {'control': 'cn_submit_rma',
##                           'value': 'Register RMA',
##                           'enabled': validSelect}

    args['selectbox'] = selectbox
    args['deviceHistList'] = deviceHistList
    args['errorDevice'] = errorDevice
    args['rmaDevice'] = rmaDevice


    searchBox.addSearch('host',
                        'ip or hostname',
                        'Netbox',
                        {'rooms': ['room','roomid'],
                        'locations': ['room','location','locationid'],
                        'netboxes': ['netboxid']},
                        call = SearchBox.checkIP)
    searchBox.addSearch('room',
                        'room id',
                        'Room',
                        {'rooms': ['roomid'],
                         'locations': ['location','locationid']},
                         where = "roomid = '%s'")
    
    # Maintenance start<->end
    oneweek = str(DateTime.now() + DateTime.oneWeek)
    oneday = str(DateTime.now() + DateTime.oneDay)
    now = str(DateTime.now())
    form += '<table>'
    form += '<tr><td>Maintenance start:</td><td>' 
    form += ' Year: <select name=maint_year_start>\n'
    for year in range(2003,2020):
        form += '<option value=' + str(year) 
        # if year was submitted in form, choose this value
        if req.form.has_key('maint_year_start'):
            if year == req.form['maint_year_start']:
                form += ' selected=selected '
            form += '>' + str(year) + '</option>\n'
        else:
            if year == int(now[0:4]):
                form += ' selected=selected '
            form += '>' + str(year) + '</option>\n'
    form += '</select>'
    form += ' Month: <select name=maint_month_start>\n'
    for month in range(1,13): 
        form += '<option value=' + str(month) 
        if month == int(now[5:7]):
           form += ' selected=selected '
        form += '>' + str(month) + '</option>\n'
    form += '</select>'
    form += ' Day: <select name=maint_day_start>\n'
    for day in range(1,32): 
        # maybe have some check on the dates.. 31.2. doesn't quite exist
        form += '<option value=' + str(day)
        if day == int(now[8:10]):
            form += ' selected=selected '
        form += '>' + str(day) + '</option>\n'
    form += '</select>'
    form += 'Hour: <select name=maint_hour_start>'
    for hour in range(1,25):
        form += '<option value=' + str(hour)
        if hour == int(now[10:13]):
            form += ' selected=selected'
        form += '>' + str(hour) + '</option>\n'
    form += '</select>'
    form += '</td></tr>'
    # how long should we set on maintenance?
    form += '<tr><td>Maintenance end:</td><td>'
    form += ' Year: <select name=maint_year_end>\n'
    for year in range(2003,2020):
        form += '<option value=' + str(year) 
        if year == int(oneday[0:4]):
            form += ' selected=selected '
        form += '>' + str(year) + '</option>\n'
    form += '</select>'
    form += ' Month: <select name=maint_month_end>\n'
    for month in range(1,13): 
        form += '<option value=' + str(month)  
        if month == int(oneday[5:7]):
            form += ' selected=selected '
        form += '>' + str(month) + '</option>\n'
    form += '</select>'
    form += ' Day: <select name=maint_day_end>\n'
    for day in range(1,32): 
        # maybe have some check on the dates.. 31.2. doesn't quite exist
        form += '<option value=' + str(day) 
        if day == int(oneday[8:10]):
            form += ' selected=selected '
        form += '>' + str(day) + '</option>\n'
    form += '</select>\n'
    form += 'Hour: <select name=maint_hour_end>'
    for hour in range(1,25):
        form += '<option value=' + str(hour)
        if hour == int(oneweek[10:13]):
            form += ' selected=selected'
        form += '>' + str(hour) + '</option>\n'
    form += '</select>'
    form += '</td></tr></table>'
    
    #if req and req.form.has_key('list'): ##alltid med nå
    body = ""
    #if req.form['list'] == 'current' or req.form['list'] == 'active':
    activedict = EmotdSelect.getMaintenance(state='active',access=True)
    #if req.form['list'] == 'scheduled':
    scheduleddict = {}
    #scheduleddict = EmotdSelect.getMaintenance(state='scheduled',access=True)
    #body += '<table width=800><tr><th>Room</th><th>Sysname</th><th>Service</th><th>Start time</th><th>End time</th><th>Title</th></tr>\n'
    #maints = [] # store each room,netbox,service in each its own row

            # end view of maintenance with this id
        #body += '</table>\n'
        # For listing ongoing or scheduled maintenances, we don't show searchBox and selectBox.. present a link maybe?
    #    searchBox = None
    #    selectBox = None     
    #    maints = None
    #elif req and not req.form.has_key('submitbutton') and not req.form.has_key('list'):
        # Run update every time the form is submitted,
        # unless the submit button has been pressed
        #maints = ['',]
    #    selectBox.update(req.form)
    #elif req and req.form.has_key('submitbutton') and req.form.has_key('id'):
##         searchBox = None
##         selectBox = None
##         maints = None
##         form = ''
##         #raise repr(req.form.list)
##         if req.form.has_key('cn_netbox'):
##             services = {}
##             boxes = {}
##             boxes['cn_netbox'] = []
##             if type(req.form['cn_netbox']).__name__ == 'str':
##                 boxes['cn_netbox'].append(req.form['cn_netbox'])
##             else:
##                 boxes['cn_netbox'] = [] # empty list to put multiple boxes into
##                 for netbox in req.form['cn_netbox']:
##                     boxes['cn_netbox'].append(netbox)
##             body += '<p>Netboxes set on maintenance:<br>\n'
##             maint = Maintenance()
##             maint.emotd = int(req.form['id'])
##             if req.form.has_key('maint_year_start'):
##                 year_start = int(req.form['maint_year_start'])
##                 month_start = int(req.form['maint_month_start'])
##                 day_start = int(req.form['maint_day_start'])
##                 hour_start = int(req.form['maint_hour_start'])
##                 year_end = int(req.form['maint_year_end'])
##                 month_end = int(req.form['maint_month_end'])
##                 day_end = int(req.form['maint_day_end'])
##                 hour_end = int(req.form['maint_hour_end'])
##                 maint_start=DateTime.Date(year_start,month_start,day_start,hour_start)
##                 maint_stop=DateTime.Date(year_end,month_end,day_end,hour_end)
##                 maint.maint_start = maint_start
##                 maint.maint_end = maint_stop
##                 maint.state = "scheduled"
##                 maint.save()
##             for blapp in boxes['cn_netbox']:
##                 body += '<li> %s ' % Netbox(blapp).sysname 
##                 try:
##                     related = Emotd_related()
##                     related.emotd = req.form['id']
##                     related.key = 'netbox'
##                     related.value = blapp
##                 except:
##                     body += '<p><font color=red>An error occured!</font>'
##         else:
##             body = '<font color=red><p>No netbox or service/module chosen</font>'

    #maints = [maintparse(activedict),maintparse(scheduleddict)]
    #maints = maintparse(activedict)
    ##maints = [s,]
    args['title'] = title
#    nameSpace = {'title': title, 'motd': None, 'maints': maints, 'menu': menu, 'form':form,'body': body, 'searchBox': searchBox, 'selectBox': selectBox}
    nameSpace = {'title': title,'page': 'browse', 'body': body, 'args': args, 'form':form, 'menu': menu}
    if req.form.has_key('cn_add_netboxes') or req.form.has_key('cn_add_rooms') or req.form.has_key('cn_add_locations'):
        if hasattr(req,"emotdid") and req.emotdid > 0:#req.form.has_key("id") and int(req.form["id"])>0:
            #emotdid = req.form["id"]
            emotdid = req.emotdid
            kind = None
            if req.form.has_key("cn_netbox"):
                kind = "netbox"

            elif req.form.has_key("cn_room"):
                kind = "room"

            elif req.form.has_key("cn_location"):
                kind = "location"

            if kind:
                for key in req.form.keys():
                    m = re.search("cn_%s_(\w+)"%kind,key)
                    if m:
                        sql = "insert into emotd_related (emotdid,key,value) values (%d, '%s', '%s')" % (int(emotdid), kind, m.group(1))
                        database.execute(sql)
                connection.commit()
            redirect(req,BASEPATH+"add?id=%s" % emotdid)

        else:
            return placemessage(req)
    else:
        page = MaintenanceTemplate(searchList=[nameSpace])
        page.equipment = equipmentlist(emotdid)
        #raise repr(page.equipment)
        #    return page.respond()
        #template = deviceManagementTemplate(searchList=[nameSpace])
        page.path = args['path']
        page.emotdid = emotdid
        return page.respond()

def status(req):
    if req.form.has_key("id"):
        l = []
        if req.form.has_key("cn_netbox"):
            req.write("Add netboxes")
            for key in req.form.keys():
                m = re.search("cn_netbox_(\d+)",key)
                if m:
                    l.append(m.group(1))
        elif req.form.has_key("cn_room"):
            req.write("Add rooms")
            for key in req.form.keys():
                m = re.search("cn_room_(\d+)",key)
                if m:
                    l.append(m.group(1))
        elif req.form.has_key("cn_location"):
            req.write("Add locations")
            for key in req.form.keys():
                m = re.search("cn_location_(\d+)",key)
                if m:
                    l.append(m.group(1))
        req.write(repr(l))
    else:
        req.write("hei")
    return apache.OK

def maintlist(req):
    activedict = EmotdSelect.getMaintenance(state='active',access=True)
    maints = maintparse(activedict)
    ##maints = [s,]
    #args['title'] = title
#    nameSpace = {'title': title, 'motd': None, 'maints': maints, 'menu': menu, 'form':form,'body': body, 'searchBox': searchBox, 'selectBox': selectBox}
    nameSpace = {'title': 'Maintenance List', 'menu': menu,'maints': maints}
    page = MaintListTemplate(searchList=[nameSpace])
    page.path = [('Frontpage','/'),
                 ('Tools','/toolbox'),
                 ('Messages',BASEPATH),
                 ('Maintenance List','')]
    page.body=""
    return page.respond()


def formatEmotd(emotd):
    if emotd.has_key('last_changed'):
        last_changed = emotd['last_changed']
        if not isinstance(last_changed,str):
            #last_changed = DateTime.strptime(last_changed,"%Y-%m-%d")
            emotd['last_changed'] = strftime("%Y-%m-%d %H:%M",last_changed.tuple())
    else:
        emotd['last_changed'] = None
        
    emotd['replaces_title'] = None
    emotd['replaces_title_en'] = None
    #body += emotd['type']
    if emotd.has_key('replaces_emotd') and emotd['replaces_emotd']:
        replaces_emotd = EmotdSelect.get(int(emotd['replaces_emotd']))
        emotd['replaces_title'] = replaces_emotd['title']
        emotd['replaces_title_en'] = replaces_emotd['title_en']

    return emotd

def view(req):
    ''' Show a given MOTD based on the motd_id '''
    page = EmotdFrontpage()#searchList=[nameSpace]
    page.title = 'View MOTD'
    page.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("View","")]
    page.body = ''
    page.access = False
    form = ''
    page.emotds = []
    if not req.form.has_key('id'):
        page.body = 'You must supply a valid MOTD id!'
    else:
        emotdid = req.form['id']
        try:
            emotdid = int(emotdid)
            emotd = EmotdSelect.get(int(req.form['id']))
            emotd = formatEmotd(emotd)
            
            ## sikkerhetskontrollen
            if emotd['type'] != 'internal': 
                page.emotds.append(emotd)
            else:
                if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit') :
                    page.emotds.append(emotd)
                    page.access = True
                else:
                    page.access = False
                    page.body += '<p>Access to current message is currently for NAV users only</p>'
        except ValueError,e:
            page.body += '<font color=red>Invalid literal for MOTD-identification</font>'
    page.menu = getMenu(req)
#    nameSpace = {'title': title, 'emotds': motd, 'searchBox': None, 'menu': menu, 'body': body, 'form': form}
#    if access == True:
#        page.access = True
    return page.respond()
    
def isdefault(a,b):
    if a==b:
        return 'selected=selected'

def placemessage(req):

    page = EmotdMessageTemplate()
    page.title = "Add equipment to message"
    page.path = [("Frontpage", "/"), ("eMotd", BASEPATH),("Add to message","")]
    page.menu = getMenu(req)
    type = None
    eql = []
    if req.form.has_key("cn_netbox"):
        type = "netbox"
        for key in req.form.keys():
            m = re.search("cn_netbox_(\d+)",key)
            if m:
                eql.append(Netbox(m.group(1)))
    elif req.form.has_key("cn_room"):
        type = "room"
        for key in req.form.keys():
            m = re.search("cn_room_(\d+)",key)
            if m:
                eql.append(m.group(1))
    elif req.form.has_key("cn_location"):
        type = "location"
        for key in req.form.keys():
            m = re.search("cn_location_(\d+)",key)
            if m:
                eql.append(m.group(1))

    page.type = type    
    page.equipment_list = eql
    page.emotds = EmotdSelect.fetchAll()
    return page.respond()

def edit(req):
    ''' Edit a given motd_id or new Emotd if motd_id is not given '''
    title = 'Editing as %s ' % (req.session['user'].login)
    EmotdTemplate.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Edit","")]
    id = "None"
    body = ''
    menu = getMenu(req)
    now = DateTime.now()
    week = now + DateTime.oneWeek
    parent_id = None
    form=None
    if req.form.has_key('action'):
        # action can be either followup or change
        action = req.form['action']
        if req.form.has_key('id'):
            if action == 'change':
                #let's edit that existing MOTD
                id = Emotd(req.form['id']).emotdid
                author = Emotd(req.form['id']).author
                description = Emotd(req.form['id']).description
                description_en = Emotd(req.form['id']).description_en
                detail = Emotd(req.form['id']).detail
                detail_en = Emotd(req.form['id']).detail_en
                title = Emotd(req.form['id']).title
                title_en = Emotd(req.form['id']).title_en
            elif action == 'followup':
                parent_id = req.form['id']
                author = Emotd(parent_id).author
                description = Emotd(parent_id).description
                description_en = Emotd(parent_id).description_en
                detail = Emotd(parent_id).detail
                detail_en = Emotd(parent_id).detail_en
                type = Emotd(parent_id).type
                title = Emotd(parent_id).title
                title_en = Emotd(parent_id).title_en
                if title.startswith('Re:'):
                    # do not want Re: Re: Re: as title
                    pass
                else:
                    #title = 'Re:' + Emotd(parent_id).title
                    title = 'Re:' + title
                if title_en.startswith('Re:'):
                    pass
                else:
                    #title = 'Re:' + Emotd(parent_id).title_en
                    title_en = 'Re:' + title_en
            else:
                raise repr('Action not supported.')
        else:
            raise repr('Id missing')
    else:
        id = "None"
        title = '' 
        title_en = ''
        description = ''
        description_en = ''
        detail = ''
        detail_en = ''
        author = req.session['user'].login
    if title_en == None:
        title_en = ''
    if description_en == None:
        description_en = ''
    if detail == None:
        detail = ''
    if detail_en == None:
        detail_en = ''
    now = str(DateTime.now())
    muststar = '<span style="color:red;">*</span>'
    body += '<form action=commit method=post>\n'
    #body += '<table border=0>\n'
    body += '<input type=hidden name=author value=%s>\n' % author
    body += '<input type=hidden name=date_change value=%s>\n' % now
    #body += '<tr><td colspan=2 bgcolor=lightgrey>Put on maintenance: '
    #body += '<i>Set netbox/service/module on maintenance? </i><input type="checkbox" name=maintenance></td></tr>'
    #body += '<tr><td>Active from : <i>Defaults to 1 week</i></td><td>' 
    body += '<ul style="list-style-type:none;marin=0;padding:0;"><li>Active from: ' 
    body += ' Year: <select name=year_start>\n'
    for year in range(2003,2020):
        body += '<option value=' + str(year) 
        if year == int(now[0:4]):
            body += ' selected=selected '
        body += '>' + str(year) + '</option>\n'
    body += '</select>'
    body += ' Month: <select name=month_start>\n'
    for month in range(1,13): 
        body += '<option value=' + str(month) 
        if month == int(now[5:7]):
            body += ' selected=selected '
        body += '>' + str(month) + '</option>\n'
    body += '</select>'
    body += ' Day: <select name=day_start>\n'
    for day in range(1,32): 
        # maybe have some check on the dates.. 31.2. doesn't quite exist
        body += '<option value=' + str(day)
        if day == int(now[8:10]):
            body += ' selected=selected '
        body += '>' + str(day) + '</option>\n'
    body += '</select>'
    body += ' Hour: <select name=hour_start>\n'
    for hour in range(1,25):
        body += '<option value=' + str(hour)
        if hour == int(now[11:13]):
            body += ' selected=selected '
        body += '>' + str(hour) + '</option>\n'
    body += '</select>\n'
    #body += '</td></tr>'
    body += '</li>'
    #body += '<td>Active to:</td><td>'
    body += '<li>Active to:'
    oneweek = str(DateTime.now() + DateTime.oneWeek)
    body += ' Year: <select name=year_end>\n'
    for year in range(2003,2020):
        body += '<option value=' + str(year) 
        if year == int(oneweek[0:4]):
            body += ' selected=selected '
        body += '>' + str(year) + '</option>\n'
    body += '</select>'
    body += ' Month: <select name=month_end>\n'
    for month in range(1,13): 
        body += '<option value=' + str(month)  
        if month == int(oneweek[5:7]):
            body += ' selected=selected '
        body += '>' + str(month) + '</option>\n'
    body += '</select>'
    body += ' Day: <select name=day_end>\n'
    for day in range(1,32): 
        # maybe have some check on the dates.. 31.2. doesn't quite exist
        body += '<option value=' + str(day) 
        if day == int(oneweek[8:10]):
            body += ' selected=selected '
        body += '>' + str(day) + '</option>\n'
    body += '</select>'
    body += ' Hour: <select name=hour_end>\n'
    for hour in range(1,25):
        body += '<option value=' + str(hour)
        if hour == int(oneweek[11:13]):
            body += ' selected=selected '
        body += '>' + str(hour) + '</option>\n'
    body += '</select>\n'
    #body += '</td></tr>\n'
    body += ' <i>Defaults to 1 week</i></li>\n'
    # type-values should be fetched from a table... leave that for later... 
    #body += '<tr><td colspan=2 bgcolor=lightgrey>MOTD type: <font color="red">*</font> <select name=type>\n'
    body += '<li><label>Type</label>%s<select name=type>\n' % muststar
    body += '<option value=info>Informational</option>\n'
    body += '<option value=error>Error</option>\n'
    body += '<option value=internal>Internal </option>\n'
    body += '<option value=scheduled>Scheduled outage</option>\n'
    #body += '</select> <i>Internal will not be publically available - e.g. for NAV users only. </i></td></tr>\n'
    body += '</select> <i>Internal will not be publically available - e.g. for NAV users only. </i></li>\n'
    #body += '<tr>'
    #body += '<td>Title: <font color="red">*</font><input type=text name=title size=20 maxlength=100 value="%s"><i>(Norwegian)</i></td>' % title
    #<li><div><ul>
    body += '<li><table><tr><td><h2>%s</h2><ul style="list-style-type:none;marin=0;padding:0;">' % LANG1
    body += '<li><label>Title</label><font color="red">*</font><input type=text name=title size=20 maxlength=100 value="%s">' % title
    body += '<li><label>Estimated downtime</label><textarea wrap="hard" name="downtime" rows=2 cols=30>%s</textarea></li>'
    body += '<li><label>Affected end users</label><textarea wrap="hard" name="affected" rows=2 cols=30>%s</textarea></li>'
    body += '<li><label>Description</label>%s<textarea wrap="hard" name="description" rows=8 cols=30>%s</textarea></li>\n' % (muststar,detail)
    body += '<li><label>Details</label><textarea wrap="hard" name="detail" rows=8 cols=30>%s</textarea></li>\n' % detail
    body += '</ul></td><td><h2>%s</h2><ul style="list-style-type:none;marin=0;padding:0;">' % LANG2
    body += '<li><label>Title</label><input type=text name=title_en size=20 maxlength=100 value="%s"></li>' % title_en
    body += '<li><label>Estimated downtime</label><textarea wrap="hard" name="downtime_en" rows=2 cols=30>%s</textarea></li></li>'
    body += '<li><label>Affected end users</label><textarea wrap="hard" name="affected_en" rows=2 cols=30>%s</textarea></li>'
    body += '<li><label>Description</label><textarea wrap="hard" name="description_en" rows=8 cols=30>%s</textarea></li>\n' % description_en
    body += '<li><label>Details</label><textarea wrap="hard" name="detail_en" rows=8 cols=30>%s</textarea></li>\n' % detail_en
    body += '</ul></td></tr></table></li>'
     
##     body += '<td><input type=text name=title_en size=20 maxlength=100 value="%s"><i>(English)</i></td>' % title_en
##     body += '</tr>'
##     body += '<tr><td align=right>Estimated downtime: <i>(freetext)</i> <input type=text name=downtime size=20 maxlength=100> <i>(Norwegian)</i></td>'
##     body += '<td><input type=text name=downtime_en size=20 maxlength=100> <i>(English)</i></td></tr>'
##     body += '<tr><td align=right>Affected end users: <i>(freetext)</i> <input type=text name=affected size=20 maxlength=100> <i>(Norwegian)</i></td>'
##     body += '<td><input type=text name=affected_en size=20 maxlength=100> <i>(English)</i></td></tr>'
##     body += '<tr>'
##     body += '<td>Norwegian Description: <font color="red">*</font> </td>\n'
##     body += '<td>English Description:</td>\n'
##     body += '</tr>'
##     body += '<tr>'
##     body += '<td><textarea wrap="hard" name="description" rows=8 cols=30>%s</textarea></td>\n' % description
##     body += '<td><textarea wrap="hard" name="description_en" rows=8 cols=30>%s</textarea></td>\n' % description_en
##     body += '</tr>'
##     body += '<tr>'
##     body += '<td>Details in Norwegian:</td>\n'
##     body += '<td>Details in English:</td>\n'
##     body += '</tr>'
##     body += '<tr>'
##     body += '<td><textarea wrap="hard" name="detail" rows=8 cols=30>%s</textarea></td>\n' % detail
##     body += '<td><textarea wrap="hard" name="detail_en" rows=8 cols=30>%s</textarea></td>\n' % detail_en
##     body += '</tr>'
    if id != "None":
        body += '<input type=hidden name=emotdid value=%s>' % id
    #if req.form.has_key('parent_id'):
    if parent_id:
        body += '<input type=hidden name=parent_id value=%s>' % parent_id #req.form['parent_id']
        #buttonValue = 'Add'
    #else:
        #buttonValue = 'Submit'
    buttonValue = 'Save'
    #body += '<tr><td colspan=2 align=center><input type=submit name=submitbutton value=%s></td></tr>\n' % buttonValue
    body += '</ul>'
    body += '<input type=submit name="cn_save" value="%s">\n' % (buttonValue + " this message")
    body += '<input type=submit name="cn_save_and_add" value="%s">\n' % (buttonValue + " and add equipment to this message")
    body += '</form>\n'
    #body += '</table>'

    selectBox = None
    searchBox = None
    motd = None 
    nameSpace = {'title': title, 'motd': motd, 'selectBox': selectBox, 'searchBox': searchBox,'menu': menu, 'body': body,'form':form}
    page = EmotdStandardTemplate(searchList=[nameSpace])
    return page.respond()

def commit(req):
    ''' Commit MOTD into database. Leave motd_id blank for new Message.
        Required fields: author,date,date_start,date_end,type,title,description
    '''
    title = 'Commit MOTD'
    menu = getMenu(req)
    form = ''
    body = ''
    #raise repr(req.form.list)
    # do some checking to see whether we got all required fields
    if req.form.has_key('emotdid'):
        m = Emotd(req.form['emotdid'])
        exist = True
    else:
        # if no id, make a new MOTD
        exist = False
        m = Emotd()
    # does this motd replace another?
    if req.form.has_key('parent_id'):
        m.replaces_emotd = req.form['parent_id']
        Emotd(req.form['parent_id']).publish_end = DateTime.now()
    # Last changed
    m.last_changed = DateTime.now()
    # publish-period
    #if req.form['type'] != 'internal':
    year_start = int(req.form['year_start'])
    month_start = int(req.form['month_start'])
    day_start = int(req.form['day_start'])
    hour_start = int(req.form['hour_start'])
    year_end = int(req.form['year_end'])
    month_end = int(req.form['month_end'])
    day_end = int(req.form['day_end'])
    hour_end = int(req.form['hour_end'])
    m.publish_start = DateTime.Date(year_start,month_start,day_start,hour_start)
    m.publish_end = DateTime.Date(year_end,month_end,day_end,hour_end)
    #else:
    #    m.publish_start = DateTime.now()
    #    m.publish_end = DateTime.now()
    m.published = False
    # error or informational?
    m.type = req.form['type']   
    if req.form.has_key('affected'):
        m.affected = req.form['affected']
    # freetext description of estimated dowmtime-period
    if req.form.has_key('downtime'):
        m.downtime = req.form['downtime']
    m.title = req.form['title'] # must have local title
    m.title_en = req.form['title_en'] or ""
    m.author = req.form['author']
    desc = ""
    for line in req.form['description']:
        desc += line + ' \n ' 
    desc_en = ""
    for line in req.form['description_en']:
        desc_en += line + ' \n '
    #m.description = desc
    #m.description_en = desc_en 
    m.description = req.form['description']
    m.description_en = req.form['description_en']
    m.detail = req.form['detail']
    m.detail_en = req.form['detail_en']

    # Save new or existing MOTD
    m.save()
    if exist:
        body += 'Changes commited'
    else:
        body += 'New MOTD added <p>'
        if req.form.has_key('maintenance'):
            if req.form['maintenance'] == 'on':
                body += '<p><a href=/emotd/maintenance?id=%s ' % m.emotdid 
                if req.form.has_key('service'):
                    body += '&service=%s' % req.form['service']
                if req.form.has_key('netbox'):
                    body += '&netbox=%s' % req.form['netbox']
                body += '>Maintenenace</a> administration for current Emotd' 
    #nameSpace = {'title': title, 'motd': None,'searchBox': None, 'menu': menu, 'body': body}
    #page = EmotdTemplate(searchList=[nameSpace])
    #return page.respond()
    if req.form.has_key("cn_save"):
        redirect(req,"%sview?id=%s" % (BASEPATH, m.emotdid))
    elif req.form.has_key("cn_save_and_add"):
        redirect(req,"%sadd?id=%s" % (BASEPATH, m.emotdid))
    return apache.OK

