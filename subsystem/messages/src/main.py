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
# $Id: $
# Authors: Bjørn Ove Grøtan <bjorn.grotan@itea.ntnu.no>
#          Sigurd Gartmann <sigurd-nav@brogar.org>
#
"""
The interface part of the Messages subsystem. This is mainly the web front end that will generate HTML pages from templates. An XML-feeder is also part of this module.
"""

## Imports
from mod_python import util, apache
from mx import DateTime
from time import strftime
import re
from nav import db
from nav.web.TreeSelect import TreeSelect, Select, UpdateableSelect
from nav.web import SearchBox,EmotdSelect,redirect,shouldShow
from lib import Message, MessageListMessage, messagelist, equipmentlist, equipmentformat, textpara, MaintListElement, getMaintTime
from menu import Menu

## Configuration
from conf import DATEFORMAT, BASEPATH, LANG1, LANG2, connection, database

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

def handler(req):

    #fieldstorage variables
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)

    #the path decides what will be viewed
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
    elif path[0] == 'maintlist':
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
        #default
        output = home(req,"active")

    if output:
        req.content_type = "text/html" #maybe unneccesarry
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND

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


## is the search needed?
## def search(req):
##     ''' Free-text search in MOTD-db '''
##     title = 'MOTD freetext search'
##     EmotdTemplate.path =  [("Home", "/"), ("Messages", "/emotd"),("Search","")]
##     menu = getMenu(req)
##     body = None
##     motd = None
##     searchBox = None
##     nameSpace = {'title': title,'motd': motd,'menu': menu, 'searchBox': searchBox,'body': body , 'form': ''}
##     page = EmotdStandardTemplate(searchList=[nameSpace])
##     return page.respond()



def view(req, view = None, offset="0", lang = None):
    """ View one or all messages (of the right type)"""
    
    access = False
    user = req.session['user']
    list = 0
    category = "active"
    if shouldShow(BASEPATH+'edit',user):
        access = True

    try:
        #if the last parameter is a number, it is assumed this is the desired emotdid. this and only this message is shown.
        emotdid = int(view)
        where = "emotd.emotdid=%d" % emotdid
        
        
    except:
        #the last parameter was not a number, assuming all messages of a category / type is desired
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

#language crap again
##    if lang:
##      sql = "select emotdid, type, publish_start, publish_end, last_changed, author, title_en, description_en, detail_en, affected_en, downtime_en, replaces_emotd, maint_start, maint_end, state from emotd left outer join maintenance using (emotdid) %s order by last_changed desc" % where
##    else:
    ##    select emotdid, type, publish_start, publish_end, last_changed, author, title, description, detail, affected, downtime, replaces_emotd, maint_start, maint_end, state from emotd left outer join maintenance using (emotdid) %s order by last_changed desc" % where


    # relate units to messages. first get the units.
    sql = "select emotdid, key, value from emotd left outer join emotd_related using (emotdid) %s order by publish_end desc" % where
    database.execute(sql)
    equipment = {}
    for (emotdid, key, value) in database.fetchall():
        if not equipment.has_key(emotdid):
            equipment[emotdid] = {}
        if not equipment[emotdid].has_key(key):
            equipment[emotdid][key] = []
        equipment[emotdid][key].append(value)

    # then get the messages
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
            # and connect these
            eq = equipment[emotdid]
        messages.append(Message(user, emotdid, type, publish_start, publish_end, last_changed, author, title, description, detail, affected, downtime, replaces_emotd, replaces_title, maint_start, maint_end, state, equipmentformat(eq)))

    page = ViewMessageTemplate()
    
    if list:
        page.title = "%s Messages" % view.capitalize()
        page.path =  [("Home", "/"), ("Messages", "/emotd"),(page.title,"")]
    else:
        page.title = messages[0].title.capitalize()
        page.path =  [("Home", "/"), ("Messages", "/emotd"),(category.capitalize()+" Messages",BASEPATH+category),(page.title,"")]
    
    page.category = category
    page.messages = messages
    page.access = access
    page.username = user.login
    page.all = list
#    page.action = ""
    return page.respond()


def home(req,view="active",offset="0"):
    """ The frontpage view of this module. Shows a list of active messages as default."""
    
    if not offset:
        offset = 0
    offset = int(offset)
        
    page = EmotdFrontpage()
    user = req.session['user']
    page.title = "%s Messages" % view.capitalize()
    page.menu = Menu().getMenu(user,view)
    page.messages = messagelist(user,view,offset)
    page.path = [('Home','/'),
                 ('Messages',BASEPATH),
                 (page.title,'')]

    # define links if there are more than 20 of this message category
    page.nexturi = ""
    if len(page.messages) == 20:
        page.nexturi = BASEPATH+view+"/"+str(offset+1)

    page.previousuri = ""
    if int(offset) > 0:
        page.previousuri = BASEPATH+view+"/"+str(offset-1)

    return page.respond()

def maintlist(req):
    page = MaintListTemplate()
    page.path = [('Home','/'), ('Messages',BASEPATH), ("Units on maintenance", None)]
    sql = "select emotd.emotdid, title, key, value, maint_start, maint_end, state from emotd_related left outer join emotd using (emotdid) left outer join maintenance using (emotdid) where type != 'internal' and maint_end > now() order by maint_end desc"
    ## should be either or, not , in the order by clause
    
    database.execute(sql)
    maints = database.fetchall()
    maintlist = []
    for (emotdid, title,  key, value, start, end, state) in maints:
        if key == 'room':
            netboxid = ""
            sysname = ""
            try:
                database.execute("select descr from room where roomid='%s'" % value)
                descr = database.fetchone()[0]

            except:
                descr = value
                
            database.execute("select sysname, netboxid from netbox where roomid='%s'" % value)

            for (sysname, netboxid) in database.fetchall():

                mle = MaintListElement(emotdid,title,start,end, key)
                if netboxid:
                    mle.setNetbox(netboxid,sysname)
                mle.setRoom(value,descr)
                maintlist.append(mle)
                    
        elif key == 'location':
            netboxid = ""
            sysname = ""
            roomid =""
            roomdesc = ""
            try:
                database.execute("select descr from location where locationid='%s'" % value)
                descr = database.fetchone()
            except:
                descr = value

            database.execute("select roomid, descr, netboxid, sysname from room left outer join netbox using (roomid) where locationid='%s'" % value)

            for (roomid, roomdesc, netboxid, sysname) in database.fetchall():
                mle = MaintListElement(emotdid, title, start, end, key)
                if netboxid:
                    mle.setNetbox(netboxid,sysname)
                mle.setRoom(roomid, roomdesc)
                mle.setLocation(value,descr)
 
                maintlist.append(mle)
                
        elif key == 'netbox':
            try:
                database.execute("select sysname from netbox where netboxid=%d" % int(value))
                descr = database.fetchone()[0]
            except:
                descr = key + value
                
            mle = MaintListElement(emotdid, title, start, end, key)
            mle.setNetbox(value,descr)
           
            maintlist.append(mle)

        elif key == 'service':
            netboxid = ""
            sysname = ""
            try:
                database.execute("select handle, netbox.netboxid, sysname from service left outer join netbox using (netboxid) where serviceid=%d" % int(value))
                (descr,netboxid,sysname) = database.fetchone()
            except:
                descr = key + value

            mle = MaintListElement(emotdid), title, start, end, key
            if netboxid:
                mle.setNetbox(netboxid,sysname)
            mle.setService(value,descr)
            maintlist.append(mle)
                
        elif key == 'module':
            netboxid = ""
            sysname = ""
            module =""
            try:
                database.execute("select moduleid, module, descr from module where moduleid=%d" % int(value))
                (moduleid, module, descr, netboxid, sysname) = database.fetchone()
            except:
                descr = key + value
                
            mle = MaintListElement(emotdid, title, start, end, key)
            if netboxid:
                mle.setNetbox(netboxid,sysname)
            mle.setModule(value,module,descr)
            maintlist.append(mle)

    page.menu = Menu().getMenu(req.session['user'], 'maintenance')
    page.maintlist = maintlist
    return page.respond()


def maintenance(req, id = None):
    ''' Put locations,rooms,netboxes,modules,services on maintenance to prevent alerts being sent while doing maintenance. Some message attributes are open for editing too.
    '''
    args = {}
    form = ''
    body = ''
    title = 'Maintenance Setup'
    ##menu = getMenu(req)

    args['path'] = [('Home','/'),
                    ('Messages',BASEPATH),
                    (title, None)]
    if not req.session.has_key("message"):
        req.session["message"] = {}
    if id:
        req.session["message"]["emotdid"] = int(id)
    elif not req.session["message"].has_key("emotdid"):
        req.session["message"]["emotdid"] = 0
    emotdid = req.session["message"]["emotdid"]

    if isinstance(emotdid, list):
        emotdid = emotdid[0]

    #selectbox (treeselect) and searchbox. see the documentation on how these works. Not intuitive.
    
    selectBox = TreeSelect()
    searchbox = SearchBox.SearchBox(req,
                'Type a room id, an ip or a (partial) sysname or servicename', form=False)
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

    args['action'] = BASEPATH + 'add'

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
    # Not allowed to go on, unless at least one unit is selected
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

    args['submit'] = {'control': buttonkey,
                      'value': buttontext,
                      'enabled': validSelect}
    args['done'] = {'control': donename,
                    'value': donetext,
                    'enabled': True}
    args['doneaction'] = doneaction

    args['selectbox'] = selectbox

    
    # Maintenance start<->end
    oneweek = str(DateTime.now() + DateTime.oneWeek)
    oneday = str(DateTime.now() + DateTime.oneDay)
    now = str(DateTime.now())
    
    body = ""
    args['title'] = title
    nameSpace = {'title': title, 'args': args}

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
        # make page. one submit makes this script (maintenance method) both parsing input and redirect to this page for making the resulting page.
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
    """ A lot of parsing and session and data handling. This method is run when the SUBMIT button is pressed. """
    
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

def cancelmaintenance(req):

    req.session["equipment"] = {}
    req.session["message"] = {}

    req.session.save()
    
    redirect(req,BASEPATH+"add/")


def isdefault(a,b):
    if a==b:
        return 'selected=selected'

def placemessage(req, lang = None):
    """(deprecated)"""

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
    """(deprecated)"""
    
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
        raise repr("ERROR: Could not retrieve ID")
        
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
