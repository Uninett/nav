#################################################
## blapp.py

#################################################
## Imports
#from miscUtils import getattrlist,makewherelist
from mod_python import util, apache
from mx import DateTime
import sys,os,re,copy,string
import nav
#from tables import *
#import forgetHTML as html
#import forgetSQL
import nav.db.manage 
from nav.db.manage import Emotd, Emotd_related, Maintenance, Room, Service, Netbox 
from nav.web import EmotdSelect
from nav.web.TreeSelect import TreeSelect, Select, UpdateableSelect
from nav.web import SearchBox

#cursor = database.cursor()

#################################################
## Templates

from nav.web.templates.EmotdTemplate import EmotdTemplate
from nav.web.templates.EmotdFrontpage import EmotdFrontpage
from nav.web.templates.MaintenanceTemplate import MaintenanceTemplate

#################################################
## Module constants

title = 'Massage of the day'
menu = ''

EmotdTemplate.path =  [("Frontpage", "/"), ("eMotd", "/emotd")]

#################################################
# Elements 
 
def handler(req):
    path = req.uri
    filename = re.search('/([^/]+)$',path).group(1)
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)
    if filename == 'index':
        output = show_active(req)
    elif filename == 'edit':
        output = edit(req)
    elif filename == 'search':
        output = search(req)
    elif filename == 'view':
        output = view(req)
    elif filename == 'viewall':
        output = viewall(req)
    elif filename == 'show_active':
        output = show_active(req)
    elif filename == 'commit':
        output = commit(req)
    elif filename == 'rssfeed':
        output = feed(req)
    elif filename == 'maintenance':
        output = maintenance(req)
    else:
        output = show_active(req)
    if output:
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND


def getMenu(req):
    # Only show menu if logged in user
    # Should have some fancy icons and shit
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        menu = '''
        <b>Administration mode</b> <br><br>
        <a href="edit">Compose</a><br>
        <a href="show_active">Show active MOTDs</a><br>
        <a href="viewall">View all previos MOTDs</a><br>
        <a href="maintenance?list=active">Current maintenance</a><br>
        '''
    else:
        # do we have a menu for anonymous users? Maybe search, view, show_last_n etc
        menu = '''
                 <a href="show_active">Show active MOTDs</a><br>
                 <a href="viewall">View all previos MOTDs</a><br>  
                 <a href="maintenance?list=active">Current maintenance</a><br>
                '''
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
    page = EmotdTemplate(searchList=[nameSpace])
    return page.respond()


def show_active(req):
    ''' Show all active MOTD (as in not outdated )'''
    title = 'Current active messages'
    EmotdFrontpage.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Current active messages","")]
    body = ''
    form = ''
    menu = getMenu(req)
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        motd = EmotdSelect.getAllActive(access=True)
        access = True
    else:
        access = False
        motd = EmotdSelect.getAllActive()
    nameSpace = {'title': title, 'emotds': motd, 'menu': menu, 'access': access}
    page = EmotdFrontpage(searchList=[nameSpace])
    if access:
        page.access = True
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
    title = 'All published messages'
    EmotdFrontpage.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Published messages","")]
    menu = getMenu(req)
    if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit'):
        emotds = EmotdSelect.fetchAll(access=True)
    else:
        emotds = EmotdSelect.fetchAll()
    nameSpace = {'title': title, 'emotds': emotds, 'menu': menu }
    page = EmotdFrontpage(searchList=[nameSpace])
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

def maintenance(req):
    ''' Put locations,rooms,netboxes,modules,services on maintenance to prevent 
        alerts being sent while doing maintenance
    '''
    form = ''
    body = ''
    searchBox = None
    selectBox = None
    EmotdTemplate.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Maintenance","")]

    searchBox = SearchBox.SearchBox(req,'Type a room id, an ip,a (partial) sysname or servicename') 
    selectBox = TreeSelect()
    # search
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
    searchBox.addSearch('service',
                        'serviceid or partial sercicename',
                        'Service',
                        {'rooms':['netbox','room','roomid'],
                         'netboxes':['netbox','netboxid'],
                         'locations': ['netbox','room','location','locationid'],
                         'services':['serviceid']},
                        where = "handler ='%s'")

    sr = searchBox.getResults(req)
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
                               multiple = True,
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
                               preSelected = sr['services'])
    # onchange=''
    selectBox.addSelect(select) # Location
    selectBox.addSelect(select2)# Room
    selectBox.addSelect(select3)# Netbox
    selectBox.addSelect(select4)# Module or Service

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
    
    if req and req.form.has_key('list'): 
        body = '<p>Current maintenance:</p>'
        maintdict = {}
        if req.form['list'] == 'current' or req.form['list'] == 'active':
            maintdict = EmotdSelect.getMaintenance(state='active',access=True)
        if req.form['list'] == 'scheduled':
            maintdict = EmotdSelect.getMaintenance(state='scheduled',access=True)
        body += '<table width=800><tr><td>\n'
        for maint in maintdict.keys():
            body += '<table> \n'
            body += '<tr><td>Maintenanceid: %s </td>\n' % maint
            mstart = maintdict[maint][0]['maint_start']
            mend   = maintdict[maint][0]['maint_end']
            body += '<td>Started: %s</td><td>Ends at: %s </td></tr>\n' % (mstart,mend)
            body += '<tr><td>Room</td><td>Netbox</td><td>Service/module</td></tr>'
            for f in range(len(maintdict[maint])):
                # One maintenance, can keep severel rooms,netbox,services
                entry = maintdict[maint][f]
                if entry['key'] == 'room':
                    room = Room(entry['value']).roomid + "," + Room(entry['value']).descr
                    body += '<tr><td><b>%s</b></td><td>&nbsp;</td><td>&nbsp;</td></tr>' % (room)
                if entry['key'] == 'netbox':
                    room = Netbox(entry['value']).room.roomid + "," + Netbox(entry['value']).room.descr 
                    netbox = Netbox(entry['value']).sysname 
                    body += '<tr><td>%s</td><td><b>%s</b><td>&nbsp;</td></tr>' % (room,netbox)
                if entry['key'] == 'service':
                    netbox = Service(entry['value']).netbox.sysname
                    room = Service(entry['value']).netbox.room.roomid + "," + Service(61).netbox.room.descr
                    service = Service(entry['value']).handler
                    body += '<tr><td>%s</td><td>%s</td><td><b>&s</b></td></tr>\n' % (room,netbox,service)
            body += '</table><hr>\n'
            # end view of maintenance with this id
        body += '</td></tr></table>\n'
        # For listing ongoing or scheduled maintenances, we don't show searchBox and selectBox.. present a link maybe?
        searchBox = None
        selectBox = None     
    elif req and not req.form.has_key('submitbutton') and not req.form.has_key('list'):
        # Run update every time the form is submitted,
        # unless the submit button has been pressed
        selectBox.update(req.form)
    elif req and req.form.has_key('submitbutton') and req.form.has_key('id'):
        searchBox = None
        selectBox = None
        form = ''
        #raise repr(req.form.list)
        if req.form.has_key('cn_netbox'):
            services = {}
            boxes = {}
            boxes['cn_netbox'] = []
            if type(req.form['cn_netbox']).__name__ == 'str':
                boxes['cn_netbox'].append(req.form['cn_netbox'])
            else:
                boxes['cn_netbox'] = [] # empty list to put multiple boxes into
                for netbox in req.form['cn_netbox']:
                    boxes['cn_netbox'].append(netbox)
            body += '<p>Netboxes set on maintenance:<br>\n'
            maint = Maintenance()
            maint.emotd = int(req.form['id'])
            if req.form.has_key('maint_year_start'):
                year_start = int(req.form['maint_year_start'])
                month_start = int(req.form['maint_month_start'])
                day_start = int(req.form['maint_day_start'])
                hour_start = int(req.form['maint_hour_start'])
                year_end = int(req.form['maint_year_end'])
                month_end = int(req.form['maint_month_end'])
                day_end = int(req.form['maint_day_end'])
                hour_end = int(req.form['maint_hour_end'])
                maint_start=DateTime.Date(year_start,month_start,day_start,hour_start)
                maint_stop=DateTime.Date(year_end,month_end,day_end,hour_end)
                maint.maint_start = maint_start
                maint.maint_end = maint_stop
                maint.state = "scheduled"
                maint.save()
            for blapp in boxes['cn_netbox']:
                body += '<li> %s ' % Netbox(blapp).sysname 
                try:
                    related = Emotd_related()
                    related.emotd = req.form['id']
                    related.key = 'netbox'
                    related.value = blapp
                except:
                    body += '<p><font color=red>An error occured!</font>'
        else:
            body = '<font color=red><p>No netbox or service/module chosen</font>'
    #else:
        #selectBox.update(req.form)
    #    form = '<font color=red><p>No id given. Cannot set maintenance without Emotd!</font>'

    nameSpace = {'title': title, 'motd': None, 'menu': menu, 'form':form,'body': body, 'searchBox': searchBox, 'selectBox': selectBox}
    page = EmotdTemplate(searchList=[nameSpace])
    return page.respond()

def view(req):
    ''' Show a given MOTD based on the motd_id '''
    title = 'View MOTD'
    EmotdFrontpage.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("View","")]
    body = ''
    access = False
    form = ''
    motd = []
    if not req.form.has_key('id'):
        body = 'You must supply a valid MOTD id!'
    else:
        emotdid = req.form['id']
        try:
            emotdid = int(emotdid)
            emotd = EmotdSelect.get(int(req.form['id']))
            #body += emotd['type']
            if emotd['type'] != 'internal': 
                motd.append(emotd)
            else:
                if nav.auth.hasPrivilege(req.session['user'],'web_access','/emotd/edit') :
                    motd.append(emotd)
                    access = True
                else:
                    access = False
                    body += '<p>Access to current message is currently for NAV users only</p>'
        except ValueError,e:
            body += '<font color=red>Invalid literal for MOTD-identification</font>'
    menu = getMenu(req)
    nameSpace = {'title': title, 'emotds': motd, 'searchBox': None, 'menu': menu, 'body': body, 'form': form}
    page = EmotdFrontpage(searchList=[nameSpace])
    if access == True:
        page.access = True
    return page.respond()
    
def isdefault(a,b):
    if a==b:
        return 'selected=selected'

def edit(req):
    ''' Edit a given motd_id or new Emotd if motd_id is not given '''
    title = 'Editing as %s ' % (req.session['user'].login)
    EmotdTemplate.path =  [("Frontpage", "/"), ("eMotd", "/emotd"),("Edit","")]
    id = "None"
    body = ''
    menu = getMenu(req)
    now = DateTime.now()
    week = now + DateTime.oneWeek
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
                    title = 'Re:' + title_en
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
    body += '<form action=commit method=post>\n'
    body += '<table border=0>\n'
    body += '<input type=hidden name=author value=%s>\n' % author
    body += '<input type=hidden name=date_change value=%s>\n' % now
    body += '<tr><td colspan=2 bgcolor=lightgrey>Put on maintenance: '
    body += '<i>Set netbox/service/module on maintenance? </i><input type="checkbox" name=maintenance></td></tr>'
    now = str(DateTime.now())
    body += '<tr><td>Active from : <i>Defaults to 1 week</i></td><td>' 
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
    body += '</td></tr>'
    body += '<td>Active to:</td><td>'
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
    body += '</td></tr>\n'
    # type-values should be fetched from a table... leave that for later... 
    body += '<tr><td colspan=2 bgcolor=lightgrey>MOTD type: <font color="red">*</font> <select name=type>\n'
    body += '<option value=info>Informational</option>\n'
    body += '<option value=error>Error</option>\n'
    body += '<option value=internal>Internal </option>\n'
    body += '<option value=scheduled>Scheduled outage</option>\n'
    body += '</select> <i>Internal will not be publically available - e.g. for NAV users only. </i></td></tr>\n'
    body += '<tr>'
    body += '<td>Title: <font color="red">*</font><input type=text name=title size=20 maxlength=100 value=%s><i>(Norwegian)</i></td>' % title
    body += '<td><input type=text name=title_en size=20 maxlength=100 value=%s><i>(English)</i></td>' % title_en
    body += '</tr>'
    body += '<tr><td align=right>Estimated downtime: <i>(freetext)</i> <input type=text name=downtime size=20 maxlength=100> <i>(Norwegian)</i></td>'
    body += '<td><input type=text name=downtime_en size=20 maxlength=100> <i>(English)</i></td></tr>'
    body += '<tr><td align=right>Affected end users: <i>(freetext)</i> <input type=text name=affected size=20 maxlength=100> <i>(Norwegian)</i></td>'
    body += '<td><input type=text name=affected_en size=20 maxlength=100> <i>(English)</i></td></tr>'
    body += '<tr>'
    body += '<td>Norwegian Description: <font color="red">*</font> </td>\n'
    body += '<td>English Description:</td>\n'
    body += '</tr>'
    body += '<tr>'
    body += '<td><textarea wrap="hard" name="description" rows=8 cols=50>%s</textarea></td>\n' % description
    body += '<td><textarea wrap="hard" name="description_en" rows=8 cols=50>%s</textarea></td>\n' % description_en
    body += '</tr>'
    body += '<tr>'
    body += '<td>Details in Norwegian:</td>\n'
    body += '<td>Details in English:</td>\n'
    body += '</tr>'
    body += '<tr>'
    body += '<td><textarea wrap="hard" name="detail" rows=8 cols=50>%s</textarea></td>\n' % detail
    body += '<td><textarea wrap="hard" name="detail_en" rows=8 cols=50>%s</textarea></td>\n' % detail_en
    body += '</tr>'
    if id != "None":
        body += '<input type=hidden name=emotdid value=%s>' % id
    if req.form.has_key('parent_id'):
        body += '<input type=hidden name=parent_id value=%s>' % req.form['parent_id']
        buttonValue = 'Add'
    else:
        buttonValue = 'Submit'
    body += '<tr><td colspan=2 align=center><input type=submit name=submitbutton value=%s></td></tr>\n' % buttonValue
    body += '</form>\n'
    body += '</table>'

    selectBox = None
    searchBox = None
    motd = None 
    nameSpace = {'title': title, 'motd': motd, 'selectBox': selectBox, 'searchBox': searchBox,'menu': menu, 'body': body}
    page = EmotdTemplate(searchList=[nameSpace])
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
    if req.form['type'] != 'internal':
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
    else:
        m.publish_start = DateTime.now()
        m.publish_end = DateTime.now()
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
    nameSpace = {'title': title, 'motd': None,'searchBox': None, 'menu': menu, 'body': body}
    page = EmotdTemplate(searchList=[nameSpace])
    return page.respond()

