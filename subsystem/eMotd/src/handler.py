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
from nav.web.templates.FeederTemplate import FeederTemplate

#################################################
## Module constants

title = 'Message of the day'
menu = ''

EmotdTemplate.path =  [("Home", "/"), ("Messages", "/emotd")]
DATEFORMAT = "%Y-%m-%d %H:%M"
BASEPATH = '/emotd/'
LIMIT = 20
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
        if len(path)>2:
                output = view(req,path[1],path[2])
        elif len(path)>1:
            output = view(req,path[1])
        else:
            output = view(req)
    elif path[0] == 'maintenance':
        output = maintlist(req)
    elif path[0] == 'rss':
        output = feed(req)
    elif path[0] == 'add':
        if len(path)>1:
            output = maintenance(req,path[1])
        else:
            output = maintenance(req)

    elif path[0] == 'active':
        if len(path)>1:
            output = home(req,"active",path[1])
        else:
            output = home(req,"active")   
    elif path[0] == 'historic':
        if len(path)>1:
            output = home(req,"historic",path[1])
        else:
            output = home(req,"historic")   
    elif path[0] == 'planned':
        if len(path)>1:
            output = home(req,"planned",path[1])
        else:
            output = home(req,"planned")   
            
    elif path[0] == 'commit':
        output = commit(req)
    elif path[0] == 'cancel':
        output = cancelmaintenance(req)
    elif path[0] == 'submit':
        output = submit(req)        
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
        output = home(req,"active")

    if output:
        req.content_type = "text/html"
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND

class MenuItem:

    def __init__(self,link,text,this=""):
        self.link = BASEPATH+link
        self.text = text
        if this == link:
            self.this = 1
        else:
            self.this = 0
        
def getMenu(user,this):
    # Only show menu if logged in user
    # Should have some fancy icons and shit
    menu = []
    menu.append(MenuItem("active","Active messages",this))
    if nav.auth.hasPrivilege(user,'web_access','/emotd/edit'):
        menu.append(MenuItem("planned","Planned messages",this))
        menu.append(MenuItem("historic","Historic messages",this))

    menu.append(MenuItem("maintenance","Maintenance list"))
    if nav.auth.hasPrivilege(user,'web_access','/emotd/edit'):
        menu.append(MenuItem("edit","New message",this))
        menu.append(MenuItem("add","Maintenance Setup",this))
    return menu

def search(req):
    ''' Free-text search in MOTD-db '''
    title = 'MOTD freetext search'
    EmotdTemplate.path =  [("Home", "/"), ("Messages", "/emotd"),("Search","")]
    menu = getMenu(req)
    body = None
    motd = None
    searchBox = None
    nameSpace = {'title': title,'motd': motd,'menu': menu, 'searchBox': searchBox,'body': body , 'form': ''}
    page = EmotdStandardTemplate(searchList=[nameSpace])
    return page.respond()


class Message:
    def __init__(self, user, emotdid, type, publish_start, publish_end, last_changed, author, title, description, detail, affected, downtime, replaces_emotd, replaces_title, maint_start, maint_end, state, equipment):
        self.emotdid = emotdid
        if last_changed and not isinstance(last_changed, str):
            last_changed = strftime("%Y-%m-%d %H:%M",last_changed.tuple())
        if publish_start and not isinstance(publish_start, str):
            publish_start = strftime("%Y-%m-%d %H:%M",publish_start.tuple())
        if publish_end and not isinstance(publish_end, str):
            publish_end = strftime("%Y-%m-%d %H:%M",publish_end.tuple())
        if maint_start and not isinstance(maint_start, str):
            maint_start = strftime("%Y-%m-%d %H:%M",maint_start.tuple())
        if maint_end and not isinstance(maint_end, str):
            maint_end = strftime("%Y-%m-%d %H:%M",maint_end.tuple())
        self.own = False
        if user == author:
            self.own = True
        if description:
            description = textpara(description)
        if detail:
            detail = textpara(detail)
        self.last_changed = last_changed
        self.publish_start = publish_start
        self.publish_end = publish_end
        self.maint_start = maint_start
        self.maint_end = maint_end
        self.author = author
        self.title = title
        self.description = description
        self.detail = detail
        self.affected = affected
        self.downtime = downtime
##         self.title_en = title_en
##         self.description_en = description_en
##         self.detail_en = detail_en
##         self.affected_en = affected_en
##         self.downtime_en = downtime_en
        self.replaces_emotd = replaces_emotd
        self.replaces_title = replaces_title
        self.equipment = equipment
        self.type = type
                 

def viewold(req, view = None, lang = None):

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

def view(req, view = None, offset="0", lang = None):
    access = False
    user = req.session['user']
    list = 0
    category = "active"
    if nav.auth.hasPrivilege(user,'web_access','/emotd/edit'):
        access = True

    try:
        emotdid = int(view)
        where = "emotd.emotdid=%d" % emotdid
        
        
    except:
        list = 1
        category = view
        if access and view == "all":
            where = ""
        elif access and view == "planned":
            where = "emotd.publish_start > now()"
        elif access and view == "historic":
            where = "emotd.publish_end < now()"
        else:
            where = "emotd.publish_end > now() and emotd.publish_start < now()"
            view = "active"
        
    if not access:
        if len(where):
            # må koordineres med view == "all" lenger opp
            where += " and type != 'internal'"
            
    where = "where " + where


##    if lang:
##      sql = "select emotdid, type, publish_start, publish_end, last_changed, author, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd, maint_start, maint_end, state from emotd left outer join maintenance using (emotdid) %s order by last_changed desc" % where
##    else:
    ##    select emotdid, type, publish_start, publish_end, last_changed, author, title, description, detail, affected, downtime, replaces_emotd, maint_start, maint_end, state from emotd left outer join maintenance using (emotdid) %s order by last_changed desc" % where
        
    sql = "select emotdid, key, value from emotd left outer join emotd_related using (emotdid) %s order by publish_end desc" % where
    database.execute(sql)
    equipment = {}
    for (emotdid, key, value) in database.fetchall():
        if not equipment.has_key(emotdid):
            equipment[emotdid] = {}
        if not equipment[emotdid].has_key(key):
            equipment[emotdid][key] = []
        equipment[emotdid][key].append(value)

    
    sql = "select emotd.emotdid, emotd.type, emotd.publish_start, emotd.publish_end, emotd.last_changed, emotd.author, emotd.title, emotd.description, emotd.detail, emotd.affected, emotd.downtime, emotd.replaces_emotd,e2.title, maint_start, maint_end, state from emotd left outer join maintenance using (emotdid) left outer join emotd as e2 on emotd.replaces_emotd=e2.emotdid %s order by publish_end desc, emotd.last_changed desc" % where

    database.execute(sql)

    now = DateTime.now()
    messages = []
    for (emotdid, type, publish_start, publish_end, last_changed, author, title, description, detail, affected, downtime, replaces_emotd, replaces_title, maint_start, maint_end, state) in database.fetchall():
        if not list:
            if publish_end < now:
                category = "historic"
            elif publish_start > now:
                category = "planned"
            
        eq = {}
        if equipment.has_key(emotdid):
            eq = equipment[emotdid]
        messages.append(Message(user, emotdid, type, publish_start, publish_end, last_changed, author, title, description, detail, affected, downtime, replaces_emotd, replaces_title, maint_start, maint_end, state, equipmentformat(eq)))

    page = ViewMessageTemplate()
    
    if list:
        page.title = "%s Messages" % view.capitalize()
        page.path =  [("Home", "/"), ("Messages", "/emotd"),(page.title,"")]
    else:
        page.title = messages[0].title.capitalize()
        page.path =  [("Home", "/"), ("Messages", "/emotd"),(category.capitalize()+" Messages","/emotd/"+category),(page.title,"")]
    
    page.category = category
    page.messages = messages
    page.access = access
    page.username = user.login
    page.all = list
#    page.action = ""
    return page.respond()

## def messageList(view, user, menu = ""):
##     access = False
##     if nav.auth.hasPrivilege(user,'web_access','/emotd/edit'):
##         access = True

    
##     page = EmotdFrontpage()
##     page.statustype = view
##     if access and view == "all":
##         where = ""
##     elif access and view == "scheduled":
##         where = "publish_start > now()"
##     elif access and view == "old":
##         where = "publish_end < now()"
##     else:
##         where = "publish_end > now() and publish_start < now()"
##         page.statustype = "active"
##     page.title = "%s Messages" % page.statustype.capitalize()
            
##     emotds = []
##     if not access:
##         if len(where):
##             # må koordineres med view == "all" lenger opp
##             where += " and type != 'internal'"

##     if len(where):
##         where = "where " + where
        
##     sql = "select emotdid, key, value from emotd left outer join emotd_related using (emotdid) %s order by last_changed desc" % where
##     database.execute(sql)

##     equipment = {}
##     for (emotdid, key, value) in database.fetchall():
##         if not equipment.has_key(emotdid):
##             equipment[emotdid] = {}
##         if not equipment[emotdid].has_key(key):
##             equipment[emotdid][key] = []
##         equipment[emotdid][key].append(value)

##     sql = "select emotdid, last_changed, author, title, description, detail, affected, downtime, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd from emotd %s order by last_changed desc" % where
##     database.execute(sql)
##     eq = {}
##     for emotd in database.fetchall():
##         emotdid = emotd[0]
##         if equipment.has_key(emotdid):
##             eq = equipment[emotdid]
##         emotds.append(Message(emotd,user.login,equipmentformat(eq)))
        
##     page.path =  [("Home", "/"), ("Messages", "/emotd"),(page.title,"")]
##     page.menu = menu

##     page.emotds = emotds
##     return page.respond()
##     #return emotds

class MessageListMessage:
    def __init__(self,id,title,description,last_changed,author,type,units):
        self.id = int(id)
        self.title = title
        self.description = description
        self.last_changed = last_changed.strftime(DATEFORMAT)
        self.author = author
        self.type = type
        self.units = units
        self.new = 0
        if last_changed>DateTime.today():
            self.new = 1

def home(req,view="active",offset="0"):

    if not offset:
        offset = 0
    offset = int(offset)
        
    page = EmotdFrontpage()
    user = req.session['user']
    page.title = "%s Messages" % view.capitalize()
    page.menu = getMenu(user,view)
    page.messages = messagelist(user,view,offset)
    page.path = [('Frontpage','/'),
                 ('Messages',BASEPATH),
                 (page.title,'')]
    
    page.nexturi = ""
    if len(page.messages) == 20:
        page.nexturi = "/emotd/"+view+"/"+str(offset+1)

    page.previousuri = ""
    if int(offset) > 0:
        page.previousuri = "/emotd/"+view+"/"+str(offset-1)

    return page.respond()

def messagelist(user,view="active",offset=0):
    access = False
    if nav.auth.hasPrivilege(user,'web_access','/emotd/edit'):
        access = True

    if offset:
        offset = int(offset)
        
    if access and view == "planned":
        time = "publish_start > now()"
    elif access and view == "historic":
        time = "publish_end < now()"
    else:
        time = "publish_end > now() and publish_start < now()"

    if access:
        database.execute("select emotd.emotdid, title, description, last_changed, author, type, count(value) as units from emotd left outer join emotd_related using (emotdid) where %s group by emotd.emotdid, title, description, last_changed, author, type, publish_start, publish_end  order by publish_end desc, last_changed desc limit %s offset %d" %(time,LIMIT,offset*LIMIT))
    else:
        database.execute("select emotd.emotdid, title, description, last_changed, author, type, count(value) as units from emotd left outer join emotd_related using (emotdid) where %s and type != 'internal' group by emotd.emotdid, title, description, last_changed, author, type, publish_start, publish_end order by publish_end desc, last_changed desc limit %s offset %d"% (time, LIMIT, offset*LIMIT))

    messages = []
    for (id, titile, description, last_changed, author, type, units) in database.fetchall():
        messages.append(MessageListMessage(id, titile, description, last_changed, author, type, units))
        
    return messages
    
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
    page.menu = getMenu(req.session['user'],"maintenance")
    page.maints = maintlist
    page.title = 'Maintenance List'
    page.path = [('Frontpage','/'),
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

    page = FeederTemplate()
    database.execute("select emotdid, title, description from emotd where publish_end > now() and publish_start < now() and type != 'internal' order by publish_end desc, last_changed desc") 
    page.messages = database.fetchall()

    page.server = req.server.server_hostname

    return page.respond()


def mainttime(req, id = None):

    page = MaintTimeTemplate()

    req.ny = False
    if id:
        req.emotdid = int(id)

    if req.form.has_key("id"):
        req.emotdid = int(req.form["id"])

    if hasattr(req,"emotdid"):
        (page.start, page.end) = getMaintTime(req.emotdid)
        page.action = BASEPATH + "committime"
        page.emotdid = req.emotdid
        page.ny = req.ny
        return page.respond()


def getMaintTime(emotdid = None):
    maintenance = None
    if emotdid:
        database.execute("select maint_start,maint_end from maintenance where emotdid=%d" % int(emotdid))
        maintenance = database.fetchone()
    if maintenance:
        start = maintenance[0]
        end = maintenance[1]
    else:
        start = DateTime.now()
        end = DateTime.now() + DateTime.RelativeDateTime(days=+7)

    (year,month,day,hour,minute) = start.tuple()[0:5]
    if not maintenance:
        minute = 0
    start = (year,month,day,hour,minute)
    
    (year,month,day,hour,minute) = end.tuple()[0:5]
    if not maintenance:
        minute = 0
    end = (year,month,day,hour,minute)
            
    return (start,end)

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

    args['path'] = [('Home','/'),
                    ('Messages',BASEPATH),
                    ('Maintenance Setup', None)]
    if not req.session.has_key("message"):
        req.session["message"] = {}
    if id:
        req.session["message"]["emotdid"] = int(id)
    elif not req.session["message"].has_key("emotdid"):
        req.session["message"]["emotdid"] = 0
    emotdid = req.session["message"]["emotdid"]

    if isinstance(emotdid, list):
        emotdid = emotdid[0]

    ##searchBox = SearchBox.SearchBox(req,'Type a room id, an ip, a (partial) sysname or servicename')
    selectBox = TreeSelect()
    # search
    # Make the searchbox
    searchbox = SearchBox.SearchBox(req,
                'Type a room id, an ip or a (partial) sysname or servicename')
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
    searchbox.addSearch('service',
                        '(partial) servicename',
                        'Service',
                        {'rooms':['netbox','room','roomid'],
                         'netboxes':['netbox','netboxid'],
                         'locations': ['netbox','room','location','locationid'],
                         'services':['serviceid','handler']},
                        where = "handler ='%s'")

    args['searchbox'] = searchbox

    sr = {"locations":[],"rooms":[],"netboxes":[]}
    if req.form.has_key('sb_submit'):
        sr = searchbox.getResults(req)

#    if emotdid:
#        args['action'] = BASEPATH + 'add/' + str(emotdid)
#    else:
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

    doneaction = BASEPATH + "submit"
    donetext = "Submit"
    
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


##     searchBox.addSearch('host',
##                         'ip or hostname',
##                         'Netbox',
##                         {'rooms': ['room','roomid'],
##                         'locations': ['room','location','locationid'],
##                         'netboxes': ['netboxid']},
##                         call = SearchBox.checkIP)
##     searchBox.addSearch('room',
##                         'room id',
##                         'Room',
##                         {'rooms': ['roomid'],
##                          'locations': ['location','locationid']},
##                          where = "roomid = '%s'")
    
    # Maintenance start<->end
    oneweek = str(DateTime.now() + DateTime.oneWeek)
    oneday = str(DateTime.now() + DateTime.oneDay)
    now = str(DateTime.now())
    
    #if req and req.form.has_key('list'): ##alltid med nå
    body = ""
    args['title'] = title
    nameSpace = {'title': title,'page': 'browse', 'body': body, 'args': args, 'form':form, 'menu': menu}
##     if req.form.has_key('cn_add_netboxes') or req.form.has_key('cn_add_rooms') or req.form.has_key('cn_add_locations'):
##         if hasattr(req,"emotdid") and req.emotdid > 0:#req.form.has_key("id") and int(req.form["id"])>0:
##             #emotdid = req.form["id"]
##             emotdid = req.emotdid
##             kind = None
##             if req.form.has_key("cn_netbox"):
##                 kind = "netbox"

##             elif req.form.has_key("cn_room"):
##                 kind = "room"

##             elif req.form.has_key("cn_location"):
##                 kind = "location"

##             if kind:
##                 for key in req.form.keys():
##                     m = re.search("cn_%s_(\w+)"%kind,key)
##                     if m:
##                         sql = "insert into emotd_related (emotdid,key,value) values (%d, %s, %s)"
##                         database.execute(sql, (emotdid, kind, m.group(1)))
##                 connection.commit()
##             redirect(req,BASEPATH+"add/%s" % emotdid)

##         else:

    ### PARSE INPUT
    if req.form.has_key("cn_done"):
        redirect(req,BASEPATH+"submit")

    elif len(req.form):

        if not req.session.has_key('message'):
            req.session['message'] = {}
        if req.form.has_key("emotdid"):
            if isinstance(req.form["emotdid"],list):
                emotdid = req.form["emotdid"][0]
            else:
                emotdid = req.form["emotdid"]
            req.session['message']['emotdid'] = emotdid
            
        if req.form.has_key("messagetitle"):
            req.session['message']['title'] = req.form["messagetitle"]
        if req.form.has_key("messagedescription"):
            req.session['message']['description'] = req.form["messagedescription"]
        if req.form.has_key("messagetype"):
            req.session['message']['type'] = req.form["messagetype"]

        #raise repr(emotdid)
    
        if req.form.has_key("maintstart_hour"):
            req.session['message']['maint_start'] = DateTime.DateTime(int(req.form["maintstart_year"]),int(req.form["maintstart_month"]),int(req.form["maintstart_day"]),int(req.form["maintstart_hour"]),int(req.form["maintstart_minute"])).strftime(DATEFORMAT)
        if req.form.has_key("maintend_hour"):
            req.session['message']['maint_end'] = DateTime.DateTime(int(req.form["maintend_year"]),int(req.form["maintend_month"]),int(req.form["maintend_day"]),int(req.form["maintend_hour"]),int(req.form["maintend_minute"])).strftime(DATEFORMAT)
        
        if req.form.has_key('cn_add_netboxes') or req.form.has_key('cn_add_rooms') or req.form.has_key('cn_add_locations'):
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
    if req.form.has_key('cn_add_netboxes') or req.form.has_key('cn_add_rooms') or req.form.has_key('cn_add_locations'):
        redirect(req,BASEPATH+"add")
    else:
        page = MaintenanceTemplate(searchList=[nameSpace])
        page.remove = 0
        page.maintstart = ""
        page.maintend = ""
        page.messagetitle = ""
        page.messagelist = ""
        page.messagetitle = ""
        page.messagedescription = ""
        page.messagetype = ""
        page.defined = 0
        page.equipment = {}
        page.newequipment = {}
        page.defined = 0

        emotdid = int(emotdid)
    
        if req.session.has_key('message') and req.session['message'].has_key('defined') and req.session['message']['defined']:
            page.defined = 1

        else:
            page.messagelist = selectmessagelist()
        (page.maintstart,page.maintend) = getMaintTime(emotdid)
        if emotdid:
            page.remove = 1
            page.equipment = equipmentlist(emotdid)
            database.execute("select title, description, type from emotd where emotdid=%d",(int(emotdid),))
            (page.messagetitle,page.messagedescription,messagetype) = database.fetchone()
        else:
            emotdid = 0
            try:
                if req.session.has_key('message'):
                    if req.session['message'].has_key('emotdid') and req.session['message']['emotdid']:
                        emotdid = req.session['message']['emotdid']
                    if req.session['message'].has_key('title') and req.session['message']['title']:
                        page.messagetitle = req.session['message']['title']
                    if req.session['message'].has_key('description') and req.session['message']['description']:    
                        page.messagedescription = req.session['message']['description']
                    if req.session['message'].has_key('type') and req.session['message']['type']:
                        page.messagetype = req.session['message']['type']
            except:
                raise repr(req.session)
        if req.session.has_key('equipment'):
            page.newequipment = equipmentformat(req.session['equipment'])
        page.path = args['path']
        page.emotdid = emotdid
        return page.respond()

def submit(req):
    emotdid = 0
    if req.session.has_key("message"): #do something
        if req.session['message'].has_key("emotdid"):
            try:
                emotdid = int(req.session["message"]["emotdid"])
            except:
                emotdid = 0
        elif req.form.has_key("emotdid"): 
            emotdid = int(req.form["emotdid"])
        if emotdid: #update
            if req.session.has_key("equipment"):
                equipment = req.session["equipment"]
                database.execute("select key,value from emotd_related where emotdid=%d",(emotdid,))
                old = {"location":[], "room":[], "netbox":[], "module":[], "service":[]}
                for (key,value) in database.fetchall():
                    old[key].append(value)

                for key,values in equipment.items():
                    for v in values:
                        if not old[key].count(v):
                #            equipment[key].remove(v)
                #            old[key].remove(v)
                #        else:
                            database.execute("insert into emotd_related (emotdid, key, value) values (%s,%s,%s)",(emotdid, key, v))
                #            equipment[key].remove(v)

                #for keys,values in old.items():
                #    for v in values:
                #        database.execute("delete from emotd_related where emotdid=%s and key=%s and value=%s", (emotdid, key, v))
            messagemaintstart = ""
            messagemaintend = ""
            if req.session['message'].has_key('maint_start') and req.session['message']['maint_start']:
                messagemaintstart = req.session['message']['maint_start']
            if req.session['message'].has_key('maint_end') and req.session['message']['maint_end']:
                messagemaintend = req.session['message']['maint_end']
            if messagemaintstart and messagemaintend:
                database.execute("select emotdid from maintenance where emotdid=%s",(emotdid,))
                maintenance = database.fetchone()
                if maintenance:
                    database.execute("update maintenance set maint_start=%s, maint_end=%s where emotdid=%s",(messagemaintstart,messagemaintend,emotdid))
                else:
                    database.execute("insert into maintenance (emotdid, maint_start, maint_end) values (%s, %s ,%s)", (emotdid, messagemaintstart, messagemaintend))
        else: #new
            messagetitle = ""
            messagedescription = ""
            messagetype = ""
            messagedetail = ""
            messageaffected = ""
            messagedowntime = ""
            messageauthor = req.session['user'].login
            messagelast = DateTime.now().strftime(DATEFORMAT)
            messagepublishstart = ""
            messagepublishend = ""
            messagemaintstart = ""
            messagemaintend = ""
            emotdid = 0
            
            if req.session['message'].has_key('title') and req.session['message']['title']:
                messagetitle = req.session['message']['title']
            if req.session['message'].has_key('description') and req.session['message']['description']:
                messagedescription = req.session['message']['description']
            if req.session['message'].has_key('detail') and req.session['message']['detail']:
                messagedetail = req.session['message']['detail']
            if req.session['message'].has_key('affected') and req.session['message']['affected']:
                messageaffected = req.session['message']['affected']
            if req.session['message'].has_key('downtime') and req.session['message']['downtime']:
                messagedowntime = req.session['message']['downtime']
#            if req.session['message'].has_key('author') and req.session['message']['author']:
#                messageauthor = req.session['message']['author']
#            if req.session['message'].has_key('last_changed') and req.session['message']['last_changed']:
#                messagelast = req.session['message']['last_changed']
            if req.session['message'].has_key('maint_start') and req.session['message']['maint_start']:
                messagemaintstart = req.session['message']['maint_start']
            if req.session['message'].has_key('maint_end') and req.session['message']['maint_end']:
                messagemaintend = req.session['message']['maint_end']
            if req.session['message'].has_key('publish_start') and req.session['message']['publish_start']:
                messagepublishstart = req.session['message']['publish_start']
            elif req.session['message'].has_key("maint_start"):
                messagepublishstart = req.session['message']['maint_start']
            if req.session['message'].has_key('publish_end') and req.session['message']['publish_end']:
                messagepublishend = req.session['message']['publish_end']
            elif req.session['message'].has_key("maint_end"):
                messagepublishend = req.session['message']['maint_end']
            if req.session['message'].has_key('type') and req.session['message']['type']:
                messagetype = req.session['message']['type']
                
            
            ### get next emotdid
            database.execute("select nextval('emotd_emotdid_seq')")
            emotdid = int(database.fetchone()[0])

            if messagetitle and messagedescription:
                database.execute("insert into emotd (emotdid, author, description, detail, title, affected, downtime, type, publish_start, publish_end, last_changed) values (%s, %s, %s, %s, %s, %s, %s, %s, %s ,%s, %s)", (emotdid, messageauthor, messagedescription, messagedetail, messagetitle, messageaffected, messagedowntime, messagetype, messagepublishstart, messagepublishend, messagelast))
                #raise repr("insert into emotd (emotdid, author, description, detail, title, affected, downtime, type, publish_start, publish_end, last_changed) values (%s, %s, %s, %s, %s, %s, %s, %s, %s ,%s, %s)" % (emotdid, messageauthor, messagedescription, messagedetail, messagetitle, messageaffected, messagedowntime, messagetype, messagepublishstart, messagepublishend, messagelast))

                if req.session.has_key("equipment"):
                    equipment = req.session["equipment"]
                    for key,values in equipment.items():
                        for v in values:
                            database.execute("insert into emotd_related (emotdid, key, value) values (%s,%s,%s)",(emotdid, key, v))
                            equipment[key].remove(v)

                if messagemaintstart and messagemaintend:
                    database.execute("insert into maintenance (emotdid, maint_start, maint_end) values (%s, %s ,%s)", (emotdid, messagemaintstart, messagemaintend))


                
        req.session["equipment"] = {}
        req.session["message"] = {}
        connection.commit()
        req.session.save()
    redirect(req,BASEPATH+"view/"+str(emotdid))

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

def cancelmaintenance(req):

    req.session["equipment"] = {}
    req.session["message"] = {}

    req.session.save()
    
    redirect(req,BASEPATH+"add/")


def isdefault(a,b):
    if a==b:
        return 'selected=selected'

def placemessage(req, lang = None):

    page = EmotdMessageTemplate()
    page.title = "Add to message"
    page.path = [("Home", "/"), ("Messages", BASEPATH),("Add to message","")]
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

##     if lang:
##         sql = "select emotdid, title_en, description_en from emotd where publish_end>now() order by publish_end desc"
##     else:
##         sql = "select emotdid, title, description from emotd where  publish_end>now() order by publish_end desc"
##     database.execute(sql)

##     messages = []
##     for (emotdid,title,description) in database.fetchall():
##         messages.append((emotdid, title, description))

    page.emotds = selectmessagelist()
    page.type = type    
    page.equipment_list = eql
    ##page.emotds = (req.session['user'],1)#EmotdSelect.fetchAll()
    return page.respond()

def selectmessagelist():
    database.execute("select emotdid, title, description from emotd where publish_end>now() order by publish_end desc")
    messages = []
    for (emotdid,title,description) in database.fetchall():
        messages.append((emotdid, title, description))
    return messages
    

def edit(req, id = None):
    ''' Edit a given motd_id or new Emotd if motd_id is not given '''
    page = EditTemplate()
    #title = 'Editing as %s ' % (req.session['user'].login)
    page.path =  [("Home", "/"), ("Messages", "/emotd"),("Edit Message","")]
    page.pagetitle = "Edit Message"
    #page.menu = getMenu(req)
    page.parent_id = None
    page.emotdid = None
    
    if id:
        #finnes fra før
        page.emotdid = int(id)
        #sql = "select author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, publish_start, publish_end from emotd where emotdid=%d" % page.emotdid
        sql = "select author, description, detail, title, affected, downtime, type, publish_start, publish_end from emotd where emotdid=%d" % page.emotdid
        database.execute(sql)
        #(page.author, page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en, page.type, page.publish_start, page.publish_end) = database.fetchone()
        (page.author, page.description, page.detail, page.title, page.affected, page.downtime, page.type, page.publish_start, page.publish_end) = database.fetchone()

        change = 0
        if req.session['user'].login == page.author:
            # change
            change = 1
            page.pagetitle = "Edit Message"
        else:
            # followup
            page.author = req.session['user'].login
            if not page.title.startswith('Re:'):
                page.title = 'Re: ' + page.title
#            if page.title_en.startswith('Re:'):
#                page.title_en = 'Re:' + page.title_en
            page.parent_id = page.emotdid
            page.emotdid = None
            page.pagetitle = "Make Followup Message"

    else:
        page.author = req.session['user'].login
        page.publish_start = DateTime.now()
        page.publish_end = DateTime.now() + DateTime.RelativeDateTime(days=+7)
        #(page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en) = [""] * 10
        (page.description, page.detail, page.title, page.affected, page.downtime) = [""] * 5
        page.pagetitle = "Make New Message"

    page.last_changed = str(DateTime.now())
    #for a in (page.description, page.description_en, page.detail, page.detail_en, page.title, page.title_en, page.affected, page.affected_en, page.downtime, page.downtime_en):
    for a in (page.description, page.detail, page.title, page.affected, page.downtime):
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
            sql = "insert into maintenance (emotdid,maint_start,maint_end) values (%d,%s,%s)"
            database.execute(sql, (req.emotdid, str(start), str(end)))
            connection.commit()
            redirect(req,"%sadd/%s" % (BASEPATH,req.emotdid))
        else:
            sql = "update maintenance set maint_start=%s, maint_end=%s where emotdid=%d"
            database.execute(sql, (str(start), str(end), req.emotdid))
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
    #affected_en = req.form['affected']
    downtime = req.form['downtime']
    #downtime_en = req.form['downtime']
    title = req.form['title'] # must have local title
    #title_en = req.form['title_en'] or ""
    author = req.form['author']
    description = req.form['description']
    #description_en = req.form['description_en']
    detail = req.form['detail']
    #detail_en = req.form['detail_en']
    emotdid = 0

    # Save new or existing MOTD
    if req.form.has_key("parent_id") and req.form["parent_id"]:
        replaces = int(req.form["parent_id"])
        #oppdater published end
        database.execute("update emotd set publish_end=%s where emotdid=%d",
           (str(DateTime.now()) ,replaces))
        #lag ny
        database.execute("select nextval('emotd_emotdid_seq')")
        emotdid = int(database.fetchone()[0])
        #database.execute("insert into emotd (emotdid, author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, publish_start, publish_end, replaces_emotd, last_changed) values (%d, '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',%d,'%s')" % (emotdid, author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, start, end, parent_id, last_changed))
        database.execute("insert into emotd (emotdid, author, description, detail, title, affected, downtime, type, publish_start, publish_end, replaces_emotd, last_changed) values (%d, %s,%s,%s,%s,%s,%s,%s,%s,%s,%d,%s)", (emotdid, author, description, detail, title, affected, downtime, type, str(start), str(end), replaces, str(last_changed)))
        database.execute("select key, value from emotd_related where emotdid=%d", (replaces,))
        for (key, value) in database.fetchall():
            database.execute("insert into emotd_related (emotdid, key, value) values (%d,%s,%s)",(emotdid, key, value))
    
    elif req.form.has_key('emotdid') and req.form["emotdid"]:
        emotdid = int(req.form["emotdid"])
        #database.execute("update emotd set description='%s', description_en='%s', detail='%s', detail_en='%s', title='%s', title_en='%s', affected='%s', affected_en='%s', downtime='%s', downtime_en='%s', type='%s', publish_start='%s', publish_end='%s', last_changed='%s' where emotdid=%d" % (description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, start, end, last_changed, emotdid))
        database.execute("update emotd set description=%s, detail=%s, title=%s, affected=%s, downtime=%s, type=%s, publish_start=%s, publish_end=%s, last_changed=%s where emotdid=%d", (description, detail, title, affected, downtime, type, str(start), str(end), str(last_changed), emotdid))
        
    else:
        if req.form.has_key("cn_save"):
            # if no id, make a new MOTD
            database.execute("select nextval('emotd_emotdid_seq')")
            emotdid = int(database.fetchone()[0])
            # database.execute("insert into emotd (emotdid, author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, publish_start, publish_end, last_changed) values (%d, '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % (emotdid, author, description, description_en, detail, detail_en, title, title_en, affected, affected_en, downtime, downtime_en, type, start, end, last_changed))
            database.execute("insert into emotd (emotdid, author, description, detail, title, affected, downtime, type, publish_start, publish_end, last_changed) values (%d, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (emotdid, author, description, detail, title, affected, downtime, type, str(start), str(end), str(last_changed)))
        elif req.form.has_key("cn_save_and_add"):
            if not req.session.has_key("message"):
                req.session["message"] = {}
            req.session['message']['title'] = title
            req.session['message']['description'] = description
            req.session['message']['detail'] = detail
            req.session['message']['affected'] = affected
            req.session['message']['downtime'] = downtime
            req.session['message']['author'] = author
            req.session['message']['last_changed'] = last_changed.strftime(DATEFORMAT)
            req.session['message']['type'] = type
            req.session['message']['publish_start'] = start.strftime(DATEFORMAT)
            req.session['message']['publish_end'] = end.strftime(DATEFORMAT)
            req.session['message']['defined'] = 1

            req.session.save()
            
    connection.commit()
    if req.form.has_key("cn_save"):
        redirect(req,"%sview/%s" % (BASEPATH, emotdid))
    elif req.form.has_key("cn_save_and_add"):
        redirect(req,"%sadd/" % (BASEPATH))
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
                        database.execute("insert into emotd_related (emotdid, key, value) values (%d, %s, %s)", (req.form["id"], type, id))
            req.session["equipment"] = {}
            req.session.save()
            connection.commit()
            redirect(req,BASEPATH+"view/"+req.form["id"])
        else:
            raise "noe skjedde"


def remove(req,emotdid = 0):
    if emotdid:
        emotdid = int(emotdid)
    if req.args:
        params = req.args
        types = params.split("&")
        for t in types:
            (key,vals) = t.split("=")
            for val in vals.split(","):
                if emotdid:
                    database.execute("delete from emotd_related " + 
                        "where emotdid=%d and key=%s and value=%s",
                     (emotdid, key, val))
                elif req.session.has_key("equipment") and req.session["equipment"].has_key(key):
                    while req.session["equipment"][key].count(val):
                        req.session["equipment"][key].remove(val)
        connection.commit()
        req.session.save()
    if emotdid:
        redirect(req,BASEPATH+"add/"+str(emotdid))
    else:
        redirect(req,BASEPATH+"add/")
