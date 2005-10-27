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

import commands


############################################################
def handler(req):

    # Read config from configfile
    config = readConfig(nav.path.sysconfdir + "/arnold/arnold.cfg")

    # Connect to the database
    # getConnection('subsystem','database')
    conn = db.getConnection('arnold','arnold');
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

    page.username = req.session['user'].login
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
        options = "-x enable -i" + id + " -u " + page.username
        outtext = commands.getoutput(arnoldhome + '/arnold.pl ' + options)
        redirect(req, 'blockedports?output=' + outtext)        

    elif section == 'domanualblock':
        ip = args.get('ipadresse')
        comment = args.get('comment')
        autoenable = args.get('autoenable')
        reasonid = args.get('reason')

        options = "-x disable -a" + ip + " -r" + reasonid + " -u " + page.username
        if autoenable:
            options += " -t" + autoenable
        if comment:
            options += " -c \"" + comment + "\""
            
        
        outtext = commands.getoutput(arnoldhome + '/arnold.pl ' + options)
        redirect(req, 'manualblock?output=' + outtext)

    elif section == 'doaddblockreason':
        text = args.get('blockreason')
        if text is not '':
            cur.execute("SELECT * FROM blocked_reason WHERE text='%s'" %text) 
            if cur.rowcount < 1:
                cur.execute("INSERT INTO blocked_reason (text) VALUES ('" + text + "')")
                conn.commit()
        conn.close()
        redirect(req, 'addreason')

    elif section == 'doaddblock':
        # blockid, blocktitle, description, reasonid, newreason, mailfile, inputfile, pursuit, eincrease, duration, active, user
        reasonid = args.get('reasonid')
        blockid = args.get('blockid')

        if not blockid:
            newreason = args.get('newreason')
            nr = re.search("^--", newreason)
            if not nr:
                cur.execute("SELECT * FROM blocked_reason WHERE text = '%s'" %newreason)
                if cur.rowcount < 1:
                    cur.execute("INSERT INTO blocked_reason (text) VALUES ('" + newreason + "')")
                    conn.commit()
                    cur.execute("SELECT * FROM blocked_reason WHERE text = '%s'" %newreason)
                    templist = cur.dictfetchone()
                    reasonid = templist['blocked_reasonid']


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
        userid = args.get('user')
        if req.session.has_key('user') and req.session['user'].id > 0:
            lasteditedby = req.session['user'].name

        if blockid:
            cur.execute("UPDATE block SET blocktitle='%s', blockdesc='%s', reasonid=%s, mailfile='%s', inputfile='%s', determined='%s', incremental='%s', blocktime=%s, active='%s', userid='%s', lastedited=now(), lastedituser='%s' WHERE blockid=%s" %(blocktitle, blockdesc, reasonid, mailfile, inputfile, determined, incremental, blocktime, active, userid, lasteditedby, blockid))
        else:
            cur.execute("INSERT INTO block (blocktitle, blockdesc, mailfile, reasonid, determined, incremental, blocktime, userid, active, lastedited, lastedituser, inputfile) VALUES ('%s','%s','%s',%s,'%s','%s',%s,'%s','%s',now(),'%s','%s')" %(blocktitle, blockdesc, mailfile, reasonid, determined, incremental, blocktime, userid, active, lasteditedby, inputfile))

        conn.commit()
        conn.close()
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

    conn.close()
    return apache.OK


############################################################
def setMenu(page):
    buttonnames = ['History',"Blocked ports","Search","Add blockreason","Manual block","Blocktypes"]
    buttons = {'History':'history' ,"Blocked ports":'blockedports', "Search":'search', "Add blockreason":'addreason', "Manual block":'manualblock', "Blocktypes":'blocktypes'}
    
    page.buttonnames = buttonnames
    page.buttons = buttons


############################################################
def printHistory(cur, page, sort, section, days):

    page.headersList = ['ip','dns','mac','netbios','orgid','status','reason','lastchanged','details']
    page.headers = { 'ip': 'Ip', 'dns':'Dns', 'mac':'Mac','netbios':'Netbios', 'orgid':'Orgid', 'status':'Status' ,'reason':'Reason', 'lastchanged':'Lastchanged', 'details':'&nbsp;', '':''}

    if days < '0':
        days = '0'
        
    page.days = days
    page.headertext = "History"
    page.hitstext = "hits in history based on activity the last " + days + " days"
    page.sort = 1

    try:
        cur.execute("SELECT DISTINCT identityid, ip, mac, dns, netbios, orgid, text AS reason, multiple, starttime, swsysname AS sysname, swmodule, swport, blocked_status AS status, to_char(lastchanged,'YYYY-MM-DD HH24:MI:SS') as lastchanged FROM identity LEFT JOIN blocked_reason USING (blocked_reasonid) WHERE lastchanged > current_date + integer '-" + days + "'  ORDER BY " + sort)
        list = cur.dictfetchall()
    except psycopg.DatabaseError, e:
        list = {}

    for item in list:
        item['details'] = "<a href='showdetails?id=" + str(item['identityid']) +"'>Details</a>"

    page.hits = cur.rowcount
    page.list = list
    page.section = section


############################################################
def printBlocked(cur, page, sort, section):

    page.headersList = ['ip','dns','netbios','orgid','reason','sysname','lastchanged','activate','details']
    page.headers = { 'ip': 'Ip', 'dns':'Dns', 'netbios':'Netbios', 'orgid':'Orgid','reason':'Reason', 'sysname':'Switch', 'lastchanged':'Lastchanged', 'activate':'&nbsp;', 'details':'&nbsp;'}

    cur.execute("SELECT DISTINCT identityid,orgid,ip,mac,dns,netbios,text as reason, multiple,starttime,lastchanged,swsysname as sysname, swmodule,swport,userlock,secret FROM identity LEFT JOIN blocked_reason USING (blocked_reasonid) WHERE blocked_status='disabled' ORDER BY " + sort)

    page.hits = cur.rowcount
    page.headertext = "List of ports currently blocked"
    page.hitstext = "ports blocked"
    
    list = cur.dictfetchall()

    for item in list:
        item['lastchanged'] = item['lastchanged'].strftime('%Y-%m-%d %k:%M:%S')
        item['activate'] = "<a href='arnold/doenable?id=" + str(item['identityid']) + "'>Activate port</a>"
        item['details'] = "<a href='showdetails?id=" + str(item['identityid']) +"'>Details</a>"

    page.sort = 1
    page.list = list
    page.section = section


############################################################
def printSearch(cur, page, searchfield, searchtext, status, days):
    searchfields = ['IP','MAC','Netbios','dns','Orgid']
    page.statusfields = ['disabled','enabled','both']
    page.searchfields = searchfields
    page.searchfield = searchfield
    page.searchtext = searchtext
    page.days = days or '7'

    if days < '0':
        days = '0'

    page.status = status or 'both'

    if searchtext:
        
        page.headersList = ['ip','dns','mac','netbios','orgid','status','reason','lastchanged','history']
        page.headers = { 'ip': 'Ip', 'dns':'Dns', 'mac':'Mac', 'netbios':'Netbios', 'orgid':'Organization', 'status':'Status' ,'reason':'Reason', 'lastchanged':'Lastchanged', 'history':'&nbsp;'}

        whereclause = ''

        # Check searchfield
        if searchfield.lower() == 'ip':
            whereclause = " WHERE " + searchfield.lower() + " <<= inet '" + searchtext + "' "
        else:
            whereclause = " WHERE " + searchfield.lower() + " LIKE '%" + searchtext + "%' "

        # Status - radiobuttons
        if status == 'disabled':
            whereclause += " AND blocked_status = 'disabled' "
        elif status == 'enabled':
            whereclause += " AND blocked_status = 'enabled' "
        else:
            pass

        # Days
        days = days or 7

        q = "SELECT DISTINCT identityid, ip, mac, dns, netbios, orgid, text AS reason, multiple, starttime, swsysname AS sysname, swmodule, swport, blocked_status AS status, to_char(lastchanged,'YYYY-MM-DD HH24:MI:SS') as lastchanged FROM identity LEFT JOIN blocked_reason USING (blocked_reasonid)" + whereclause + " AND lastchanged > current_date + integer '-" + days + "' "
        try:
            cur.execute(q)
            searchresults = cur.dictfetchall()
            numresults = cur.rowcount
            
            if numresults == 0:
                page.headertext = "Search for " + searchfield + " = \"" + searchtext + "\", status = " + page.status + ", last changed " + page.days + " days ago, did not return anything."
                page.searchresults = {}
            else:
                for element in searchresults:
                    element['history'] = "<a href='showdetails?id=" + str(element['identityid']) + "'>History</a>"

                page.headertext = "Searchresults when searching for " + searchfield + " with value '" + searchtext + "'"
                page.searchresults = searchresults
                page.hits = cur.rowcount
                page.hitstext = "result(s) found"
                
        except psycopg.DatabaseError:
            page.searchresults = {}
            page.headertext = "<!-- " + q + "-->DBError. Search for " + searchfield + " = \"" + searchtext + "\", status = " + page.status + ", last changed " + page.days + " days ago, did not return anything."

    else:
        page.searchresults = {}

    page.sort = 0
        

############################################################
def printBlocks(cur, page, sort, section):
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
    page.headersList = ['ip', 'dns', 'netbios', 'mac', 'sysname', 'modport', 'status', 'starttime', 'lastchanged', 'autoenable', 'mail']
    page.headers = {'ip':'Ip', 'dns':'Dns', 'netbios':'Netbios', 'mac':'Mac', 'sysname':'Switch', 'modport':'Port', 'status':'Status', 'starttime':'Starttime', 'lastchanged':'Lastchanged', 'autoenable':'Autoenable', 'mail':'Mail'}

    cur.execute("SELECT ip,dns,netbios,mac,swsysname as sysname,swmodule,swport,lastchanged,starttime,mail,blocked_status as status,autoenable FROM identity WHERE identityid = " + id)

    list = cur.dictfetchall()

    for element in list:
        element['modport'] = str(element['swmodule']) + ":" + str(element['swport'])
        element['starttime'] = element['starttime'].strftime('%Y-%m-%d %k:%M:%S')
        element['lastchanged'] = element['lastchanged'].strftime('%Y-%m-%d %k:%M:%S')
        if element['autoenable']:
            element['autoenable'] = element['autoenable'].strftime('%Y-%m-%d %k:%M:%S')
        else:
            element['autoenable'] = '&nbsp;'

    page.list = list
    page.section = section
    page.sort = 0
    page.headertext = "Details for " + list[0]['ip']

    cur.execute("SELECT eventtime,event_comment as comment,blocked_status as action,text as reason, username FROM event LEFT JOIN blocked_reason USING (blocked_reasonid) WHERE identityid=" + id + " ORDER BY eventtime")

    page.headersList2 = ['eventtime','action','reason','comment','username']
    page.headers2 = {'eventtime':'Eventtime', 'action':'Action', 'reason':'Reason', 'comment':'Comment', 'username':'User'}
    list2 = cur.dictfetchall()

    for element in list2:
        element['reason'] = element['reason'] or "&nbsp;"
        element['comment'] = element['comment'] or "&nbsp;"

    page.hits2 = cur.rowcount
    page.hitstext2 = "entries in history"
    page.headertext2 = "History"
    page.list2 = list2



############################################################
def printBlockreasons(cur, page,section):

    page.blockreasonheadersList = ['text']
    page.blockreasonheaders = {'text':'Reason'}

    cur.execute("SELECT blocked_reasonid as id, text FROM blocked_reason");
    page.blockreasons = cur.dictfetchall()
    page.hits = cur.rowcount
    page.sort = 0
    page.hitstext = "reasons in the database"
    page.headertext = "Existing reasons for blocking"



############################################################
def printManualblock(cur,page,sort,section):

    cur.execute("SELECT blocked_reasonid AS id, text FROM blocked_reason ORDER BY text");
    page.reasons = cur.dictfetchall()



############################################################
def printAddblocktype (cur, page, id):

    cur.execute("SELECT blocked_reasonid as id, text FROM blocked_reason ORDER BY text");
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


def readConfig(path):

    try:
        file = open (path)
        lines = file.readlines()
        file.close()
    except IOError:
        return
    
    config = {}

    for line in lines:
        if re.search("(^#|^\s+)", line):
            continue
        (var,val) = line.split("=")
        var = var.strip()
        val = val.strip()
        config[var] = val

    return config
