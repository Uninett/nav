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
from nav.web.templates.EditTemplate import EditTemplate
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
        if len(path)>1:
            output = view(req,path[1])
        else:
            output = view(req)
    elif path[0] == 'maintenance':
        output = maintlist(req)
    elif path[0] == 'add':
        output = maintenance(req)
    elif path[0] == 'commit':
        output = commit(req)        
    elif path[0] == 'committime':
        output = committime(req)
        
    elif path[0] == 'time':
        output = mainttime(req)
    else:
        output = view(req)

    if output:
        req.content_type = "text/html"
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND

class MenuItem:

    def __init__(self,link,text):
        self.link = link
        self.text = text
        
def getMenu(req):
    # Only show menu if logged in user
    # Should have some fancy icons and shit
    menu = []
    menu.append(MenuItem("active","Active"))
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        menu.append(MenuItem("scheduled","Scheduled"))
        menu.append(MenuItem("old","Old"))

    menu.append(MenuItem("maintenance","Maintenance"))
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        menu.append(MenuItem("edit","New message"))
        #menu.append(MenuItem("maintenance","Set on maintenance"))
    return menu

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
    def __init__(self, mess, user, equipment):# emotdid, last_changed, author, title, description, detail, affected, downtime, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd, key, value):
        #raise(repr(args))
        (emotdid, last_changed, author, title, description, detail, affected, downtime, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd) = mess[0:16]
        self.emotdid = emotdid
        if not isinstance(last_changed, str):
            last_changed = strftime("%Y-%m-%d %H:%M",last_changed.tuple())
        self.replaces_title = ""
        if replaces_emotd:
            database.execute("select title from emotd where emotdid=%d" % int(replaces_emotd))
            row = database.fetchone()
            if row:
                self.replaces_title = row[0]
        self.own = False
        if user == author:
            self.own = True
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
    page = EmotdFrontpage() 
    page.title = 'Current active messages'
    page.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),(page.title,"")]
    page.menu = getMenu(req)

    page.emotds = getEmotds(req.session['user'])
    return page.respond()

def view(req, view = None):

    user = req.session['user']

    access = False
    if nav.auth.hasPrivilege(user,'web_access','/emotd/edit'):
        access = True

    where = ""
    if view:

        try:
            page = EmotdFrontpage()
            page.title = "View message"
            page.statustype = view

            id = int(view)
            where = "emotdid=%d" % id
            
        except ValueError:
            page = EmotdFrontpage()
            page.statustype = view
            if access and view == "all":
                where = ""
            elif access and view == "scheduled":
                where = "publish_start > now()"
            elif access and view == "old":
                where = "publish_end < now()"
            else:
                where = "publish_end > now() and publish_start < now()"
                page.statustype = "active"
            page.title = "View %s messages" % page.statustype
    else:
        page = EmotdFrontpage()
        page.statustype = "active"
        page.title = "View %s messages" % page.statustype
        where = "publish_end > now() and publish_start < now()"
    
    emotds = []
    if not access:
        if len(where):
            # må koordineres med view == "all" lenger opp
            where += " and type != 'internal'"

    if len(where):
        where = "where " + where
        
    sql = "select emotdid, key, value from emotd left outer join emotd_related using (emotdid) %s order by last_changed desc" % where
    database.execute(sql)

    equipment = {}
    for (emotdid, key, value) in database.fetchall():
        if not equipment.has_key(emotdid):
            equipment[emotdid] = {}
        if not equipment[emotdid].has_key(key):
            equipment[emotdid][key] = []
        equipment[emotdid][key].append(value)

    sql = "select emotdid, last_changed, author, title, description, detail, affected, downtime, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd from emotd %s order by last_changed desc" % where
    database.execute(sql)
    eq = {}
    for emotd in database.fetchall():
        emotdid = emotd[0]
        if equipment.has_key(emotdid):
            eq = equipment[emotdid]
        emotds.append(Message(emotd,user.login,equipmentformat(eq)))
        
    page.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),(page.title,"")]
    page.menu = getMenu(req)

    page.emotds = emotds
    return page.respond()
    #return emotds

def equipmentlist(emotdid):

    sql = "select emotdid, key, value from emotd left outer join emotd_related using (emotdid) where emotdid=%d order by publish_end desc" % int(emotdid)
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

## def maintparse(maintdict):
##     maints = []
##     for maint in maintdict.keys():
##         mstart = maintdict[maint][0]['maint_start'].strftime(DATEFORMAT)
##         mend   = maintdict[maint][0]['maint_end'].strftime(DATEFORMAT)
##         emotdid = int(maintdict[maint][0]['emotdid'])
##         ##title = Emotd(emotdid).title
##         ##emotdurl = "<a href=/emotd/view?id=%s> %s </a>" % (emotdid,title) 
##         for f in range(len(maintdict[maint])):
##             # One maintenance, can keep severel rooms,netbox,services
##             entry = maintdict[maint][f]
##             if entry['key'] == 'room':
##                 roomid = entry['value']
##                 database.execute("select descr from room where roomid='%s'" % roomid)
##                 entry['roomid'] = roomid 
##                 entry['roomdesc'] = database.fetchone()[0]
##                 entry['netboxid'] = None
##                 entry['serviceid'] = None
##             if entry['key'] == 'netbox':
##                 netboxid = int(entry['value'])
##                 database.execute("select sysname,netbox.roomid,descr from netbox left outer join room using(roomid) where netboxid=%d" % netboxid)
##                 (entry['netboxid'], entry['roomid'], entry['roomdesc']) = database.fetchone()
##                 entry['serviceid'] = None
##             if entry['key'] == 'service':
##                 serviceid = int(entry['value'])
##                 database.execute("select handler, sysname, netboxi.roomid, roomdesc from service left outer join netbox using (netboxid) left outer join room using (roomid) where serviceid = %d" % serviceid)
##                 (entry['serviceid'], entry['netboxid'], entry['roomid'], entry['roomdesc']) = database.fetchone()
##             entry['mstart'] = mstart
##             entry['mend'] = mend
##             database.execute("select title from emotd where emotdid = %d" % emotdid)
##             entry['title'] = database.fetchone()[0]
##             entry['emotdid'] = emotdid
##             maints.append(entry)
##     return maints

class MaintElement:

    def __init__(self, emotdid, emotdtitle, key, value, description, start, end, state):
        self.emotdid = emotdid
        self.title = emotdtitle
        self.key = key
        self.value = value
        self.description = description
        self.start = start
        self.end = end
        self.state = state
        

def maintlist(req):
    #activedict = EmotdSelect.getMaintenance(state='active',access=True)
    sql = "select emotd.emotdid, key, value, maint_start, maint_end, title, state from emotd_related left outer join emotd using (emotdid) left outer join maintenance using (emotdid) where type != 'internal' "
    database.execute(sql)
    maints = database.fetchall()
    maintlist = []
    for (emotdid, key, value, start, end, title, state) in maints:
        if key == 'room':
            database.execute("select descr from room where roomid='%s'" % value)
            descr = "%s (%s)" % (value,database.fetchone()[0])
        elif key == 'location':
            database.execute("select descr from location where locationid='%s'" % value)
            descr = "%s (%s)" % (value,database.fetchone()[0])
        elif key == 'netbox':
            database.execute("select sysname from netbox where netboxid=%d" % int(value))
            descr = database.fetchone()[0]
        elif key == 'service':
            database.execute("select handle from service where serviceid=%d" % int(value))
            descr = database.fetchone()[0]
        elif key == 'module':
            database.execute("select module, descr from module where moduleid=%d" % int(value))
            descr = database.fetchone()[0]
        else:
            raise repr("Unsupported equipment type")
        maintlist.append(MaintElement(emotdid,title,key,value,descr,start,end,state))

    page = MaintListTemplate()
    page.menu = getMenu(req)
    page.maints = maintlist
    page.title = 'Maintenance List'
    page.path = [('Frontpage','/'),
                 ('Tools','/toolbox'),
                 ('Messages',BASEPATH),
                 (page.title,'')]
    return page.respond()


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
    page = EmotdFrontpage()
    page.title = "Published messages"
    page.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),(page.title,"")]
    page.menu = getMenu(req)

    page.emotds = getEmotds(req.session['user'],"all")
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
            body += '<link>http://isbre.itea.ntnu.no/emotd/view/%(emotdid)s </link>' % row
            body += '</item>\n'
    # and this will be the tail of the feed
    body += '</rdf:RDF>\n\n'
    if client:
        if client == "html":
            body += '</pre></body></html>'
    return body


def mainttime(req):

    page = MaintTimeTemplate()

    req.ny = False
    if req.form.has_key("id"):
        req.emotdid = int(req.form["id"])

    if hasattr(req,"emotdid"):
        database.execute("select maint_start,maint_end from maintenance where emotdid=%d" % req.emotdid)
        maintenance = database.fetchone()
        if maintenance:
            start = maintenance[0]
            end = maintenance[1]
        else:
            start = DateTime.now()
            end = DateTime.now() + DateTime.RelativeDateTime(days=+7)
            req.ny = True
        
        (year,month,day,hour,minute) = start.tuple()[0:5]
        if not maintenance:
            minute = 0
        page.start = (year,month,day,hour,minute)
        (year,month,day,hour,minute) = end.tuple()[0:5]
        if not maintenance:
            minute = 0
        page.end = (year,month,day,hour,minute)
        page.action = BASEPATH + "committime"
        page.emotdid = req.emotdid
        page.ny = req.ny
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
    sql = "select emotd.emotdid, key, value, maint_start, maint_end, title, state from emotd_related left outer join emotd using (emotdid) left outer join maintenance using (emotdid) where type != 'internal' "
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



## def formatEmotd(emotd):
##     if emotd.has_key('last_changed'):
##         last_changed = emotd['last_changed']
##         if not isinstance(last_changed,str):
##             #last_changed = DateTime.strptime(last_changed,"%Y-%m-%d")
##             emotd['last_changed'] = strftime("%Y-%m-%d %H:%M",last_changed.tuple())
##     else:
##         emotd['last_changed'] = None
        
##     emotd['replaces_title'] = None
##     emotd['replaces_title_en'] = None
##     #body += emotd['type']
##     if emotd.has_key('replaces_emotd') and emotd['replaces_emotd']:
##         replaces_emotd = EmotdSelect.get(int(emotd['replaces_emotd']))
##         emotd['replaces_title'] = replaces_emotd['title']
##         emotd['replaces_title_en'] = replaces_emotd['title_en']

##     return emotd


## todo: slå sammen med viewall/active, hvis ikke emtodid.

def viewtest(req,id=None):
    if id:
        id = int(id)
    page = EmotdFrontpage()
    page.title = "View message"
    page.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),(page.title,"")]
    page.menu = getMenu(req)

    page.emotds = getEmotds(req.session['user'],id)
    return page.respond()
    

def viewold(req):
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
    page.emotds = (req.session['user'],1)#EmotdSelect.fetchAll()
    return page.respond()

def edit(req, id = None):
    ''' Edit a given motd_id or new Emotd if motd_id is not given '''
    page = EditTemplate()
    #title = 'Editing as %s ' % (req.session['user'].login)
    page.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Edit","")]
    page.menu = getMenu(req)
    page.parent_id = None
    page.emotdid = None
    
    if id:
        #finnes fra før
        page.emotdid = int(req.form["id"])
        sql = "select author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, published_start, published_end from emotd where emotdid=%d" % page.emotdid
        database.execute(sql)
        (page.author, page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en, page.type, page.published_start, page.published_end) = database.fetchone()

        change = 0
        if req.session['user'].login == author:
            # change
            change = 1
            page.pagetitle = "Change eMotD Message"
        else:
            # followup
            page.author = req.session['user'].login
            if not page.title.startswith('Re:'):
                page.title = 'Re:' + title
            if page.title_en.startswith('Re:'):
                page.title_en = 'Re:' + title_en
            page.parent_id = page.emotdid
            page.emotdid = None
            page.pagetitle = "Make Followup Message"

    else:
        page.author = req.session['user'].login
        page.published_start = DateTime.now()
        page.published_end = DateTime.now() + DateTime.RelativeDateTime(days=+7)
        (page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en) = [""] * 10

    page.last_changed = str(DateTime.now())
    for a in (page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en):
        if a == None:
            a = ""
            
    (year,month,day,hour,minute) = published_start.tuple()[0:5]
    if not id:
        minute = 0
    page.published_start = (year,month,day,hour,minute)
    (year,month,day,hour,minute) = published_end.tuple()[0:5]
    if not id:
        minute = 0
    page.published_end = (year,month,day,hour,minute)

    page.primary_language = LANG1
    page.secondary_language = LANG2

    return page.respond()

def committime(req):
    if req.form.has_key("id"):
        req.emotdid = int(req.form["id"])
    if req.form.has_key("ny"):
        req.ny = req.form["ny"]
    if hasattr(req,"emotdid"):
        req.emotdid = int(req.emotdid)
        start = DateTime.DateTime(int(req.form["start_year"]),int(req.form["start_month"]),int(req.form["start_day"]),int(req.form["start_hour"]),int(req.form["start_minute"]))
        end = DateTime.DateTime(int(req.form["end_year"]),int(req.form["end_month"]),int(req.form["end_day"]),int(req.form["end_hour"]),int(req.form["end_minute"]))
        if hasattr(req,"ny") and req.ny:
            sql = "insert into maintenance (emotdid,maint_start,maint_end) values (%d,'%s','%s')" % (req.emotdid, start.strftime("%Y-%m-%d %H:%M"), end.strftime("%Y-%m-%d %H:%M"))
        else:
            sql = "update maintenance set maint_start='%s', maint_end='%s' where emotdid=%d" % (start.strftime("%Y-%m-%d %H:%M"), end.strftime("%Y-%m-%d %H:%M"), req.emotdid)
        database.execute(sql)
        connection.commit()
        redirect(req,"%sadd?id=%s" % (BASEPATH,req.emotdid))
    else:
        raise repr("ERROR: Coud not retrieve ID")
        
def commit(req):
    ''' Commit MOTD into database. Leave motd_id blank for new Message.
        Required fields: author,date,date_start,date_end,type,title,description
    '''
    form = ''
    body = ''
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
    if req.form.has_key("cn_save"):
        redirect(req,"%sview/%s" % (BASEPATH, m.emotdid))
    elif req.form.has_key("cn_save_and_add"):
        redirect(req,"%stime?id=%s" % (BASEPATH, m.emotdid))
    return apache.OK

