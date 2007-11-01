#
# $Id$
#
# Copyright 2003-2005 Norwegian University of Science and Technology
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
# Authors: John Magne Bredal <john.m.bredal@ntnu.no>
#

from mod_python import apache
import re
import nav, nav.path
from nav import web, db
from nav.db import manage
from nav.web.templates.MainTemplate import MainTemplate
from nav.web.templates.ArnoldTemplate import ArnoldTemplate
from nav.web.URI import URI
from urllib import unquote_plus
from IPy import IP
import nav.arnold

import ConfigParser

# Read config from configfile
configfile = nav.path.sysconfdir + "/arnold/arnold.conf"
config = ConfigParser.ConfigParser()
config.read(configfile)

# Connect to the database

dbname = config.get('arnold','database')

global manage, conn
# Connect to manage-database
manage = nav.db.getConnection('default')
# Connect to arnold-database
conn = db.getConnection('arnold', dbname);

    

############################################################
def handler(req):

    # getConnection('subsystem','database')
    cur = conn.cursor()

    arnoldhome = nav.path.bindir

    # Reload to make sure any changes in ArnoldTemplate are included

    #reload(ArnoldTemplate)
    args = URI(req.unparsed_uri)

    page = ArnoldTemplate()


    # Page path is used for quick navigation
    page.path = [("Home","/"), ("Arnold", False)]

    section = ""
    s = re.search("arnold\/(\w+?)(?:\/$|\?|\&|$)",req.uri)
    if s:
        section = s.group(1)
    else:
        section = 'blockedports'

    # Make menu based on user
    setMenu(page)

    username = req.session['user'].login
    page.username = username
    page.name = req.session['user'].name

    if section == 'blocktypes':
        sort = args.get('sort') or 'blocktitle'
        page.head = 'List of current blocktypes'
        printBlocks(cur, page, sort, section)
        page.path = [("Home","/"), ("Arnold", "/arnold"), ("Blocktypes", False)]

    elif section == 'history':
        sort = args.get('sort') or 'ip'
        days = args.get('days') or '7'
        # This is printhistory
        page.head = "History"
        printHistory(cur, page, sort, section, days)
        page.path = [("Home","/"), ("Arnold", "/arnold"), ("History", False)]

    elif section == 'blockedports':
        sort = args.get('sort') or 'ip'
        page.output = args.get('output') or ""
        page.head = "List of blocked ports"
        printBlocked(cur,page,sort, section)
        page.path = [("Home","/"), ("Arnold", "/arnold"), ("Blocked ports", False)]

    elif section == 'search':
        page.head = "Search"
        searchfield = args.get('searchfield')
        searchtext = args.get('searchtext')
        status = args.get('status')
        days = args.get('days')
        printSearch(cur, page, searchfield, searchtext, status, days)
        page.path = [("Home","/"), ("Arnold", "/arnold"), ("Search", False)]

    elif section == 'addreason':
        page.head = "Add blockreason"
        printBlockreasons(cur, page, section)
        page.path = [("Home","/"), ("Arnold", "/arnold"), ("Add blockreason", False)]

    elif section == 'manualblock':
        sort = args.get('sort') or 'ip'
        page.head = "Manual block"
        page.output = args.get('output') or ""
        printManualblock(cur, page, sort, section)
        page.path = [("Home","/"), ("Arnold", "/arnold"), ("Manual block", False)]

    elif section == 'showdetails':
        page.head = "Details"
        id = args.get('id')
        showDetails(cur, page, section, id)
        page.path = [("Home","/"), ("Arnold", "/arnold"), ("Details", False)]

    elif section == 'addBlocktype':
        page.head = ""
        page.path = [("Home","/"), ("Arnold", "/arnold"), ("AddBlocktype", False)]
        id = args.get('blockid')
        if not id:
            id = 0
        printAddblocktype(cur, page, id)

    elif section == 'doenable':
        id = args.get('id')
        try:
            nav.arnold.openPort(id, username)
        except nav.arnold.NoDatabaseInformationError, why:
            redirect (req, 'blockedports?output=Port not found in database. Switch perhaps replaced. Port enabled in database only.')

        redirect(req, 'blockedports')

    elif section == 'domanualblock':
        ip = args.get('ipadresse')

        # Use modulefunction to get info about id
        try:
            info = nav.arnold.findIdInformation(ip, 3)
        except (nav.arnold.UnknownTypeError, nav.arnold.NoDatabaseInformationError), e:
            redirect(req, 'manualblock?output=%s' %e)

        page.arg = args.args
        page.candidates = info


    elif section == 'doblock':
        # Use blockport in arnold-library to block port and update
        # database
        id = {}
        id['mac'] = args.get('mac')
        id['ip'] = args.get('ip')

        try:
            sw = nav.arnold.findSwportinfo(args.get('netboxid'), args.get('ifindex'), args.get('module'), args.get('port'))
        except nav.arnold.PortNotFoundError, why:
            redirect(req, 'blockedports?output=' + str(why))

        # NB: Autoenablestep only set by a blockrun
        try:
            nav.arnold.blockPort(id, sw, args.get('autoenable'), 0, args.get('determined'), args.get('reasonid'), args.get('comment'), req.session['user'].login)
        except Exception, why:
            redirect(req, 'blockedports?output=' + str(why))

        redirect(req, 'blockedports')
                

    elif section == 'doaddblockreason':
        name = args.get('blockreason')
        comment = args.get('comment')
        if name is not '':
            try:
                nav.arnold.addReason(name, comment)
            except nav.arnold.DbError, why:
                pass
        redirect(req, 'addreason')

    elif section == 'doaddblock':
        # blockid, blocktitle, description, reasonid, newreason, mailfile, inputfile, pursuit, eincrease, duration, active, user
        reasonid = args.get('reasonid')
        blockid = args.get('blockid')

        if not blockid:
            newreason = args.get('newreason')
            nr = re.match("--", newreason)
            if not nr:
                cur.execute("SELECT reasonid FROM blocked_reason WHERE name = %s", (newreason,))
                if cur.rowcount < 1:
                    cur.execute("SELECT nextval('public.blocked_reason_blocked_reasonid_seq')")
                    reasonid = cur.fetchone()[0]
                    try:
                        cur.execute("INSERT INTO blocked_reason (blocked_reasonid, name) VALUES (%s, %s)", (reasonid, newreason))
                    except nav.db.driver.ProgrammingError, why:
                        conn.rollback()
                else:
                    reasonid = cur.fetchone()[0]


        blocktitle = args.get('blocktitle')
        blockdesc = args.get('description')
        mailfile = args.get('mailfile')
        inputfile = args.get('inputfile')
        determined = args.get('pursuit')
        incremental = args.get('eincrease')
        if incremental == 'on':
            incremental = 'y'
        else:
            incremental = 'n'
        blocktime = args.get('duration')
        active = args.get('active')
        if active == 'on':
            active = 'y'
        else:
            active = 'n'
        if req.session.has_key('user') and req.session['user'].id > 0:
            lasteditedby = req.session['user'].name

        if blockid:
            q = """
            UPDATE block SET blocktitle=%s, blockdesc=%s,
            reasonid=%s, mailfile=%s, inputfile=%s,
            determined=%s, incremental=%s, blocktime=%s,
            active=%s, lastedited=now(), lastedituser=%s
            WHERE blockid=%s
            """
            try:
                cur.execute(q, (blocktitle, blockdesc, reasonid, mailfile, inputfile, determined, incremental, blocktime, active, lasteditedby, blockid))
            except nav.db.driver.ProgrammingError, why:
                conn.rollback()
        else:
            q = """
            INSERT INTO block (blocktitle, blockdesc, mailfile,
            reasonid, determined, incremental, blocktime, active,
            lastedited, lastedituser, inputfile)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now(), %s, %s)
            """
            try:
                cur.execute(q, (blocktitle, blockdesc, mailfile, reasonid, determined, incremental, blocktime, active, lasteditedby, inputfile))
            except nav.db.driver.ProgrammingError, why:
                conn.rollback()


        if blockid:
            redirect(req,'addBlocktype?blockid=%s' %blockid)
        else:
            redirect(req,'blocktypes')
        
                
    else:
        page.head = section
        page.headersList = ['a']
        page.headers = {'a':'b'}



    page.action = section


    # Set some page-variables
    req.content_type = "text/html"
    req.send_http_header()
    page.title = "Arnold"

    req.write(page.respond())

    return apache.OK


############################################################
def setMenu(page):
    buttonnames = ['History',"Blocked ports","Search","Add blockreason","Manual block","Blocktypes"]
    buttons = {'History':'history' ,"Blocked ports":'blockedports', "Search":'search', "Add blockreason":'addreason', "Manual block":'manualblock', "Blocktypes":'blocktypes'}
    
    page.buttonnames = buttonnames
    page.buttons = buttons


############################################################
def printHistory(cur, page, sort, section, days):
    """
    Get history information based on input.
    """

    reconnect()

    page.headersList = ['ip','dns','mac','netbios','orgid','status','reason','lastchanged','details']
    page.headers = { 'ip': 'Ip', 'dns':'Dns', 'mac':'Mac','netbios':'Netbios', 'orgid':'Orgid', 'status':'Status' ,'reason':'Reason', 'lastchanged':'Lastchanged', 'details':'&nbsp;', '':''}

    if days < '0':
        days = '0'
        
    page.days = days
    page.headertext = "History"
    page.hitstext = "hits in history based on activity the last " + days + " days"
    page.sort = 1

    try:
        query = """
        SELECT DISTINCT identityid, ip, mac, dns, netbios, orgid,
        name AS reason, starttime,  blocked_status AS status,
        to_char(lastchanged,'YYYY-MM-DD HH24:MI:SS') as lastchanged, swportid
        FROM identity LEFT JOIN blocked_reason USING (blocked_reasonid)
        WHERE lastchanged > current_date - interval '%s'  ORDER BY %s
        """ %(days, sort)
        cur.execute(query)
        list = cur.dictfetchall()
    except nav.db.driver.ProgrammingError, e:
        list = {}

    for item in list:
        item['details'] = "<a href='showdetails?id=" + str(item['identityid']) +"'>Details</a>"

    page.hits = len(list)
    page.list = list
    page.section = section


############################################################
def printBlocked(cur, page, sort, section):

    #reconnect()

    page.headersList = ['ip','dns','netbios','orgid','reason','sysname','lastchanged','activate','details']
    page.headers = { 'ip': 'Ip', 'dns':'Dns', 'netbios':'Netbios', 'orgid':'Orgid','reason':'Reason', 'sysname':'Switch', 'lastchanged':'Lastchanged', 'activate':'&nbsp;', 'details':'&nbsp;'}

    query = """SELECT DISTINCT identityid, orgid, ip, mac, dns, netbios, name AS reason,
    starttime, lastchanged, swportid
    FROM identity
    LEFT JOIN blocked_reason USING (blocked_reasonid)
    WHERE blocked_status='disabled' ORDER BY """ + sort

    cur.execute(query)

    page.hits = cur.rowcount
    page.headertext = "List of ports currently blocked"
    page.hitstext = "ports blocked"
    
    list = cur.dictfetchall()
    
    managec = manage.cursor()

    for item in list:
        item['lastchanged'] = item['lastchanged'].strftime('%Y-%m-%d %k:%M:%S')
        item['activate'] = "<a href='arnold/doenable?id=" + str(item['identityid']) + "'>Activate port</a>"
        item['details'] = "<a href='showdetails?id=" + str(item['identityid']) +"'>Details</a>"
        
        managequery = """SELECT sysname, module, port FROM netbox LEFT
        JOIN module USING (netboxid) LEFT JOIN swport USING (moduleid)
        WHERE swportid = %s"""

        managec.execute(managequery, (item['swportid'], ))
        managelist = managec.dictfetchone()
        
        item['sysname'] = managelist['sysname']
            

    page.sort = 1
    page.list = list
    page.section = section


############################################################
def printSearch(cur, page, searchfield, searchtext, status, days):

    reconnect()
    
    searchfields = ['IP','MAC','Netbios','dns','Orgid']
    page.statusfields = ['disabled','enabled','both']
    page.searchfields = searchfields
    page.searchfield = searchfield
    page.searchtext = searchtext

    try:
        days = abs(int(days)) or 7
    except (ValueError, TypeError), e:
        days = 7
        
    page.days = days
    page.status = status or 'both'

    if searchtext:
        
        page.headersList = ['ip','dns','mac','netbios','orgid','status','reason','lastchanged','history']
        page.headers = { 'ip': 'Ip', 'dns':'Dns', 'mac':'Mac', 'netbios':'Netbios', 'orgid':'Organization', 'status':'Status' ,'reason':'Reason', 'lastchanged':'Lastchanged', 'history':'&nbsp;'}

        whereclause = ''

        # Check searchfield
        if searchfield.lower() == 'ip':
            whereclause = " WHERE " + searchfield.lower() + " <<= inet %s "
        else:
            whereclause = " WHERE " + searchfield.lower() + " LIKE %s "
            searchtext = "%" + searchtext + "%"

        # Status - radiobuttons
        if status == 'disabled':
            whereclause += " AND blocked_status = 'disabled' "
        elif status == 'enabled':
            whereclause += " AND blocked_status = 'enabled' "
        else:
            pass
        

        q = """SELECT DISTINCT identityid, ip, mac, dns, netbios, orgid, name AS reason,
        starttime, blocked_status AS status, to_char(lastchanged,'YYYY-MM-DD HH24:MI:SS') AS lastchanged
        FROM identity LEFT JOIN blocked_reason USING (blocked_reasonid)""" + whereclause + """
        AND lastchanged > current_date - interval '""" + str(days) + """ days'""" 
        
        try:
            cur.execute(q, (searchtext,))
            searchresults = cur.dictfetchall()
            numresults = cur.rowcount
            
            if numresults == 0:
                page.headertext = "Search for " + searchfield + " = \"" + searchtext + "\", status = " + page.status + ", last changed " + str(page.days) + " days ago, did not return anything."
                page.searchresults = {}
            else:
                for element in searchresults:
                    element['history'] = "<a href='showdetails?id=" + str(element['identityid']) + "'>History</a>"

                page.headertext = "Searchresults when searching for " + searchfield + " with value '" + searchtext + "'"
                page.searchresults = searchresults
                page.hits = cur.rowcount
                page.hitstext = "result(s) found"
                
        except nav.db.driver.ProgrammingError:
            page.searchresults = {}
            page.headertext = "<!-- " + q + "-->\nDBError. Search for " + searchfield + " = \"" + searchtext + "\", status = " + page.status + ", last changed " + str(page.days) + " days ago, did not return anything."

    else:
        page.searchresults = {}

    page.sort = 0
        

############################################################
def printBlocks(cur, page, sort, section):

    reconnect()
    
    page.headersList = ['blockid', 'blocktitle', 'blockdesc', 'active', 'edit']
    page.headers = {'blockid': 'ID', 'blocktitle': 'Title', 'blockdesc': 'Description', 'active': 'Active', 'edit':'&nbsp;'}

    cur.execute("SELECT * FROM block ORDER BY " + sort)
    list = cur.dictfetchall()

    for element in list:
        element['edit'] = "<a href='addBlocktype?blockid=%s'>Edit</a>" %element['blockid']
        if element['active'] == 'y':
            element['active'] = 'Yes'
        else:
            element['active'] = 'No'

    page.hits = cur.rowcount
    page.headertext = "List of current blocktypes"
    page.hitstext = "blocktypes registered"
    page.sort = 1
    page.list = list
    page.section = section


############################################################
def showDetails (cur, page, section, id):

    reconnect()
    
    page.headersList = ['ip', 'dns', 'netbios', 'mac', 'sysname', 'modport', 'status', 'autoenable', 'mail']
    page.headers = {'ip':'Ip', 'dns':'Dns', 'netbios':'Netbios', 'mac':'Mac', 'sysname':'Switch', 'modport':'Port', 'status':'Status', 'autoenable':'Autoenable', 'mail':'Mail'}


    # Connect to manage-database to fetch switchport-information
    managec = manage.cursor()
    

    
    cur.execute("SELECT ip,dns,netbios,mac,swportid,lastchanged,starttime,mail,blocked_status as status,autoenable FROM identity WHERE identityid = " + id)
    list = cur.dictfetchall()

    managec.execute('SELECT * FROM netbox LEFT JOIN module USING (netboxid) LEFT JOIN swport USING (moduleid) WHERE swportid=%s', (list[0]['swportid'], ))
    managerow = managec.dictfetchone()

    for entry in list:
        if managec.rowcount <= 0:
            page.output = "Error: Could not find swport in database. Perhaps switch has been replaced?"
            entry['sysname'] = "N/A"
            entry['modport'] = "N/A"
        else:
            page.output = ""
            entry['modport'] = str(managerow['module']) + ":" + str(managerow['port'])
            entry['sysname'] = managerow['sysname']
        
        entry['starttime'] = entry['starttime'].strftime('%Y-%m-%d %k:%M:%S')
        entry['lastchanged'] = entry['lastchanged'].strftime('%Y-%m-%d %k:%M:%S')

        if entry['autoenable']:
            entry['autoenable'] = entry['autoenable'].strftime('%Y-%m-%d %k:%M:%S')
        else:
            entry['autoenable'] = '&nbsp;'

    page.list = list
    page.section = section
    page.sort = 0
    page.headertext = "Details for " + list[0]['ip']

    q = """
    SELECT eventtime, event_comment AS comment,
    blocked_status AS action, name, username
    FROM event
    LEFT JOIN blocked_reason USING (blocked_reasonid)
    WHERE identityid=%s ORDER BY eventtime
    """
    cur.execute(q, (id,))

    page.headersList2 = ['eventtime','action','name','comment','username']
    page.headers2 = {'eventtime':'Eventtime', 'action':'Action', 'name':'Reason', 'comment':'Comment', 'username':'User'}
    list2 = cur.dictfetchall()

    for entry in list2:
        entry['name'] = entry['name'] or "&nbsp;"
        entry['comment'] = entry['comment'] or "&nbsp;"
            
    page.hits2 = cur.rowcount
    page.hitstext2 = "entries in history"
    page.headertext2 = "History"
    page.list2 = list2
        

############################################################
def printBlockreasons(cur, page,section):

    reconnect()

    page.blockreasonheadersList = ['name', 'comment']
    page.blockreasonheaders = {'name':'Reason', 'comment': 'Comment'}

    cur.execute("SELECT blocked_reasonid AS id, name, comment FROM blocked_reason");
    page.blockreasons = cur.dictfetchall()
    page.hits = cur.rowcount
    page.sort = 0
    page.hitstext = "reasons in the database"
    page.headertext = "Existing reasons for blocking"



############################################################
def printManualblock(cur,page,sort,section):

    reconnect()

    cur.execute("SELECT blocked_reasonid AS id, name FROM blocked_reason ORDER BY name");
    page.reasons = cur.dictfetchall()



############################################################
def printAddblocktype (cur, page, id):

    reconnect()

    cur.execute("SELECT blocked_reasonid AS id, name FROM blocked_reason ORDER BY name");
    page.blockreasons = cur.dictfetchall()

    blockinfo = {'blockid':'', 'blocktitle':'', 'blockdesc':'', 'mailfile':'', 'reasonid':0, 'determined':'n', 'incremental':'n', 'blocktime':'', 'userid':'cron', 'active':'n', 'inputfile':''}

    if id:
        cur.execute("SELECT * FROM block WHERE blockid=%s" %id)
        blockinfo = cur.dictfetchone()
        blockinfo['lastedited'] = blockinfo['lastedited'].strftime('%Y-%m-%d %k:%M:%S')

    page.blockinfo = blockinfo


############################################################
# A helpful function for redirecting a web-page to another one.
def redirect(req, url):
    req.headers_out.add("Location", url)
    raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY


############################################################
# Connect to both databases
def reconnect():
    global manage, conn
    
    # Connect to manage-database
    manage = nav.db.getConnection('default')
    # Connect to arnold-database
    conn = db.getConnection('arnold', dbname);
 
