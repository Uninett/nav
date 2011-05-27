#
# Copyright 2006-2008 (C) Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Arnold mod_python handler module."""

import re
import logging
from mod_python import apache
from mod_python.util import FieldStorage
import nav
import nav.path
import nav.arnold
#from nav import web
from nav import db
#from nav.web.templates.MainTemplate import MainTemplate
from nav.web.templates.ArnoldTemplate import ArnoldTemplate
from nav.web.URI import URI
from nav.web.encoding import encoded_output
from nav.errors import GeneralException
#from urllib import unquote_plus
#from IPy import IP

import psycopg2.extras
import ConfigParser
logger = logging.getLogger('nav.arnoldhandler')

# Read config from configfile
CONFIG_FILE = nav.path.sysconfdir + "/arnold/arnold.conf"
config = ConfigParser.ConfigParser()
config.read(CONFIG_FILE)

# Connect to the database

global manage, conn
# Connect to manage-database
manage = nav.db.getConnection('default')
# Connect to arnold-database
conn = db.getConnection('arnold', 'arnold')
    

############################################################
@encoded_output
def handler(req):
    """ Handrler """
    # getConnection('subsystem','database')
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # arnoldhome = nav.path.bindir

    # Reload to make sure any changes in ArnoldTemplate are included

    #reload(ArnoldTemplate)
    args = URI(req.unparsed_uri)

    page = ArnoldTemplate()
    params = FieldStorage(req) # contains get and post variables

    # Page path is used for quick navigation
    page.path = [("Home","/"), ("Arnold", False)]

    section = ""
    matched_sections = re.search("arnold\/(\w+?)(?:\/$|\?|\&|$)", req.uri)
    if matched_sections:
        section = matched_sections.group(1)
    else:
        section = 'blockedports'

    # Make menu based on user
    set_menu(page)

    username = req.session['user']['login']
    page.username = username
    page.name = req.session['user']['name']

    page.path = [("Home","/"), ("Arnold", "/arnold")]

    page.output = args.get('output') or ""

    if section == 'predefined':
        sort = args.get('sort') or 'blocktitle'
        page.head = 'List of current predefined detentions'
        print_blocks(cur, page, sort, section)
        page.path.append(("Predefined Detentions", False))

    elif section == 'deletepredefined':
        page.head = "Delete predefined detention"
        page.blockid = args.get('blockid') or 0
        print_delete_predefined(cur, page)
        page.path.append(("Delete predefined detention", False))

    elif section == 'dodeletepredefined':
        if params.has_key('predefinedid'):
            sql_query = """DELETE FROM block WHERE blockid=%s"""
            predefinedid = str(params['predefinedid'])
            cur.execute(sql_query, (predefinedid, ))
            
            redirect(req, 'predefined?output=Predefined detention %s deleted.'
                     % params['predefinedtitle'])
        else:
            redirect(req, 'predefined?output=Error: No postvariable')

    elif section == 'history':
        sort = args.get('sort') or 'ip'
        days = args.get('days') or '7'
        # This is printhistory
        page.head = "History"
        print_history(cur, page, sort, section, days)
        page.path.append (("History", False))

    elif section == 'blockedports':
        sort = args.get('sort') or 'ip'
        page.head = "List of detained ports"
        print_blocked(cur, page, sort, section)
        page.path.append(("Detained ports", False))

    elif section == 'search':
        page.head = "Search"
        searchfield = args.get('searchfield')
        searchtext = args.get('searchtext') or ''
        status = args.get('status')
        days = args.get('days')
        print_search(cur, page, searchfield, searchtext, status, days)
        page.path.append(("Search", False))

    elif section == 'addreason':
        page.head = "Add detentionreason"
        page.reasonid = args.get('reasonid') or 0
        page.name = args.get('name') or ''
        page.comment = args.get('comment') or ''
        print_detention_reasons(cur, page, section)
        page.path.append(("Add detentionreason", False))

    elif section == 'deletereason':
        page.head = "Delete detentionreason"
        page.reasonid = args.get('reasonid') or 0
        print_delete_reason(cur, page)
        page.path.append(("Delete detentionreason", False))

    elif section == 'dodeletereason':
        if params.has_key('reasonid'):
            sql_query = """
            DELETE FROM blocked_reason WHERE blocked_reasonid=%s"""
            reasonid = str(params['reasonid'])
            cur.execute(sql_query, (reasonid, ))
            
            redirect(req, 'addreason?output=Detentionreason %s deleted.'
                     % params['reasonname'])
        else:
            redirect(req, 'addreason?output=Error: No postvariable')

    elif section == 'addquarantinevlan':
        page.head = "Add quarantine vlan"
        page.quarantineid = args.get('quarantineid') or 0
        page.vlan = args.get('vlan') or ''
        page.description = args.get('description') or ''
        print_add_quarantine(cur, page)
        page.path.append(("Add quarantine vlan", False))

    elif section == 'deletequarantinevlan':
        page.head = "Delete quarantine vlan"
        page.quarantineid = args.get('quarantineid') or 0
        print_delete_quarantine(cur, page)
        page.path.append(("Delete quarantine vlan", False))

    elif section == 'dodeletequarantinevlan':
        if params.has_key('vlanid'):
            sql_query = """DELETE FROM quarantine_vlans WHERE quarantineid=%s"""
            vlanid = str(params['vlanid'])
            cur.execute(sql_query, (vlanid, ))
            
            redirect(req, 'addquarantinevlan?output=Quarantinevlan %s deleted.'
                     % params['vlan'])
        else:
            redirect(req, 'addquarantinevlan?output=Error: No postvariable')

    elif section == 'manualdetain':
        sort = args.get('sort') or 'ip'
        page.head = "Manual Detention"
        page.defaultdetention = config.get('arnoldweb','defaultdetention')
        print_manual_detention(cur, page)
        page.path.append(("Manual Detention", False))        

    elif section == 'showdetails':
        page.head = "Details"
        identity = args.get('id')
        show_details(cur, page, section, identity)
        page.path.append(("Details", False))

    elif section == 'addPredefined':
        page.head = ""
        page.path.append(("AddPredefined", False))
        page.defaultdetention = config.get('arnoldweb','defaultdetention')
        identity = args.get('blockid')
        if not identity:
            identity = 0
        print_add_predefined(cur, page, identity)

    elif section == 'doenable':
        identity = args.get('id')

        # Find all ports blocked because of this mac, and if there are
        # more than one load a new page where the user can choose
        # which ones to open.

        managec = manage.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Find mac-address of this identityid
        sql_query = "SELECT * FROM identity WHERE identityid = %s"
        cur.execute(sql_query, (identity,))
        row = cur.fetchone()

        # Select all identities where this mac is the cause of block
        sql_query = """SELECT * FROM identity
        WHERE mac = %s
        AND blocked_status IN ('quarantined', 'disabled')"""
        cur.execute(sql_query, (row['mac'],))

        # Get switchinformation from database
        blockedports = [dict(row) for row in cur.fetchall()]
        for element in blockedports:
            sql_query = """
            SELECT sysname, module, baseport FROM netbox
            LEFT JOIN module USING (netboxid)
            LEFT JOIN interface USING (netboxid)
            WHERE interfaceid=%s
            """

            try:
                managec.execute(sql_query, (element['swportid'],))
            except nav.db.driver.ProgrammingError, programming_ex:
                # We just fill a dict with info if we get any, no
                # need react on error really
                continue

            if managec.rowcount > 0:
                element.update(managec.fetchone())

        page.blockedports = blockedports
        page.head = ""
        page.path.append(("Enable", False))

    elif section == 'doenableall':
        # This section is active when you have selected ports to
        # enable from section "doenable". As nav.web.URI does not
        # support multiple get-variables with the same name, we must
        # be "creative" here.

        for getvar in args.args:
            if re.match("identityid", getvar):
                try:
                    nav.arnold.openPort(args.args[getvar], username)
                except nav.arnold.NoDatabaseInformationError, why:
                    logger.error("Error when opening %s: %s"
                                 % (args.args[getvar], why))
                    continue

        redirect(req, 'blockedports')

    elif section == 'domanualdetain':
        ip = args.get('ipadresse').strip()

        # Use modulefunction to get info about id
        try:
            info = nav.arnold.findIdInformation(ip, 3)
        except (nav.arnold.UnknownTypeError,
                nav.arnold.NoDatabaseInformationError), unknown_ex:
            redirect(req, 'manualdetain?output=%s' % unknown_ex)

        page.arg = args.args
        page.candidates = info
        page.type = args.get('detainmentgroup')
        

    elif section == 'doblock':
        # Use blockport in arnold-library to block port and update
        # database

        identity = {}
        identity['mac'] = args.get('mac')
        identity['ip'] = args.get('ip')

        netboxid = int(args.get('netboxid'))
        ifindex = int(args.get('ifindex'))

        switch_port_info = None
        try:
            switch_port_info = nav.arnold.findSwportinfo(netboxid, ifindex)
        except nav.arnold.PortNotFoundError, why:
            redirect(req, 'blockedports?output=' + str(why))

        # NB: Autoenablestep only set by a blockrun
        try:
            nav.arnold.blockPort(identity, switch_port_info,
                                 args.get('autoenable'), 0,
                                 args.get('determined'), args.get('reasonid'),
                                 args.get('comment'),
                                 req.session['user']['login'], 'block')
        except GeneralException, why:
            redirect(req, 'blockedports?output=' + str(why))

        redirect(req, 'blockedports')


    elif section == 'doquarantine':
        # Use blockport in arnold-library to block port and update
        # database

        identity = {}
        identity['mac'] = args.get('mac')
        identity['ip'] = args.get('ip')

        netboxid = int(args.get('netboxid'))
        ifindex = int(args.get('ifindex'))
        vlan = int(args.get('quarantinevlan'))

        switch_port_info = None
        try:
            switch_port_info = nav.arnold.findSwportinfo(netboxid, ifindex)
        except nav.arnold.PortNotFoundError, why:
            redirect(req, 'blockedports?output=' + str(why))

        # NB: Autoenablestep only set by a blockrun
        try:
            nav.arnold.blockPort(identity, switch_port_info,
                                 args.get('autoenable'), 0,
                                 args.get('determined'), args.get('reasonid'),
                                 args.get('comment'),
                                 req.session['user']['login'], 'quarantine',
                                 vlan)
        except GeneralException, why:
            redirect(req, 'blockedports?output=' + str(why))

        redirect(req, 'blockedports')



    elif section == 'doaddblockreason':
        reasonid = args.get('reasonid') or 0
        name = args.get('blockreason')
        comment = args.get('comment')
        if name is not '':
            try:
                nav.arnold.addReason(name, comment, reasonid)
            except nav.arnold.DbError, why:
                logger.error(why)

        redirect(req, 'addreason')

    elif section == 'doaddquarantinevlan':
        quarantineid = int(args.get('quarantineid'))
        vlan = args.get('vlan')
        description = args.get('description')

        # Check that vlan is an int
        if vlan.isdigit():
            vlan = int(vlan)

            # Check if this is update or insert.
            if quarantineid > 0:
                sql_query = """
                UPDATE quarantine_vlans
                SET description=%s, vlan=%s
                WHERE quarantineid=%s
                """
                try:
                    cur.execute(sql_query, (description, vlan, quarantineid))
                except Exception, sql_ex:
                    logger.exception(sql_ex)
                
            else:
                # Check that this quarantinevlan does not already exist.
                checkexistence = """
                SELECT * FROM quarantine_vlans WHERE vlan = %s
                """
                try:
                    cur.execute(checkexistence, (vlan,))
                except Exception, sql_ex:
                    logger.exception(sql_ex)
                    redirect(req, 'addquarantinevlan')

                if cur.rowcount > 0:
                    redirect(req, 'addquarantinevlan?'
                             'output=Quarantine vlan already exists.')
                
                sql_query = """
                INSERT INTO quarantine_vlans (description, vlan)
                VALUES (%s, %s)
                """
                try:
                    cur.execute(sql_query, (description, vlan))
                except Exception, sql_ex:
                    logger.exception(sql_ex)
                    
                
        redirect(req, 'addquarantinevlan')
            

    elif section == 'doaddpredefined':
        # blockid, blocktitle, description, reasonid, newreason,
        # mailfile, inputfile, pursuit, eincrease, duration, active,
        # user
        reasonid = args.get('reasonid')
        blockid = args.get('blockid')

        if not blockid:
            newreason = args.get('newreason')
            no_reason = re.match("--", newreason)
            if not no_reason:
                sql_query = """
                SELECT blocked_reasonid FROM blocked_reason WHERE name = %s
                """
                cur.execute(sql_query, (newreason,))
                if cur.rowcount < 1:
                    sql_query = """SELECT
                    nextval('blocked_reason_blocked_reasonid_seq')"""
                    cur.execute(sql_query)
                    reasonid = cur.fetchone()[0]
                    try:
                        sql_query = """INSERT INTO blocked_reason
                        (blocked_reasonid, name) VALUES (%s, %s)"""
                        cur.execute(sql_query, (reasonid, newreason))
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
        activeonvlans = ",".join([x.strip() for x in
                                  args.get('activeonvlans').split(",")])
        quarantineid = args.get('quarantineid')
        detainmenttype = args.get('detainmenttype')
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
        if req.session.has_key('user') and req.session['user']['id'] > 0:
            lasteditedby = req.session['user']['name']

        if blockid:

            sql_query = """ UPDATE block
            SET blocktitle=%s, blockdesc=%s, reasonid=%s, mailfile=%s,
            inputfile=%s, determined=%s, incremental=%s, blocktime=%s,
            active=%s, lastedited=now(), lastedituser=%s, activeonvlans=%s,
            detainmenttype = %s, quarantineid = %s
            WHERE blockid=%s """

            try:

                cur.execute(sql_query, (blocktitle, blockdesc, reasonid,
                                mailfile, inputfile, determined, incremental,
                                blocktime, active, lasteditedby, activeonvlans,
                                detainmenttype, quarantineid, blockid))

            except nav.db.driver.ProgrammingError, why:
                conn.rollback()
        else:
            sql_query = """
            INSERT INTO block (blocktitle, blockdesc, mailfile,
            reasonid, determined, incremental, blocktime, active,
            lastedited, lastedituser, inputfile, activeonvlans, detainmenttype,
            quarantineid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now(), %s, %s, %s, %s, %s)
            """
            try:

                cur.execute(sql_query, (blocktitle, blockdesc, mailfile,
                                reasonid, determined, incremental, blocktime,
                                active, lasteditedby, inputfile, activeonvlans,
                                detainmenttype, quarantineid))

            except nav.db.driver.ProgrammingError, why:
                conn.rollback()


        if blockid:
            redirect(req,'addPredefined?blockid=%s' %blockid)
        else:
            redirect(req,'predefined')
        
                
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
def set_menu(page):
    """ Set menu """
    buttonnames = ['History', "Detained ports", "Search",
                   "Add detentionreason", "Manual detention",
                   "Predefined Detentions", "Add Quarantine vlan"]
    buttons = {'History': 'history', "Detained ports": 'blockedports',
               "Search": 'search', "Add detentionreason": 'addreason',
               "Manual detention": 'manualdetain',
               "Predefined Detentions": 'predefined',
               "Add Quarantine vlan": "addquarantinevlan"}
    
    page.buttonnames = buttonnames
    page.buttons = buttons


############################################################
def print_history(cur, page, sort, section, days):
    """ Get history information based on input.  """

    reconnect()

    page.headersList = ['ip', 'dns', 'mac', 'netbios', 'orgid', 'status',
                        'reason', 'lastchanged', 'details']
    page.headers = {'ip': 'Ip', 'dns': 'Dns', 'mac': 'Mac',
                    'netbios': 'Netbios', 'orgid':'Orgid', 'status':'Status',
                    'reason': 'Reason', 'lastchanged': 'Lastchanged',
                    'details': '&nbsp;', '': ''}

    if days < '0':
        days = '0'
        
    page.days = days
    page.headertext = "History"
    page.hitstext = "hits in history based on activity the last " + days + \
                    " days"
    page.sort = 1

    try:
        sql_query = """
        SELECT DISTINCT identityid, ip, mac, dns, netbios, orgid,
        name AS reason, starttime,  blocked_status AS status,
        to_char(lastchanged,'YYYY-MM-DD HH24:MI:SS') as lastchanged, swportid
        FROM identity LEFT JOIN blocked_reason USING (blocked_reasonid)
        WHERE lastchanged > current_date - interval '%s days'  ORDER BY %s
        """ % (days, sort)
        cur.execute(sql_query)
        item_list = [dict(row) for row in cur.fetchall()]
    except nav.db.driver.ProgrammingError, programming_ex:
        item_list = {}

    for item in item_list:
        item['details'] = ("<a href='showdetails?id=" +
                           str(item['identityid']) + "' title='Details'>"
                           "<img src='/images/arnold/details.png'></a>")

    page.hits = len(list)
    page.list = item_list
    page.section = section


############################################################
def print_blocked(cur, page, sort, section):
    """  Print blocked """
    reconnect()

    page.headersList = ['ip', 'dns', 'netbios', 'status', 'reason', 'sysname',
                        'lastchanged', 'activate', 'details']
    page.headers = {'ip': 'Ip', 'dns':'Dns', 'netbios':'Netbios',
                    'status':'Status','reason':'Reason', 'sysname':'Switch',
                    'lastchanged':'Lastchanged', 'activate':'&nbsp;',
                    'details':'&nbsp;'}

    query = """
    SELECT DISTINCT identityid, blocked_status AS status, ip, mac,
    dns, netbios, name AS reason, starttime, lastchanged, swportid
    FROM identity
    LEFT JOIN blocked_reason USING (blocked_reasonid)
    WHERE blocked_status IN ('disabled','quarantined')
    ORDER BY %s """ % sort

    cur.execute(query)

    page.hits = cur.rowcount
    page.headertext = "List of ports currently detained"
    page.hitstext = "ports detained"
    
    item_list = [dict(row) for row in cur.fetchall()]
    
    managec = manage.cursor(cursor_factory=psycopg2.extras.DictCursor)

    for item in item_list:
        item['lastchanged'] = item['lastchanged'].strftime('%Y-%m-%d %k:%M:%S')
        item['activate'] = ("<a href='doenable?id=" + str(item['identityid']) +
                            "' title='Remove detention'>"
                            "<img src='/images/arnold/enable.png'></a>")
        item['details'] = ("<a href='showdetails?id=" +
                           str(item['identityid']) + "' title='Details'>"
                           "<img src='/images/arnold/details.png'></a>")
        
        managequery = """
        SELECT sysname, baseport FROM netbox
        JOIN interface USING (netboxid)
        WHERE interfaceid = %s
        """

        managec.execute(managequery, (item['swportid'], ))
        managelist = managec.fetchone()

        if managec.rowcount > 0:
            item['sysname'] = managelist['sysname']
        else:
            item['sysname'] = 'N/A'
            

    page.sort = 1
    page.list = item_list
    page.section = section


############################################################
def print_search(cur, page, searchfield, searchtext, status, days):
    """  Print search """
    reconnect()
    
    searchfields = ['IP', 'MAC', 'Netbios', 'dns']
    searchtext = searchtext.strip()
    page.statusfields = ['disabled', 'quarantined', 'enabled', 'both']
    page.searchfields = searchfields
    page.searchfield = searchfield
    page.searchtext = searchtext

    try:
        days = abs(int(days)) or 7
    except (ValueError, TypeError), val_ex:
        days = 7
        
    page.days = days
    page.status = status or 'both'

    if searchtext:
        
        page.headersList = ['ip', 'dns', 'mac', 'netbios', 'status', 'reason',
                            'lastchanged','history']
        page.headers = { 'ip': 'Ip', 'dns':'Dns', 'mac':'Mac',
                         'netbios':'Netbios', 'status':'Status' ,
                         'reason':'Reason', 'lastchanged':'Lastchanged',
                         'history':'&nbsp;'}

        whereclause = ''

        # Check searchfield
        if searchfield.lower() == 'ip':
            whereclause = " WHERE " + searchfield.lower() + " <<= inet %s "
        elif searchfield.lower() == 'mac':
            whereclause = " WHERE " + searchfield.lower() + " = %s"
        else:
            whereclause = " WHERE " + searchfield.lower() + " LIKE %s "
            searchtext = "%" + searchtext + "%"

        # Status - radiobuttons
        if status == 'disabled':
            whereclause += " AND blocked_status = 'disabled' "
        elif status == 'enabled':
            whereclause += " AND blocked_status = 'enabled' "
        elif status == 'quarantined':
            whereclause += " AND blocked_status = 'quarantined' "
        else:
            pass
        

        sql_query = """SELECT DISTINCT identityid, ip, mac, dns, netbios,
        orgid, name AS reason, starttime, blocked_status AS status,
        to_char(lastchanged,'YYYY-MM-DD HH24:MI:SS') AS lastchanged
        FROM identity LEFT JOIN blocked_reason
        USING (blocked_reasonid)""" + whereclause + """
        AND lastchanged > current_date - interval '""" + str(days) + """
        days'""" 
        
        try:
            cur.execute(sql_query, (searchtext,))
            searchresults = [dict(row) for row in cur.fetchall()]
            numresults = cur.rowcount
            
            if numresults == 0:
                page.headertext = ("Search for %s = %s, status = %s, last "
                                   "changed %s days ago, did not return "
                                   "anything." %
                                   (searchfield, page.searchtext,
                                    page.status, str(page.days)))
                page.searchresults = {}
            else:
                for element in searchresults:
                    element['history'] = ("<a href='showdetails?id=%s'>History"
                                          "</a>" % str(element['identityid']))

                page.headertext = ("Search results when searching for %s with "
                                   "value '%s'" % (searchfield, searchtext))
                page.searchresults = searchresults
                page.hits = cur.rowcount
                page.hitstext = "result(s) found"
                
        except nav.db.driver.ProgrammingError:
            page.searchresults = {}
            page.headertext = '<!-- %s -->\nDBError. Search for %s = %s, \
            status = %s, last changed %s days ago, did not return anything.' \
            % (sql_query, searchfield, searchtext, page.status, str(page.days))
        except nav.db.driver.DataError:
            page.searchresults = {}
            page.headertext = ("<!-- %s -->\nDataError. Searching for %s for "
                               "%s is not valid." %
                               (sql_query, searchtext, searchfield))

    else:
        page.searchresults = {}

    page.sort = 0
        

############################################################
def print_blocks(cur, page, sort, section):
    """ Print blocks """
    reconnect()
    
    page.headersList = ['blockid', 'blocktitle', 'blockdesc', 'active',
                        'edit','delete']
    page.headers = {'blockid': 'ID', 'blocktitle': 'Title',
                    'blockdesc': 'Description', 'active': 'Active',
                    'edit':'&nbsp;', 'delete':'&nbsp;'}

    cur.execute("SELECT * FROM block ORDER BY " + sort)
    element_list = [dict(row) for row in cur.fetchall()]

    for element in element_list:
        element['edit'] = ("<a href='addPredefined?blockid=%s'>Edit</a>" %
                           element['blockid'])
        element['delete'] = ("<a href='deletepredefined?blockid=%s'>Delete"
                             "</a>" % element['blockid'])
        if element['active'] == 'y':
            element['active'] = 'Yes'
        else:
            element['active'] = 'No'

    page.hits = cur.rowcount
    page.headertext = "List of current predefined detentions"
    page.hitstext = "predefined detentions registered"
    page.sort = 1
    page.list = element_list
    page.section = section


############################################################
def print_delete_predefined(cur, page):
    """  Print delete predefined """
    sql_query = """
    SELECT * FROM block WHERE blockid = %s
    """
    cur.execute(sql_query, (page.blockid, ))
    page.predefined = cur.fetchone()


############################################################
def show_details (cur, page, section, identity):
    """ Show details """
    reconnect()
    
    page.headersList = ['ip', 'dns', 'netbios', 'mac', 'sysname', 'modport',
                        'tovlan', 'status', 'autoenable', 'mail']
    page.headers = {'ip':'Ip', 'dns':'Dns', 'netbios':'Netbios', 'mac':'Mac',
                    'sysname':'Switch', 'modport':'Port', 'status':'Status',
                    'autoenable':'Autoenable', 'mail':'Mail', 'tovlan': 'Vlan'}


    # Connect to manage-database to fetch switchport-information
    managec = manage.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    sql_query = """SELECT ip, dns, netbios, mac, swportid, lastchanged,
    starttime, mail, blocked_status AS status, autoenable, tovlan
    FROM identity WHERE identityid = %s
    """
    cur.execute(sql_query, (identity,))
    entry_list = [dict(row) for row in cur.fetchall()]

    sql_query = """
    SELECT * FROM netbox
    JOIN interface USING (netboxid)
    WHERE interfaceid=%s
    """
    managec.execute(sql_query, (entry_list[0]['swportid'], ))
    managerow = managec.fetchone()

    for entry in entry_list:
        if managec.rowcount <= 0:
            page.output = ("Error: Could not find swport in database. "
                           "Perhaps switch has been replaced?")
            entry['sysname'] = "N/A"
            entry['modport'] = "N/A"
        else:
            page.output = ""
            entry['modport'] = managerow['ifname']
            entry['sysname'] = managerow['sysname']
        
        entry['starttime'] = entry['starttime'].strftime('%Y-%m-%d %k:%M:%S')
        entry['lastchanged'] = entry['lastchanged'].strftime(
            '%Y-%m-%d %k:%M:%S')

        if entry['autoenable']:
            entry['autoenable'] = entry['autoenable'].strftime(
                '%Y-%m-%d %k:%M:%S')
        else:
            entry['autoenable'] = '&nbsp;'

    page.list = entry_list
    page.section = section
    page.sort = 0
    page.headertext = "Details for " + entry_list[0]['ip']

    sql_query = """
    SELECT eventtime, event_comment AS comment,
    blocked_status AS action, name, username
    FROM event
    LEFT JOIN blocked_reason USING (blocked_reasonid)
    WHERE identityid=%s ORDER BY eventtime
    """
    cur.execute(sql_query, (identity,))

    page.headersList2 = ['eventtime', 'action', 'name', 'comment', 'username']
    page.headers2 = {'eventtime':'Eventtime', 'action':'Action',
                     'name':'Reason', 'comment':'Comment', 'username':'User'}
    list2 = [dict(row) for row in cur.fetchall()]

    for entry in list2:
        entry['name'] = entry['name'] or "&nbsp;"
        entry['comment'] = entry['comment'] or "&nbsp;"
            
    page.hits2 = cur.rowcount
    page.hitstext2 = "entries in history"
    page.headertext2 = "History"
    page.list2 = list2


############################################################
def print_detention_reasons(cur, page, section):
    """ Print detention reasons """
    reconnect()

    page.blockreasonheadersList = ['name', 'comment']
    page.blockreasonheaders = {'name':'Reason', 'comment': 'Comment'}

    query = """
    SELECT blocked_reasonid AS reasonid, name, comment
    FROM blocked_reason ORDER BY reasonid
    """
    cur.execute(query)
    page.blockreasons = cur.fetchall()
    page.headertext = "Existing reasons for detention"


############################################################
def print_delete_reason(cur, page):
    """ Print delete reasons """
    sql_query = """
    SELECT * FROM blocked_reason WHERE blocked_reasonid = %s
    """
    cur.execute(sql_query, (page.reasonid, ))
    page.reason = cur.fetchone()



############################################################
def print_manual_detention(cur, page):
    """ Print manual detention """
    reconnect()

    sql_query = """
    SELECT blocked_reasonid AS id, name FROM blocked_reason ORDER BY name
    """
    cur.execute(sql_query)
    page.reasons = cur.fetchall()

    sql_query = """
    SELECT * FROM quarantine_vlans ORDER BY vlan
    """
    cur.execute(sql_query)

    page.quarantines = cur.fetchall()


############################################################
def print_add_predefined (cur, page, identity):
    """  Print add predefined """
    reconnect()

    sql_query = """
    SELECT blocked_reasonid AS id, name
    FROM blocked_reason ORDER BY name
    """
    cur.execute(sql_query)
    page.blockreasons = cur.fetchall()

    sql_query = """
    SELECT * FROM quarantine_vlans ORDER BY vlan
    """
    cur.execute(sql_query)
    page.quarantines = cur.fetchall()

    # Initialise blockinfo-dict

    blockinfo = {'blockid':'', 'blocktitle':'', 'blockdesc':'', 'mailfile':'',
                 'reasonid':0, 'determined':'n', 'incremental':'n',
                 'blocktime':'', 'active':'n','inputfile':'',
                 'activeonvlans':'', 'detainmenttype':'disable',
                 'quarantineid': 0}

    if identity:
        cur.execute("SELECT * FROM block WHERE blockid=%s" % identity)
        blockinfo = dict(cur.fetchone())
        blockinfo['lastedited'] = blockinfo['lastedited'].strftime(
            '%Y-%m-%d %k:%M:%S')

    page.blockinfo = blockinfo


############################################################
def print_add_quarantine(cur, page):
    """ Print add quarantine """
    reconnect()

    sql_query = """
    SELECT * FROM quarantine_vlans ORDER BY vlan
    """
    cur.execute(sql_query)
    quarantines = cur.fetchall()
    page.quarantineheaderslist = ['vlan', 'description', 'edit']
    page.quarantineheaders = {'vlan':'Vlan', 'description': 'Description',
                              'edit':'Edit'}
    page.hits = cur.rowcount
    page.hitstext = "quarantinevlans defined"
    page.headertext = "Current quarantinevlans"
    page.quarantines = quarantines
    page.sort = 0

############################################################
def print_delete_quarantine(cur, page):
    """ Print delete quarantine """
    sql_query = """
    SELECT * FROM quarantine_vlans WHERE quarantineid = %s
    """
    cur.execute(sql_query, (page.quarantineid, ))
    page.quarantine = cur.fetchone()


############################################################
# A helpful function for redirecting a web-page to another one.
def redirect(req, url):
    """ Redirect """
    req.headers_out.add("Location", url)
    raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY


############################################################
# Connect to both databases
def reconnect():
    """ Reconnect """
    global manage, conn
    
    # Connect to manage-database
    manage = nav.db.getConnection('default')
    # Connect to arnold-database
    conn = db.getConnection('arnold', 'arnold')
 
