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
from nav.web.templates.ViewMessageTemplate import ViewMessageTemplate
from nav.web.templates.EditTemplate import EditTemplate
from nav.web.templates.TreeSelectTemplate import TreeSelectTemplate

#################################################
## Module constants

title = 'Message of the day'
menu = ''

EmotdTemplate.path =  [("Home", "/"), ("eMotd", "/emotd")]
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
        if len(path)>1:
            output = edit(req,path[1])
        else:
            output = edit(req)
    elif path[0] == 'view':
        if len(path)>1:
            output = view(req,path[1])
        else:
            output = view(req)
    elif path[0] == 'maintenance':
        output = maintlist(req)
    elif path[0] == 'add':
        if len(path)>1:
            output = maintenance(req,path[1])
        else:
            output = maintenance(req)
    elif path[0] == 'commit':
        output = commit(req)        
    elif path[0] == 'committime':
        output = committime(req)
    elif path[0] == 'commitplacement':
        output = commitplacement(req)
    elif path[0] == 'time':
        if len(path)>1:
            output = mainttime(req,path[1])
        else:
            output = mainttime(req)
    elif path[0] == 'remove':
        if len(path)>1:
            output = remove(req,path[1])
        else:
            output = remove(req)
    elif path[0] == 'set':
        output = placemessage(req)
    else:
        output = view(req,"active")

    if output:
        req.content_type = "text/html"
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND

class MenuItem:

    def __init__(self,link,text):
        self.link = BASEPATH+link
        self.text = text
        
def getMenu(req):
    # Only show menu if logged in user
    # Should have some fancy icons and shit
    menu = []
    menu.append(MenuItem("view/active","Active"))
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        menu.append(MenuItem("view/scheduled","Scheduled"))
        menu.append(MenuItem("view/old","Old"))

    menu.append(MenuItem("maintenance","Maintenance"))
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        menu.append(MenuItem("edit","New message"))
        #menu.append(MenuItem("maintenance","Set on maintenance"))
    return menu

def search(req):
    ''' Free-text search in MOTD-db '''
    title = 'MOTD freetext search'
    EmotdTemplate.path =  [("Home", "/"), ("eMotd", "/emotd"),("Search","")]
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
                 

def view(req, view = None, lang = None):

    user = req.session['user']
    menu = getMenu(req)
    
    where = ""
    if not view:
        view = "active"

    list = 1
    try:
        view = int(view)
        list = 0

    except ValueError:
        list = 1

    if list:
        return messageList(view, user, menu)
    else:
        return messageView(view, user, lang)

def messageView(view, user, lang = None):
    access = False
    if nav.auth.hasPrivilege(user,'web_access','/emotd/edit'):
        access = True

    where = "emotdid=%d" % view
    page = ViewMessageTemplate()

    if not access:
        if len(where):
            # må koordineres med view == "all" lenger opp
            where += " and type != 'internal'"
            
    where = "where " + where

    sql = "select key, value from emotd_related %s" % where
    database.execute(sql)
    equipment = {}
    for (key, value) in database.fetchall():
        if not equipment.has_key(key):
            equipment[key] = []
        equipment[key].append(value)

    if lang:
        sql = "select emotdid, type, publish_start, publish_end, last_changed, author, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd, maint_start, maint_end, state from emotd left outer join maintenance using (emotdid) %s order by last_changed desc" % where
    else:
        sql = "select emotdid, type, publish_start, publish_end, last_changed, author, title, description, detail, affected, downtime, replaces_emotd, maint_start, maint_end, state from emotd left outer join maintenance using (emotdid) %s order by last_changed desc" % where
        
    database.execute(sql)
    (page.emotdid, page.type, page.publishstart, page.publishend, page.last_changed, page.author, page.title, page.description, page.detail, page.affected, page.downtime, page.replaces_emotd, page.maintstart, page.maintend, page.state) = database.fetchone()
    if page.publishstart:
        page.publishstart = page.publishstart.strftime(DATEFORMAT)
    if page.publishend:
        page.publishend = page.publishend.strftime(DATEFORMAT)
    if page.maintstart:
        page.maintstart = page.maintstart.strftime(DATEFORMAT)
    if page.maintend:
        page.maintend = page.maintend.strftime(DATEFORMAT)
    if page.last_changed:
        page.last_changed = page.last_changed.strftime(DATEFORMAT)
    if page.description:
        page.description = textpara(page.description)
    if page.detail:
        page.detail = textpara(page.detail)
    if page.replaces_emotd:
        database.execute("select title from emotd where emotdid=%d" % int(page.replaces_emotd))
        row = database.fetchone()
        if row:
            page.replaces_title = row[0]
    emotdid = int(page.emotdid)
    eq = {}
    if len(equipment):
        eq = equipmentformat(equipment)
    page.maintlist = eq
    page.access = access
    page.action =""
    return page.respond()

def messageList(view, user, menu = ""):
    access = False
    if nav.auth.hasPrivilege(user,'web_access','/emotd/edit'):
        access = True

    
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
        
    page.path =  [("Home", "/"), ("eMotd", "/emotd"),(page.title,"")]
    page.menu = menu

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
                try:
                    database.execute("select descr from location where locationid = '%s'" % l)
                    resdict["location"].append((l, "%s (%s)" % (l,database.fetchone()[0])))
                except:
                    resdict["location"].append((l,l))

        if eqdict.has_key("room"):
            resdict["room"] = []
            for l in eqdict["room"]:
                try:
                    database.execute("select descr from room where roomid = '%s'" % l)
                    resdict["room"].append((l,"%s (%s)" % (l,database.fetchone()[0])))
                except:
                    resdict["room"].append((l,l))
                    
        if eqdict.has_key("netbox"):
            resdict["netbox"] = []
            for l in eqdict["netbox"]:
                try:
                    database.execute("select sysname from netbox where netboxid = '%s'" % l)
                    resdict["netbox"].append((l,database.fetchone()[0]))
                except:
                    resdict["netbox"].append((l,l))
        if eqdict.has_key("service"):
            resdict["service"] = []
            for l in eqdict["service"]:
                try:
                    database.execute("select sysname from handler, netbox inner join service using (netboxid) where serviceid = '%s'" % l)
                    resultat = database.fetchone()
                    resdict["service"].append((l,"%s (%s)" % (resultat[0], resultat[1])))
                except:
                    resdict["service"].append((l,l))
    return resdict

def textpara(text):
    text = re.sub("\n+", "</p><p>", text)
    return "<p>" + text + "</p>"


class MaintElement:

    def __init__(self, emotdid, emotdtitle, key, value, description, start, end, state):
        self.emotdid = emotdid
        self.title = emotdtitle
        self.key = key
        self.value = value
        self.description = description
        if start:
            start = start.strftime(DATEFORMAT)
        if end:
            end = end.strftime(DATEFORMAT)
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
            try:
                database.execute("select descr from room where roomid='%s'" % value)
                descr = "%s (%s)" % (value,database.fetchone()[0])
            except:
                descr = value
        elif key == 'location':
            try:
                database.execute("select descr from location where locationid='%s'" % value)
                descr = "%s (%s)" % (value,database.fetchone()[0])
            except:
                descr = value
        elif key == 'netbox':
            try:
                
                database.execute("select sysname from netbox where netboxid=%d" % int(value))
                descr = database.fetchone()[0]
            except:
                descr = key + value
        elif key == 'service':
            try:
                database.execute("select handle from service where serviceid=%d" % int(value))
                descr = database.fetchone()[0]
            except:
                descr = key + value
        elif key == 'module':
            try:
                database.execute("select module, descr from module where moduleid=%d" % int(value))
                descr = database.fetchone()[0]
            except:
                descr = key + value
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


def mainttime(req, id = None):

    page = MaintTimeTemplate()

    req.ny = False
    if id:
        req.emotdid = int(id)

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


def maintenance(req, id = None):
    ''' Put locations,rooms,netboxes,modules,services on maintenance to prevent 
        alerts being sent while doing maintenance. Also views current/ongoing 
        maintenance.
    '''
    args = {}
    form = ''
    body = ''
    title = 'Set on maintenance'
    ##menu = getMenu(req)

    args['path'] = [('Frontpage','/'),
                    ('Tools','/toolbox'),
                    ('Messages',BASEPATH)]
    if not hasattr(req,"emotdid"):
        req.emotdid = 0
        if id:
            req.emotdid = int(id)
    emotdid = req.emotdid
    if not emotdid:
        emotdid = 0
        
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

    if emotdid:
        args['action'] = BASEPATH + 'add/' + str(emotdid)
    else:
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

    if emotdid:
        doneaction = BASEPATH + "view/" + str(emotdid)
        donetext = "Return to message view"
    else:
        doneaction = BASEPATH + "set"
        donetext = "Next: Select message"
    args['cancel'] = {'control': "cancel",
                    'value': "Cancel",
                    'enabled': True}
    
    args['cancelaction'] = BASEPATH + "cancel"    
    donename = "cn_done"

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
    if req.form.has_key('cn_add_boxes'):
        args['action'] = BASEPATH + 'maintenance'
       
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

    args['submit'] = {'control': buttonkey,
                      'value': buttontext,
                      'enabled': validSelect}
    args['done'] = {'control': donename,
                    'value': donetext,
                    'enabled': True}
    args['doneaction'] = doneaction

    args['selectbox'] = selectbox


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
    
    #if req and req.form.has_key('list'): ##alltid med nå
    body = ""
    args['title'] = title
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
            redirect(req,BASEPATH+"add/%s" % emotdid)

        else:
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
                        if not req.session.has_key('equipment'):
                            req.session['equipment'] = {}
                        if not req.session['equipment'].has_key(kind):
                            req.session['equipment'][kind] = []
                        req.session['equipment'][kind].append(m.group(1))
                req.session.save()
            redirect(req,BASEPATH+"add")
    else:
        page = MaintenanceTemplate(searchList=[nameSpace])
        page.remove = 0
        if emotdid:
            page.remove = 1
            page.equipment = equipmentlist(emotdid)
        else:
            emotdid = 0
            if req.session.has_key('equipment'):
                page.equipment = equipmentformat(req.session['equipment'])
            else:
                page.equipment = []
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


def isdefault(a,b):
    if a==b:
        return 'selected=selected'

def placemessage(req, lang = None):

    page = EmotdMessageTemplate()
    page.title = "Add equipment to message"
    page.path = [("Home", "/"), ("eMotd", BASEPATH),("Add to message","")]
    #page.menu = getMenu(req)
    type = None
    eql = {}
    page.emotdid = 0

    if req.args:
        params = req.args
        if not req.session.has_key("equipment"):
            req.session["equipment"] = {}
        types = params.split("&")
        for t in types:
            (key,vals) = t.split("=")
            for val in vals.split(","):
                if not req.session["equipment"].has_key(key):
                    req.session["equipment"][key] = []
                req.session["equipment"][key].append(val)
    else:
        page.remove = 1

    if req.session.has_key("equipment"):
        eql = equipmentformat(req.session["equipment"])

    if lang:
        sql = "select emotdid, title_en, description_en from emotd where publish_end>now() order by publish_end desc"
    else:
        sql = "select emotdid, title, description from emotd where  publish_end>now() order by publish_end desc"
    database.execute(sql)

    messages = []
    for (emotdid,title,description) in database.fetchall():
        messages.append((emotdid, title, description))

    page.emotds = messages
    page.type = type    
    page.equipment_list = eql
    ##page.emotds = (req.session['user'],1)#EmotdSelect.fetchAll()
    return page.respond()

def edit(req, id = None):
    ''' Edit a given motd_id or new Emotd if motd_id is not given '''
    page = EditTemplate()
    #title = 'Editing as %s ' % (req.session['user'].login)
    page.path =  [("Home", "/"), ("eMotd", "/emotd"),("Edit","")]
    page.pagetitle = "Edit eMotD"
    page.menu = getMenu(req)
    page.parent_id = None
    page.emotdid = None
    
    if id:
        #finnes fra før
        page.emotdid = int(id)
        sql = "select author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, publish_start, publish_end from emotd where emotdid=%d" % page.emotdid
        database.execute(sql)
        (page.author, page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en, page.type, page.publish_start, page.publish_end) = database.fetchone()

        change = 0
        if req.session['user'].login == page.author:
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
        page.publish_start = DateTime.now()
        page.publish_end = DateTime.now() + DateTime.RelativeDateTime(days=+7)
        (page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en) = [""] * 10
        page.pagetitle = "Make new eMotD"

    page.last_changed = str(DateTime.now())
    for a in (page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en):
        if a == None:
            a = ""
            
    (year,month,day,hour,minute) = page.publish_start.tuple()[0:5]
    if not id:
        minute = 0
    page.publish_start = (year,month,day,hour,minute)
    (year,month,day,hour,minute) = page.publish_end.tuple()[0:5]
    if not id:
        minute = 0
    page.publish_end = (year,month,day,hour,minute)

    page.primary_language = LANG1
    page.secondary_language = LANG2

    page.action = BASEPATH + "commit"

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
            database.execute(sql)
            connection.commit()
            redirect(req,"%sadd/%s" % (BASEPATH,req.emotdid))
        else:
            sql = "update maintenance set maint_start='%s', maint_end='%s' where emotdid=%d" % (start.strftime("%Y-%m-%d %H:%M"), end.strftime("%Y-%m-%d %H:%M"), req.emotdid)
            database.execute(sql)
            connection.commit()
            redirect(req,"%sview/%s" % (BASEPATH,req.emotdid))

    else:
        raise repr("ERROR: Coud not retrieve ID")
        
def commit(req):
    ''' Commit MOTD into database. Leave motd_id blank for new Message.
        Required fields: author,date,date_start,date_end,type,title,description
    '''
    start = DateTime.DateTime(int(req.form["publish_start_year"]),int(req.form["publish_start_month"]),int(req.form["publish_start_day"]),int(req.form["publish_start_hour"]),int(req.form["publish_start_minute"]))
    end = DateTime.DateTime(int(req.form["publish_end_year"]),int(req.form["publish_end_month"]),int(req.form["publish_end_day"]),int(req.form["publish_end_hour"]),int(req.form["publish_end_minute"]))
    
    # Last changed
    last_changed = DateTime.now()
    
    # publish-period
    published = False
    # error or informational?
    type = req.form['type']   
    affected = req.form['affected']
    affected_en = req.form['affected']
    downtime = req.form['downtime']
    downtime_en = req.form['downtime']
    title = req.form['title'] # must have local title
    title_en = req.form['title_en'] or ""
    author = req.form['author']
#    desc = ""
#    for line in req.form['description']:
#        desc += line + ' \n ' 
#    desc_en = ""
#    for line in req.form['description_en']:
#        desc_en += line + ' \n '
    description = req.form['description']
    description_en = req.form['description_en']
    detail = req.form['detail']
    detail_en = req.form['detail_en']

    # Save new or existing MOTD
    if req.form.has_key("parent_id") and req.form["parent_id"]:
        replaces = int(req.form["parent_id"])
        #oppdater published end
        database.execute("update emotd set publish_end='%s' where emotdid=%d" % (DateTime.now(),replaces))
        #lag ny
        database.execute("select nextval('emotd_emotdid_seq')")
        emotid = int(database.fetchone()[0])
        database.execute("insert into emotd (emotdid, author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, publish_start, publish_end, replaces_emotd, last_changed) values (%d, '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%d,'%s')" % (emotdid, author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, start, end, parent_id, last_changed))
    
    elif req.form.has_key('emotdid') and req.form["emotdid"]:
        emotdid = int(req.form["emotdid"])
        database.execute("update emotd set description='%s', description_en='%s', detail='%s', detail_en='%s', title='%s', title_en='%s', affected='%s', affected_en='%s', downtime='%s', downtime_en='%s', type='%s', publish_start='%s', publish_end='%s', last_changed='%s' where emotdid=%d" % (description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, start, end, last_changed, emotdid))
        
    else:
        # if no id, make a new MOTD
        database.execute("select nextval('emotd_emotdid_seq')")
        emotdid = int(database.fetchone()[0])
        database.execute("insert into emotd (emotdid, author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, publish_start, publish_end, last_changed) values (%d, '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % (emotdid, author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, start, end, last_changed))
    connection.commit()
    if req.form.has_key("cn_save"):
        redirect(req,"%sview/%s" % (BASEPATH, emotdid))
    elif req.form.has_key("cn_save_and_add"):
        redirect(req,"%stime/%s" % (BASEPATH, emotdid))
    return apache.OK

def commitplacement(req):
    if req.form.has_key("newmessage"):
        redirect(req,BASEPATH+"edit")
    else:
        if req.form["id"] and req.session.has_key("equipment"):
            el = req.session["equipment"]
            for type,ids in el.items():
                for id in ids:
                    database.execute("select emotdid from emotd_related where emotdid=%d and key='%s' and value='%s'" % (int(req.form["id"]), type, id))
                    already_exists = database.fetchone()
                    if not already_exists:
                        database.execute("insert into emotd_related (emotdid, key, value) values (%d, '%s', '%s')" % (int(req.form["id"]), type, id))
            req.session["equipment"] = {}
            req.session.save()
            connection.commit()
            redirect(req,BASEPATH+"view/"+req.form["id"])
        else:
            raise "noe skjedde"


def remove(req,emotdid = 0):
    if req.args:
        params = req.args
        types = params.split("&")
        for t in types:
            (key,vals) = t.split("=")
            for val in vals.split(","):
                if emotdid:
                    database.execute("delete from emotd_related where emotdid=%d and key='%s' and value='%s'" % (int(emotdid), key, val))
                elif req.session.has_key("equipment") and req.session["equipment"].has_key(key):
                    while req.session["equipment"][key].count(val):
                        req.session["equipment"][key].remove(val)
        connection.commit()
        req.session.save()
    if emotdid:
        redirect(req,BASEPATH+"add/"+str(emotdid))
    else:
        redirect(req,BASEPATH+"set/")
