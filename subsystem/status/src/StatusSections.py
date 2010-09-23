# -*- coding: ISO8859-1 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2006 UNINETT AS
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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#
"""
Contains classes representing different sections (netboxes down,
services down, etc.) on the status and history page
"""

#################################################
## Imports

import nav.db.manage
import mx.DateTime
import nav

#################################################
## Constants

FILTER_ALL_SELECTED = 'all_selected_tkn'
BASEPATH = '/status/'
INFINITY = mx.DateTime.DateTime(999999,12,31,0,0,0)

#################################################
## Classes

class SectionBox:
    " A general section on the status or history page "

    controlBaseName = None
    title = None
    maxHeight = None

    urlRoot = None

    # ManageGetArgs instance
    getArgs = None

    # Id for sorting
    sortId = None

    def __init__(self, controlBaseName, title, getArgs, maxHeight = None,\
    urlRoot = 'status'):
        self.controlBaseName = controlBaseName
        self.sortId = controlBaseName + 'sort'
        self.getArgs = getArgs
        self.urlRoot = urlRoot
        self.maxHeight = maxHeight
        self.title = title

    def addHeadings(self):
        # Add headings with sorting urls
        i = 1
        for text,sort in self.headingDefs:
            url = None
            style = None

            sortBy = i
            if (self.getArgs.getArgs(self.sortId)):
                if int(self.getArgs.getArgs(self.sortId)[0]) == sortBy:
                    # already sorting by this column, reverse it
                    sortBy = -i
            args = self.getArgs.addArg(self.sortId,repr(sortBy))
            url = '%s?%s#%s' % (self.urlRoot,args,self.controlBaseName)
            
            self.headings.append((text,url,style,self.controlBaseName))
            i+=1

    def sort(self):
        if self.headingDefs[self.sortBy][1]:
            compareFunction = self.headingDefs[self.sortBy][1]
            self.rows.sort(compareFunction)        
        else:
            self.rows.sort()
        if self.sortReverse:
            self.rows.reverse()

    # Compare function for sorting lists of ip's
    def ipCompare(self,ip1,ip2):
        # ip1[0] and ip2[0] are the sort parameter
        ip1 = ip1[0].split('.')
        ip2 = ip2[0].split('.')
        r = 0
        try:
            for i in range(0,4):
                r = cmp(int(ip1[i]),int(ip2[i]))
                if r != 0:
                    break
        except:
            r = 0
        return r

#################################################
## Sections that inherits from SectionBox
        
class ServiceSectionBox(SectionBox):
    " Section displaying services that are down or in shadow "

    # attribs for preferences
    name = 'Services down'
    typeId = 'service'

    prefsOptions = None

    defaultSort = 3         # -3, thus sortReverse = True
    sortReverse = False 
    sortBy = defaultSort

    def __init__(self, controlBaseName,getArgs,title,filterSettings):
        # Sort reverse by column 3 (downtime)

        self.headings = []
        self.headingDefs = [('Sysname',None),
                            ('Handler',None),
                            ('Down since',None),
                            ('Downtime',None),
                            ('',None)]
        self.rows = []
        self.summary = None
        self.historyLink = []
        self.historyLink.append((BASEPATH + 'history/?type=services',
                                 'history'))
        self.historyLink.append(('/ipdevinfo/service/matrix/',
                                 'service status'))
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
        filterSettings = self.filterSettings
    
        sql = """SELECT DISTINCT n.sysname, s.handler, ah.start_time,
                now() - ah.start_time AS downtime, s.up, s.serviceid, n.netboxid
            FROM alerthist AS ah, netbox AS n, service AS s
            WHERE ah.netboxid = n.netboxid
                AND ah.subid = s.serviceid::text
                AND ah.end_time = 'infinity'
                AND ah.eventtypeid = 'serviceState'"""
 
        # parse filter settings
        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # catid
            if not filterSettings['handler'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for handler in filterSettings['handler']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "s.handler = '" + handler + "'"
                    first_line = False
                where_clause += ") "
            # state
            self.listStates = filterSettings['state']
            if not filterSettings['state'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for state in filterSettings['state']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "s.up = '" + state + "'"
                    first_line = False
                where_clause += ") "
            else: 
              where_clause += " AND (s.up = 'n' OR s.up = 's') "

        sql = sql + where_clause + " ORDER BY now()-start_time" 

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        
  
        # If components is on maintenance, do not show them
        sql = """SELECT n.sysname, s.handler, ah.start_time,
                now() - ah.start_time AS downtime, s.up, s.serviceid,
                n.netboxid
            FROM alerthist AS ah, netbox AS n, service AS s
            WHERE ah.netboxid = n.netboxid
                AND ah.subid = s.serviceid::text
                AND ah.end_time = 'infinity'
                AND ah.eventtypeid = 'maintenanceState'"""
        database.execute(sql)
        result_maint = database.fetchall()        

        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        servicesDown = 0
        servicesShadow = 0
        servicesMaintenance = 0

        SYSNAME = 0
        HANDLER = 1
        STARTTIME = 2
        DOWNTIME = 3
        UP = 4
        SERVICEID = 5
        BOXID = 6

        # Create list of components on maintenance
        onmaint = {}
        for line in result_maint:
            onmaint[(line[BOXID], line[SERVICEID])] = True
        
        for line in result:
            # If on maintenance, skip this component
            if (line[BOXID], line[SERVICEID]) in onmaint:
                servicesMaintenance += 1
                continue

            row = []
            style = None

            if line[UP] == 's':
                servicesShadow += 1
                #style = 'shadow' 
            else:
                servicesDown += 1 

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None,style))

            # Handler
            row.append((line[HANDLER],
                        '/ipdevinfo/service/handler=%s/' % line[HANDLER],
                        None,style))
 
            # Start
            row.append((line[STARTTIME].strftime('%Y-%m-%d %H:%M'),
                        None, None, style))

            # Downtime
            downTime = '%dd %dh %dmin' % (
                line[DOWNTIME].absvalues()[0],
                int(line[DOWNTIME].strftime('%H')),
                int(line[DOWNTIME].strftime('%M')),
            )
            row.append((downTime,None,None,style))

            # History link
            row.append((None,
                        BASEPATH + 'history/?type=services&id=%s' \
                        % (line[SERVICEID],),
                        ('/images/status/status-history.png',
                        'View history for this service'),
                        None))

            self.rows.append([line[self.sortBy],row])

        self.sort()

        servicesDown = str(servicesDown)
        servicesShadow = str(servicesShadow)
        servicesMaintenance = str(servicesMaintenance)
        if servicesDown=='0':
            servicesDown = 'No'
        if servicesShadow=='0':
            servicesShadow = 'No'
        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = servicesDown + ' services down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = servicesShadow + ' services in shadow'
        else:
            self.summary = servicesDown + ' services down, ' + \
                           servicesShadow.lower() + ' in shadow'

    def getFilters(controlBaseName,orgList):
        """
        Returns the filters that this section box accepts
        """
        filterHeadings = ['Organisation','Service','State']

        filterSelects = []
        table = nav.db.manage.Org

        # Org
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        for org in table.getAllIterator(orderBy = 'orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Handler
        # FIXME: The handler list should be dynamic (see seeddb.py for example)
        optionsList = [(FILTER_ALL_SELECTED,'All')]
        filterSelects.append((controlBaseName + '_' + 'handler',\
            [(FILTER_ALL_SELECTED, 'All', True),
            ('dc', 'dc', False),
            ('dns', 'dns', False),
            ('dummy', 'dummy', False),
            ('ftp', 'ftp', False),
            ('http', 'http', False),
            ('https', 'https', False),
            ('imap', 'imap', False),
            ('imaps', 'imaps', False),
            ('ldap', 'ldap', False),
            ('mysql', 'mysql', False),
            ('oracle', 'oracle', False),
            ('pop3', 'pop3', False),
            ('postgresql', 'postgresql', False),
            ('radius', 'radius', False),
            ('rpc', 'rpc', False),
            ('smb', 'smb', False),
            ('smtp', 'smtp', False),
            ('ssh', 'ssh', False)]
        ))


        # State
        filterSelects.append((controlBaseName + '_' + 'state',\
            [(FILTER_ALL_SELECTED, 'All', True),
            ('y', 'Up', False),
            ('n', 'Down', False),
            ('s', 'Shadow', False)]
        ))
        return (filterHeadings,filterSelects)
    getFilters = staticmethod(getFilters)


class ServiceMaintenanceSectionBox(SectionBox):
    " Section displaying services that are on maintenance "

    name = 'Services on maintenance'
    typeId = 'servicemaint'

    prefsOptions = None

    defaultSort = 3
    sortReverse = False 
    sortBy = defaultSort

    def __init__(self, controlBaseName, getArgs, title, filterSettings):
        # Sort reverse by column 4 (downtime)

        self.headings = []
        self.headingDefs = [('Sysname',None),
                            ('Handler',None),
                            ('Down since',None),
                            ('Downtime',None),
                            ('',None),
                            ('',None)]
        self.rows = []
        self.summary = None
        self.historyLink = []
        self.historyLink.append(('/maintenance/calendar',
                                 'maintenance schedule'))
        self.historyLink.append(('/ipdevinfo/service/matrix/',
                                 'service status'))
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName, title, getArgs, None)
        self.addHeadings()
        return

    def fill(self):
        filterSettings = self.filterSettings
    
        sql = """SELECT DISTINCT n.sysname, s.handler, ah.start_time,
                now() - ah.start_time AS downtime, s.up, s.serviceid,
                n.netboxid, ahv.val AS maint_taskid
            FROM alerthist AS ah NATURAL JOIN alerthistvar AS ahv,
                netbox AS n, service AS s
            WHERE ah.netboxid = n.netboxid
                AND ah.subid = s.serviceid::text
                AND ah.end_time = 'infinity'
                AND ah.eventtypeid = 'maintenanceState'
                AND ahv.var = 'maint_taskid'"""

        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # handler (service)
            if not filterSettings['handler'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for handler in filterSettings['handler']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "s.handler = '" + handler + "'"
                    first_line = False
                where_clause += ") "
            # state
            self.listStates = filterSettings['state']
            if not filterSettings['state'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for state in filterSettings['state']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "s.up = '" + state + "'"
                    first_line = False
                where_clause += ") "

        sql = sql + where_clause + " ORDER BY now()-ah.start_time" 

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        

        # If components is down, get down since and downtime
        sql = """SELECT DISTINCT n.sysname, s.handler, ah.start_time,
                now() - ah.start_time AS downtime, s.up, s.serviceid,
                n.netboxid
            FROM alerthist AS ah, netbox AS n, service AS s
            WHERE ah.netboxid = n.netboxid
                AND ah.subid = s.serviceid::text
                AND ah.end_time = 'infinity'
                AND ah.eventtypeid = 'serviceState'"""
        sql = sql + where_clause + " ORDER BY now()-start_time"
        database.execute(sql)
        result_down = database.fetchall()
 
        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        servicesMaintenance = 0
        servicesMaintenanceUp = 0
        servicesMaintenanceDown = 0
        servicesMaintenanceShadow = 0

        SYSNAME = 0
        HANDLER = 1
        STARTTIME = 2
        DOWNTIME = 3
        UP = 4
        SERVICEID = 5
        BOXID = 6
        MAINTID = 7

        downtimes = {}
        for line in result_down:
            downtimes[(line[SYSNAME], line[HANDLER])] = \
                (line[STARTTIME], line[DOWNTIME])
        
        for line in result:
            row = []
            style = None    

            servicesMaintenance += 1
            if line[UP] == 'y':
                servicesMaintenanceUp += 1
            elif line[UP] == 'n':
                servicesMaintenanceDown += 1
            else:
                servicesMaintenanceShadow += 1

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None, style))

            # Handler
            row.append((line[HANDLER],
                        '/ipdevinfo/service/handler=%s/' % line[HANDLER],
                        None, style))
 
            if line[UP] == 'y':
                # Down since
                row.append(('Up', None, None, style))
                # Downtime
                row.append(('', None, None, style))
            else:
                (starttime, downtime) = \
                    downtimes[(line[SYSNAME], line[HANDLER])]
                # Down since
                row.append((starttime.strftime('%Y-%m-%d %H:%M'),
                            None, None, style))
                # Downtime
                downtime = '%dd, %dh, %dmin' % (
                    downtime.absvalues()[0],
                    int(downtime.strftime('%H')),
                    int(downtime.strftime('%M')),
                )
                row.append((downtime, None, None, style))

            # Wrench icon
            row.append((None,
                        '/maintenance/view?id=%s' % line[MAINTID],
                        ('/images/status/wrench.gif',
                        'Maintenance details'),
                        None))

            # History link
            row.append((None,
                        BASEPATH + 'history/?type=services&id=%s' \
                        % (line[SERVICEID],),
                        ('/images/status/status-history.png',
                        'View history for this service'),
                        None))

            if line[UP] != 'y' and self.sortBy == STARTTIME:
                self.rows.append([starttime, row])
            elif line[UP] != 'y' and self.sortBy == DOWNTIME:
                self.rows.append([downtime, row])
            else:
                self.rows.append([line[self.sortBy], row])

        self.sort()

        servicesMaintenance = str(servicesMaintenance)
        servicesMaintenanceUp = str(servicesMaintenanceUp)
        servicesMaintenanceDown = str(servicesMaintenanceDown)
        servicesMaintenanceShadow = str(servicesMaintenanceShadow)
        if servicesMaintenance == '0':
            servicesMaintenance = 'No'
        if servicesMaintenanceUp == '0':
            servicesMaintenanceUp = 'No'
        if servicesMaintenanceDown == '0':
            servicesMaintenanceDown = 'No'
        if servicesMaintenanceShadow == '0':
            servicesMaintenanceShadow = 'No'

        self.summary = servicesMaintenance + ' services on maintenance (' + \
            servicesMaintenanceUp + ' up, ' + \
            servicesMaintenanceDown.lower() + ' down, ' + \
            servicesMaintenanceShadow.lower() + ' in shadow)'

    def getFilters(controlBaseName, orgList):
        """
        Return the filters that this section box accepts
        """

        filterHeadings = ['Organisation','Service','State']

        filterSelects = []
        table = nav.db.manage.Org

        # Org
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        for org in table.getAllIterator(orderBy = 'orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Handler
        # FIXME: The handler list should be dynamic (see seeddb.py for example)
        optionsList = [(FILTER_ALL_SELECTED,'All')]
        filterSelects.append((controlBaseName + '_' + 'handler',\
            [(FILTER_ALL_SELECTED, 'All', True),
            ('dc', 'dc', False),
            ('dns', 'dns', False),
            ('dummy', 'dummy', False),
            ('ftp', 'ftp', False),
            ('http', 'http', False),
            ('https', 'https', False),
            ('imap', 'imap', False),
            ('imaps', 'imaps', False),
            ('ldap', 'ldap', False),
            ('mysql', 'mysql', False),
            ('oracle', 'oracle', False),
            ('pop3', 'pop3', False),
            ('postgresql', 'postgresql', False),
            ('radius', 'radius', False),
            ('rpc', 'rpc', False),
            ('smb', 'smb', False),
            ('smtp', 'smtp', False),
            ('ssh', 'ssh', False)]
        ))

        # State
        filterSelects.append((controlBaseName + '_' + 'state',\
            [(FILTER_ALL_SELECTED, 'All', True),
            ('y', 'Up', False),
            ('n', 'Down', False),
            ('s', 'Shadow', False)]
        ))
        return (filterHeadings,filterSelects)
    getFilters = staticmethod(getFilters)


class NetboxSectionBox(SectionBox):
    " Section displaying netboxes that are down or in shadow "

    # attribs for preferences
    name = 'IP Devices down'
    typeId = 'netbox'

    prefsOptions = None

    defaultSort = 3
    sortReverse = False 
    sortBy = defaultSort

    def __init__(self, controlBaseName,getArgs,title,filterSettings):
        # Sort reverse by column 4 (downtime)

        self.headings = []
        self.headingDefs = [('Sysname',None),
                            ('IP',self.ipCompare),
                            ('Down since',None),
                            ('Downtime',None),
                            ('',None)]
        self.rows = []
        self.summary = None
        self.historyLink = []
        self.historyLink.append((BASEPATH + 'history/?type=boxes',
                                 'history'))
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
        filterSettings = self.filterSettings
    
        sql = """SELECT n.sysname, n.ip, ah.start_time, now() - ah.start_time
                    AS downtime, n.up, at.alerttype, n.netboxid
                FROM alerthist AS ah, netbox AS n, alerttype AS at
                WHERE ah.netboxid = n.netboxid
                    AND at.alerttypeid = ah.alerttypeid
                    AND ah.end_time = 'infinity'
                    AND ah.eventtypeid = 'boxState'
                    AND (n.up = 'n' OR n.up = 's')"""
 
        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # catid
            if not filterSettings['catid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for cat in filterSettings['catid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.catid = '" + cat + "'"
                    first_line = False
                where_clause += ") "
            # state
            self.listStates = filterSettings['state']
            if not filterSettings['state'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for state in filterSettings['state']:
                    if not first_line:
                        where_clause += " OR "
                    if state=='n':
                        # Down
                        state = 'boxDown'
                    elif state=='s':
                        # Shadow
                        state = 'boxShadow'
                    where_clause += "at.alerttype = '" + state + "'"
                    first_line = False
                where_clause += ") "
            else:
                where_clause += " AND (at.alerttype='boxDown' or " +\
                                "at.alerttype='boxShadow') "

        sql = sql + where_clause + " ORDER BY now()-start_time" 

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        

        # If components is on maintenance, do not show them
        sql = """SELECT n.sysname, n.ip, ah.start_time,
                now() - ah.start_time AS downtime, n.up, at.alerttype,
                n.netboxid
            FROM alerthist AS ah, netbox AS n, alerttype AS at
            WHERE ah.netboxid = n.netboxid
                AND ah.alerttypeid = at.alerttypeid
                AND ah.end_time = 'infinity'
                AND ah.eventtypeid = 'maintenanceState'"""
        database.execute(sql)
        result_maint = database.fetchall()        
 
        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        boxesDown = 0
        boxesShadow = 0
        boxesMaintenance = 0

        SYSNAME = 0
        IP = 1
        STARTTIME = 2
        DOWNTIME = 3
        UP = 4
        ALERTTYPE = 5
        BOXID = 6

        # Create list of components on maintenance
        onmaint = {}
        for line in result_maint:
            onmaint[line[BOXID]] = True

        for line in result:
            # If on maintenance, skip this component
            if line[BOXID] in onmaint:
                boxesMaintenance += 1
                continue
            
            row = []
            style = None

            if line[ALERTTYPE] == 'boxShadow':
                boxesShadow += 1
                #style = 'shadow' 
            else:
                boxesDown += 1 

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None, style))

            # Ip
            row.append((line[IP],None,None,style))
 
            # Down since
            row.append((line[STARTTIME].strftime('%Y-%m-%d %H:%M'),
                        None, None, style))

            # Downtime
            downTime = '%dd %dh %dmin' % (
                line[DOWNTIME].absvalues()[0],
                int(line[DOWNTIME].strftime('%H')),
                int(line[DOWNTIME].strftime('%M')),
            )

            row.append((downTime,None,None,style))

            # History icon
            row.append((None,
                        BASEPATH + 'history/?type=boxes&id=%s' % (line[BOXID],),
                        ('/images/status/status-history.png',
                        'View history for this box'),
                        None))

            self.rows.append([line[self.sortBy],row])

        self.sort()

        boxesDown = str(boxesDown)
        boxesShadow = str(boxesShadow)
        boxesMaintenance = str(boxesMaintenance)

        if boxesDown == '0':
            boxesDown = 'No'
        if boxesShadow == '0':
            boxesShadow = 'No'
        if boxesMaintenance == '0':
            boxesMaintenance = 'No'

        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = boxesDown + ' IP devices down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = boxesShadow + ' IP devices in shadow'
        else:
            self.summary = boxesDown + ' IP devices down, ' + \
                           boxesShadow.lower() + ' in shadow'

    def getFilters(controlBaseName,orgList):
        """
        Return the filters that this section accepts
        """

        filterHeadings = ['Organisation','Category','State']

        filterSelects = []

        # Org
        table = nav.db.manage.Org
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for org in table.getAllIterator(orderBy='orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Cat
        table = nav.db.manage.Cat
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for cat in table.getAllIterator():
             optionsList.append((cat.catid,cat.catid,False))
        filterSelects.append((controlBaseName + '_' + 'catid',optionsList))

        # State
        filterSelects.append((controlBaseName + '_' + 'state',\
        [(FILTER_ALL_SELECTED,'All',True),('n','Down',False),\
        ('s','Shadow',False)]))
        return (filterHeadings,filterSelects)
    getFilters = staticmethod(getFilters)


class NetboxMaintenanceSectionBox(SectionBox):
    " Section displaying netboxes that are on maintenance "

    name = 'IP devices on maintenance'
    typeId = 'netboxmaint'

    prefsOptions = None

    defaultSort = 3
    sortReverse = False 
    sortBy = defaultSort

    def __init__(self, controlBaseName, getArgs, title, filterSettings):
        # Sort reverse by column 4 (downtime)

        self.headings = []
        self.headingDefs = [('Sysname',None),
                            ('IP',self.ipCompare),
                            ('Down since',None),
                            ('Downtime',None),
                            ('',None),
                            ('',None)]
        self.rows = []
        self.summary = None
        self.historyLink = []
        self.historyLink.append(('/maintenance/calendar',
                                 'maintenance schedule'))
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName, title, getArgs, None)
        self.addHeadings()
        return

    def fill(self):
        filterSettings = self.filterSettings

        sql = """SELECT DISTINCT n.sysname, n.ip, ah.start_time,
                now() - ah.start_time AS downtime, n.up, at.alerttype,
                n.netboxid, ahv.val AS maint_taskid
            FROM alerthist AS ah NATURAL JOIN alerthistvar AS ahv,
                netbox AS n, alerttype AS at
            WHERE ah.netboxid = n.netboxid
                AND ah.alerttypeid = at.alerttypeid
                AND ah.end_time = 'infinity'
                AND ah.eventtypeid = 'maintenanceState'
                AND ahv.var = 'maint_taskid'"""

        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # catid
            if not filterSettings['catid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for cat in filterSettings['catid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.catid = '" + cat + "'"
                    first_line = False
                where_clause += ") "
            # state
            self.listStates = filterSettings['state']
            if not filterSettings['state'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for state in filterSettings['state']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.up = '" + state + "'"
                    first_line = False
                where_clause += ") "

        sql = sql + where_clause + " ORDER BY now()-ah.start_time"

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()

        # If components is down, get down since and downtime
        sql = """SELECT DISTINCT n.sysname, n.ip, ah.start_time,
                now() - ah.start_time AS downtime, n.up, at.alerttype,
                n.netboxid
            FROM alerthist AS ah, netbox AS n, alerttype AS at
            WHERE ah.netboxid = n.netboxid
                AND ah.alerttypeid = at.alerttypeid
                AND ah.end_time = 'infinity'
                AND ah.eventtypeid = 'boxState'"""
        sql = sql + where_clause + " ORDER BY now()-start_time"
        database.execute(sql)
        result_down = database.fetchall()

        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        boxesMaintenance = 0
        boxesMaintenanceUp = 0
        boxesMaintenanceDown = 0
        boxesMaintenanceShadow = 0

        SYSNAME = 0
        IP = 1
        STARTTIME = 2
        DOWNTIME = 3
        UP = 4
        ALERTTYPE = 5
        BOXID = 6
        MAINTID = 7

        downtimes = {}
        for line in result_down:
            downtimes[(line[SYSNAME], line[IP])] = \
                (line[STARTTIME], line[DOWNTIME])

        for line in result:
            row = []
            style = None

            boxesMaintenance += 1
            if line[UP] == 'y':
                boxesMaintenanceUp += 1
            elif line[UP] == 'n':
                boxesMaintenanceDown += 1
            else:
                boxesMaintenanceShadow += 1

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None, style))

            # Ip
            row.append((line[IP], None, None, style))

            if line[UP] == 'y':
                # Down since
                row.append(('Up', None, None, style))
                # Downtime
                row.append(('', None, None, style))
            else:
                if downtimes.has_key((line[SYSNAME], line[IP])):
                    (starttime, downtime) = \
                        downtimes[(line[SYSNAME], line[IP])]
                else:
                    (starttime, downtime) = (None, None)

                # Down since
                if starttime:
                    starttime = starttime.strftime('%Y-%m-%d %H:%M')
                else:
                    starttime = 'N/A'
                row.append((starttime, None, None, style))

                # Downtime
                if downtime:
                    downtime = '%dd %dh %dmin' % (
                        downtime.absvalues()[0],
                        int(downtime.strftime('%H')),
                        int(downtime.strftime('%M')),
                    )
                else:
                    downtime = 'N/A'
                row.append((downtime, None, None, style))

            # Wrench icon
            row.append((None,
                        '/maintenance/view?id=%s' % line[MAINTID],
                        ('/images/status/wrench.gif',
                        'Maintenance details'),
                        None))

            # History icon
            row.append((None,
                        BASEPATH + 'history/?type=boxes&id=%s' % line[BOXID],
                        ('/images/status/status-history.png',
                        'View history for this box'),
                        None))

            if line[UP] != 'y' and self.sortBy == STARTTIME:
                self.rows.append([starttime, row])
            elif line[UP] != 'y' and self.sortBy == DOWNTIME:
                self.rows.append([downtime, row])
            else:
                self.rows.append([line[self.sortBy], row])

        self.sort()

        boxesMaintenance = str(boxesMaintenance)
        boxesMaintenanceUp = str(boxesMaintenanceUp)
        boxesMaintenanceDown = str(boxesMaintenanceDown)
        boxesMaintenanceShadow = str(boxesMaintenanceShadow)
        if boxesMaintenance == '0':
            boxesMaintenance = 'No'
        if boxesMaintenanceUp == '0':
            boxesMaintenanceUp = 'No'
        if boxesMaintenanceDown == '0':
            boxesMaintenanceDown = 'No'
        if boxesMaintenanceShadow == '0':
            boxesMaintenanceShadow = 'No'

        self.summary = boxesMaintenance + ' IP devices on maintenance (' + \
            boxesMaintenanceUp + ' up, ' + \
            boxesMaintenanceDown.lower() + ' down, ' + \
            boxesMaintenanceShadow.lower() + ' in shadow)'

    def getFilters(controlBaseName,orgList):
        """
        Return the filters that this section accepts
        """

        filterHeadings = ['Organisation','Category','State']

        filterSelects = []

        # Org
        table = nav.db.manage.Org
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for org in table.getAllIterator(orderBy='orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Cat
        table = nav.db.manage.Cat
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for cat in table.getAllIterator():
             optionsList.append((cat.catid,cat.catid,False))
        filterSelects.append((controlBaseName + '_' + 'catid',optionsList))

        # State
        filterSelects.append((controlBaseName + '_' + 'state',\
        [(FILTER_ALL_SELECTED,'All',True),('n','Down',False),\
        ('s','Shadow',False)]))
        return (filterHeadings,filterSelects)
    getFilters = staticmethod(getFilters)


class ModuleSectionBox(SectionBox):
    " Section displaying modules that are down or in shadow "
    
    # attribs for preferences
    name = 'Modules down'
    typeId = 'module'     
 
    prefsOptions = None

    defaultSort = 4      
    sortReverse = False 
    sortBy = defaultSort

    def __init__(self, controlBaseName,getArgs,title,filterSettings):
        # Sort reverse by column 4 (downtime)

        self.headings = []
        self.headingDefs = [('Sysname',None),
                            ('IP',self.ipCompare),
                            ('Module',None),
                            ('Down since',None),
                            ('Downtime',None),
                            ('',None)]
        self.rows = []
        self.summary = None
        self.historyLink = []
        self.historyLink.append((BASEPATH + 'history/?type=modules',
                                 'history'))
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
        filterSettings = self.filterSettings
    
        sql = """SELECT n.sysname, n.ip, m.module, ah.start_time,
                    now() - ah.start_time, n.up, at.alerttype, m.moduleid,
                    n.netboxid
                FROM alerthist AS ah, netbox AS n, alerttype AS at, module AS m
                WHERE ah.netboxid = n.netboxid
                    AND ah.subid = m.moduleid::text
                    AND ah.end_time = 'infinity'
                    AND ah.eventtypeid = 'moduleState'
                    AND ah.alerttypeid = at.alerttypeid
                    AND at.alerttype = 'moduleDown'"""
 
        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # catid
            if not filterSettings['catid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for cat in filterSettings['catid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "n.catid = '" + cat + "'"
                    first_line = False
                where_clause += ") "
            # state
            self.listStates = filterSettings['state']
            if not filterSettings['state'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for state in filterSettings['state']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "m.up = '" + state + "'"
                    first_line = False
                where_clause += ") "
            else:
              where_clause += "AND (m.up='n' OR m.up='s') "

        sql = sql + where_clause + " ORDER BY now() - start_time" 

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        

        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        modulesDown = 0
        modulesShadow = 0

        SYSNAME = 0
        IP = 1
        MODULE = 2
        STARTTIME = 3
        DOWNTIME = 4
        UP = 5
        ALERTTYPE = 6
        MODULEID = 7
        BOXID = 8
        
        for line in result:
            row = []
            style = None    

            if line[UP] == 's':
                modulesShadow += 1
                style = 'shadow' 
            else:
                modulesDown += 1 

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None,
                        style))

            # Ip
            row.append((line[IP],None,None,style))
 
            # Module
            row.append((str(line[MODULE]),None,None,style))

            # Down since
            row.append((line[STARTTIME].strftime('%Y-%m-%d %H:%M'),
                        None,None,style))

            # Downtime
            downTime = '%dd %dh %dmin' % (
                line[DOWNTIME].absvalues()[0],
                int(line[DOWNTIME].strftime('%H')),
                int(line[DOWNTIME].strftime('%M')),
            )

            row.append((downTime,None,None,style))

            # History icon
            row.append((None,
                        BASEPATH + 'history/?type=modules&id=%s' \
                        % (line[MODULEID],),
                        ('/images/status/status-history.png',
                        'View history for this module'),
                        None))

            self.rows.append([line[self.sortBy],row])

        self.sort()

        modulesDown = str(modulesDown)
        modulesShadow = str(modulesShadow)
        if modulesDown=='0':
            modulesDown = 'No'
        if modulesShadow=='0':
            modulesShadow = 'No'
        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = modulesDown + ' modules down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = modulesShadow + ' modules in shadow'
        else:
            self.summary = modulesDown + ' modules down, ' + \
                           modulesShadow.lower() + ' in shadow'

    def getFilters(controlBaseName,orgList):
        """
        Return the filters that this section accepts
        """

        filterHeadings = ['Organisation','Category','State']

        filterSelects = []

        # Org
        table = nav.db.manage.Org
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for org in table.getAllIterator(orderBy='orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Cat
        table = nav.db.manage.Cat
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for cat in table.getAllIterator():
             optionsList.append((cat.catid,cat.catid,False))
        filterSelects.append((controlBaseName + '_' + 'catid',optionsList))

        # State
        filterSelects.append((controlBaseName + '_' + 'state',\
        [(FILTER_ALL_SELECTED,'All',True),('n','Down',False),\
        ('s','Shadow',False)]))
        return (filterHeadings,filterSelects)
    getFilters = staticmethod(getFilters)


class ThresholdSectionBox(SectionBox):
    " Section displaying threshold events "

    # attribs for preferences
    name = 'Thresholds exceeded'
    typeId = 'threshold'

    prefsOptions = None

    defaultSort = 3         # -3, thus sortReverse = True
    sortReverse = False 
    sortBy = defaultSort

    def __init__(self, controlBaseName,getArgs,title,filterSettings):
        # Sort reverse by column 3 (downtime)

        self.headings = []
        self.headingDefs = [('Sysname',None),
                            ('Description',None),
                            ('Exceeded since',None),
                            ('Time exceeded',None),
                            ('',None)]
        self.rows = []
        self.summary = None
        self.historyLink = []
        self.historyLink.append((BASEPATH + 'history/?type=thresholds',
                                 'history'))
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
        filterSettings = self.filterSettings
    
        sql = "SELECT netbox.sysname," +\
              "alerthist.start_time,now()-alerthist.start_time," +\
              "rrd_datasource.descr,rrd_datasource.units," +\
	          "rrd_datasource.threshold,netbox.netboxid," +\
              "rrd_datasource.rrd_datasourceid " +\
              "FROM alerthist,alerttype,netbox,rrd_datasource " + \
              "WHERE alerthist.netboxid=netbox.netboxid AND " +\
              "alerthist.end_time='infinity' AND " +\
              "alerthist.eventtypeid='thresholdState' AND " +\
              "alerthist.alerttypeid=alerttype.alerttypeid AND " +\
    	      "alerttype.alerttype='exceededThreshold' AND " +\
	          "alerthist.subid=rrd_datasource.rrd_datasourceid::text  "
 
        # parse filter settings
        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "netbox.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # catid
            if not filterSettings['catid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for cat in filterSettings['catid']:
                    if not first_line:
                        where_clause += " OR "
                    where_clause += "netbox.catid = '" + cat + "'"
                    first_line = False
                where_clause += ") "
            # state
            #self.listStates = filterSettings['type']
            #if not filterSettings['type'].count(FILTER_ALL_SELECTED):
            #    where_clause += " and ("
            #    first_line = True
            #    for atype in filterSettings['type']:
            #        if not first_line:
            #            where_clause += " or "
            #        where_clause += "alerthist.alerttype = '" + atype + "'"
            #        first_line = False
            #    where_clause += ") "

        sql = sql + where_clause + " ORDER BY now()-start_time" 

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        
  
        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        thresholdsExceeded = 0

        SYSNAME = 0
        DESCRIPTION = 1
        STARTTIME = 2
        DOWNTIME = 3
        DATASOURCE_DESCR = 4
        DATASOURCE_UNITS = 5
        DATASOURCE_THRESHOLD = 6
        BOXID = 7
        DATASOURCEID = 8
        
        for tmpline in result:
            tmpline = list(tmpline)
            # Must insert description (-1 since description isnt there yet)
            if not tmpline[DATASOURCE_DESCR-1]:
                tmpline[DATASOURCE_DESCR-1] = 'Unknown datasource '
            if not tmpline[DATASOURCE_THRESHOLD-1]:
                tmpline[DATASOURCE_THRESHOLD-1] = ''
            if not tmpline[DATASOURCE_UNITS-1]:
                tmpline[DATASOURCE_UNITS-1] = ''
            descr = tmpline[DATASOURCE_DESCR-1] + ' exceeded ' +\
                    str(tmpline[DATASOURCE_THRESHOLD-1]) +\
                    str(tmpline[DATASOURCE_UNITS-1])
            line = list(tmpline[0:1]) + [descr] + list(tmpline[1:8])

            row = []
            style = None    

            thresholdsExceeded += 1

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None,style))

            # Description
            row.append((line[DESCRIPTION],None,None,style))

            # Start
            row.append((line[STARTTIME].strftime('%Y-%m-%d %H:%M'),
                        None, None, style))

            # Downtime
            downTime = '%dd %dh %dmin' % (
                line[DOWNTIME].absvalues()[0],
                int(line[DOWNTIME].strftime('%H')),
                int(line[DOWNTIME].strftime('%M')),
            )
            row.append((downTime,None,None,style))

            # History link
            row.append((None,
                        BASEPATH + 'history/?type=thresholds&id=%s' \
                        % (line[DATASOURCEID],),
                        ('/images/status/status-history.png',
                        'View history for this datasource'),
                        None))

            self.rows.append([line[self.sortBy],row])

        self.sort()

        thresholdsExceeded = str(thresholdsExceeded)
        if thresholdsExceeded=='0':
            thresholdsExceeded = 'No'
        if thresholdsExceeded=='1':
            self.summary = thresholdsExceeded + ' threshold exceeded'
        else:
            self.summary = thresholdsExceeded + ' thresholds exceeded'

    def getFilters(controlBaseName,orgList):
        """
        Returns the filters that this section box accepts
        """
        filterHeadings = ['Organisation','Category']

        filterSelects = []
        table = nav.db.manage.Org

        # Org
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        for org in table.getAllIterator(orderBy = 'orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Cat
        table = nav.db.manage.Cat
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for cat in table.getAllIterator():
             optionsList.append((cat.catid,cat.catid,False))
        filterSelects.append((controlBaseName + '_' + 'catid',optionsList))

        # Alerttype
        #filterSelects.append((controlBaseName + '_' + 'type',\
        #[(FILTER_ALL_SELECTED,'All',True),
        # ('exceededThreshold','exceededThreshold',False),\
        # ('belowThreshold','belowThreshold',False)]))
        return (filterHeadings,filterSelects)
    getFilters = staticmethod(getFilters)


##
## History sections
##


class NetboxHistoryBox(SectionBox):
    " Section showing the history of netboxes that have been down or in shadow "
   
    defaultSort = 2
    sortBy = defaultSort
    sortReverse = True
    
    def __init__(self,controlBaseName,getArgs,title,date,boxid=None):
        self.headings = []
        self.rows = []
        if boxid:
            # Don't show history icon when we're looking at one box
            self.headingDefs = [('Sysname',None),
                                ('IP',self.ipCompare),
                                ('From',None),
                                ('To',None),
                                ('Downtime',None),
                                ('boxState',None)]
                                
        else:
            self.headingDefs = [('Sysname',None),
                                ('IP',self.ipCompare),
                                ('From',None),
                                ('To',None),
                                ('Downtime',None),
                                ('boxState',None),
                                ('',None)]

        self.date = date
        self.boxid = boxid

        SectionBox.__init__(self,controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
        sql = "SELECT netbox.sysname,netbox.ip," +\
              "alerthist.start_time,alerthist.end_time," +\
              "netbox.netboxid,alerttype.alerttype " +\
              "FROM alerthist,netbox,alerttype WHERE " + \
              "alerthist.netboxid=netbox.netboxid AND " +\
              "alerthist.alerttypeid=alerttype.alerttypeid AND " +\
              "alerthist.eventtypeid='boxState' AND " +\
              "(alerttype.alerttype='boxDown' OR " +\
              "alerttype.alerttype='boxUp' OR " +\
              "alerttype.alerttype='boxShadow' OR " +\
              "alerttype.alerttype='boxSunny') AND " +\
              "date(start_time) = '%s' " %(self.date,)

        
        if self.boxid:
            sql += " AND alerthist.netboxid='%s'" % (self.boxid,)

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        

        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        SYSNAME = 0
        IP = 1
        FROM = 2
        TO = 3
        DOWNTIME = 4
        BOXID = 5
        ALERTTYPE = 6

        for tmpline in result:
            # Must insert downtime
            if not tmpline[TO] or tmpline[TO]==INFINITY:
                downTime = mx.DateTime.now() - tmpline[FROM]
            else:
                downTime = tmpline[TO] - tmpline[FROM]
            line = list(tmpline[0:4]) + [downTime] + list(tmpline[4:6])

            row = []

            style = None
            #if (line[ALERTTYPE]=='boxShadow' or line[ALERTTYPE]=='boxSunny'):
            #    style = 'shadow'

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None,style))

            # IP
            row.append((line[IP],None,None,style))
 

            # From
            row.append((line[FROM].strftime('%Y-%m-%d %H:%M'),
                       None, None, style))

            # To
            if not line[TO] or line[TO]==INFINITY:
                row.append(('Still down',None,None,style))
            else:
                row.append((line[TO].strftime('%Y-%m-%d %H:%M'),
                           None, None, style))

            # Downtime
            downTime = '%dd %dh %dmin' % (
                line[DOWNTIME].absvalues()[0],
                int(line[DOWNTIME].strftime('%H')),
                int(line[DOWNTIME].strftime('%M')),
            )
            row.append((downTime,None,None,style))

            # boxState
            row.append((line[ALERTTYPE],None,None,style))

            # History
            if not self.boxid:
                row.append((None,
                            BASEPATH + 'history/?type=boxes&id=%s' \
                            % (line[BOXID],),
                            ('/images/status/status-history.png',
                            'View history for thix box'),
                            style))
            
            self.rows.append([line[self.sortBy],row])
        self.sort()

class ServiceHistoryBox(SectionBox):
    " Section showing history for services "
    
    defaultSort = 2
    sortBy = defaultSort
    sortReverse = True
    
    def __init__(self,controlBaseName,getArgs,title,date,serviceid=None):
        self.headings = []
        self.rows = []
        self.date = date
        self.serviceid = serviceid

        if serviceid:
            # Don't show history icon when we're looking at one box
            self.headingDefs = [('Sysname',None),
                                ('Handler',None),
                                ('From',None),
                                ('To',None),
                                ('Downtime',None)]
                                
        else:
            self.headingDefs = [('Sysname',None),
                                ('Handler',None),
                                ('From',None),
                                ('To',None),
                                ('Downtime',None),
                                ('',None)]

        SectionBox.__init__(self,controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):

        sql = "SELECT netbox.sysname,service.handler," +\
              "alerthist.start_time,alerthist.end_time,netbox.netboxid,"+\
              "alerttype.alerttype,service.serviceid FROM netbox,"+\
              "service,alerthist LEFT JOIN alerttype using(alerttypeid) "+\
              "WHERE alerthist.netboxid = netbox.netboxid AND "+\
              "alerthist.subid=service.serviceid::text AND " +\
              "alerthist.eventtypeid='serviceState' AND " +\
              "date(start_time) = '%s' " %(self.date,)
            
        if self.serviceid:
            sql += " AND service.serviceid='%s'" % (self.serviceid,)

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        

        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        SYSNAME = 0
        HANDLER = 1
        FROM = 2
        TO = 3
        DOWNTIME = 4
        BOXID = 5
        ALERTTYPE = 6
        SERVICEID = 7

        for tmpline in result:
            # Must insert downtime
            if not tmpline[TO] or tmpline[TO]==INFINITY:
                downTime = mx.DateTime.now() - tmpline[FROM]
            else:
                downTime = tmpline[TO] - tmpline[FROM]
            line = list(tmpline[0:4]) + [downTime] + list(tmpline[4:7])
            row = []

            style = None
            #if (line[ALERTTYPE]=='boxShadow' or line[ALERTTYPE]=='boxSunny'):
            #    style = 'shadow'

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None,style))

            # Handler
            row.append((line[HANDLER],None,None,style))
 

            # From
            row.append((line[FROM].strftime('%Y-%m-%d %H:%M'),
                       None, None, style))

            # To
            if not line[TO] or line[TO]==INFINITY:
                row.append(('Still down',None,None,style))
            else:
                row.append((line[TO].strftime('%Y-%m-%d %H:%M'),
                           None, None, style))

            # Downtime
            downTime = '%dd %dh %dmin' % (
                line[DOWNTIME].absvalues()[0],
                int(line[DOWNTIME].strftime('%H')),
                int(line[DOWNTIME].strftime('%M')),
            )
            row.append((downTime,None,None,style))

            # History
            if not self.serviceid:
                row.append((None,
                            BASEPATH + 'history/?type=services&id=%s' \
                            % (line[SERVICEID],),
                            ('/images/status/status-history.png',
                            'View history for this service'),
                            style))
            
            self.rows.append([line[self.sortBy],row])
        self.sort()


class ModuleHistoryBox(SectionBox):
    " Section showing history for modules "
    
    defaultSort = 2
    sortBy = defaultSort
    sortReverse = True
    
    def __init__(self,controlBaseName,getArgs,title,date,moduleid=None):
        self.headings = []
        self.rows = []
        self.date = date
        self.moduleid = moduleid

        if moduleid:
            # Don't show history icon when we're looking at one box
            self.headingDefs = [('Sysname',None),
                                ('Module',None),
                                ('From',None),
                                ('To',None),
                                ('Downtime',None)]
                                
        else:
            self.headingDefs = [('Sysname',None),
                                ('Module',None),
                                ('From',None),
                                ('To',None),
                                ('Downtime',None),
                                ('',None)]

        SectionBox.__init__(self,controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):

        sql = """
            SELECT
                netbox.sysname, module.module, alerthist.start_time,
                alerthist.end_time, netbox.netboxid, alerttype.alerttype,
                module.moduleid
            FROM netbox, module, alerthist
            LEFT JOIN alerttype using(alerttypeid)
            WHERE
                alerthist.netboxid = netbox.netboxid AND
                alerthist.subid = module.moduleid::text AND
                alerthist.eventtypeid = 'moduleState' AND
                (
                  alerttype.alerttype = 'moduleDown' OR
                  alerttype.alerttype = 'moduleUp'
                ) AND
                date(start_time) = '%s' """ % (self.date,)

        if self.moduleid:
            sql += " AND module.moduleid='%s'" % (self.moduleid,)

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        

        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        SYSNAME = 0
        MODULE = 1
        FROM = 2
        TO = 3
        DOWNTIME = 4
        BOXID = 5
        ALERTTYPE = 6
        MODULEID = 7

        for tmpline in result:
            # Must insert downtime
            if not tmpline[TO] or tmpline[TO]==INFINITY:
                downTime = mx.DateTime.now() - tmpline[FROM]
            else:
                downTime = tmpline[TO] - tmpline[FROM]
            line = list(tmpline[0:4]) + [downTime] + list(tmpline[4:7])
            row = []

            style = None
            #if (line[ALERTTYPE]=='boxShadow' or line[ALERTTYPE]=='boxSunny'):
            #    style = 'shadow'

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None,style))

            # Handler
            row.append((str(line[MODULE]),None,None,style))
 

            # From
            row.append((line[FROM].strftime('%Y-%m-%d %H:%M'),
                       None, None, style))

            # To
            if not line[TO] or line[TO]==INFINITY:
                row.append(('Still down',None,None,style))
            else:
                row.append((line[TO].strftime('%Y-%m-%d %H:%M'),
                           None, None, style))

            # Downtime
            downTime = '%dd %dh %dmin' % (
                line[DOWNTIME].absvalues()[0],
                int(line[DOWNTIME].strftime('%H')),
                int(line[DOWNTIME].strftime('%M')),
            )
            row.append((downTime,None,None,style))

            # History
            if not self.moduleid:
                row.append((None,
                            BASEPATH + 'history/?type=modules&id=%s' \
                            % (line[MODULEID],),
                            ('/images/status/status-history.png',
                            'View history for this module'),
                            style))
            
            self.rows.append([line[self.sortBy],row])
        self.sort()


class ThresholdHistoryBox(SectionBox):
    " Section showing history for threshold "
    
    defaultSort = 2
    sortBy = defaultSort
    sortReverse = True
    
    def __init__(self,controlBaseName,getArgs,title,date,dataid=None):
        self.headings = []
        self.rows = []
        self.date = date
        self.dataid = dataid

        if dataid:
            # Don't show history icon when we're looking at one box
            self.headingDefs = [('Sysname',None),
                                ('Description',None),
                                ('From',None),
                                ('To',None),
                                ('Time exceeded',None)]
                                
        else:
            self.headingDefs = [('Sysname',None),
                                ('Description',None),
                                ('From',None),
                                ('To',None),
                                ('Time exceeded',None),
                                ('',None)]

        SectionBox.__init__(self,controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
 
        sql = "SELECT netbox.sysname," +\
              "alerthist.start_time,alerthist.end_time,"+\
              "rrd_datasource.descr,rrd_datasource.units," +\
              "rrd_datasource.threshold," +\
              "netbox.netboxid,rrd_datasource.rrd_datasourceid " +\
              "FROM netbox,rrd_datasource,"+\
              "alerthist LEFT JOIN alerttype using(alerttypeid) "+\
              "WHERE alerthist.netboxid = netbox.netboxid AND "+\
              "alerthist.subid=rrd_datasource.rrd_datasourceid::text AND " +\
              "alerthist.eventtypeid='thresholdState' AND " +\
              "(alerttype.alerttype='exceededThreshold' OR " +\
              "alerttype.alerttype='belowThreshold') AND " +\
              "date(start_time) = '%s' " %(self.date,)
            
        if self.dataid:
            sql += " AND rrd_datasource.rrd_datasourceid='%s'" % \
                   (self.dataid,)

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        

        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        SYSNAME = 0
        DESCR = 1
        FROM = 2
        TO = 3
        DURATION = 4
        DATASOURCE_DESCR = 5
        DATASOURCE_UNITS = 6
        DATASOURCE_THRESHOLD = 7
        BOXID = 8
        DATASOURCEID = 9
        
        for tmpline in result:
            # Must insert description (-2 since description isnt there yet)
            tmpline = list(tmpline)
            if not tmpline[DATASOURCE_DESCR-2]:
                tmpline[DATASOURCE_DESCR-2] = 'Unknown datasource'
            if not tmpline[DATASOURCE_THRESHOLD-2]:
                tmpline[DATASOURCE_THRESHOLD-2] = ''
            if not tmpline[DATASOURCE_UNITS-2]:
                tmpline[DATASOURCE_UNITS-2] = ''
                
            descr = tmpline[DATASOURCE_DESCR-2] + ' exceeded ' +\
                    tmpline[DATASOURCE_THRESHOLD-2] +\
                    tmpline[DATASOURCE_UNITS-2]
            line = list(tmpline[0:1]) + [descr] + list(tmpline[1:10])
            # Must insert duration
            if not line[TO] or line[TO]==INFINITY:
                duration = mx.DateTime.now() - line[FROM]
            else:
                duration = line[TO] - line[FROM]
            line = list(line[0:4]) + [duration] + list(line[4:10])
            row = []

            style = None
            #if (line[ALERTTYPE]=='boxShadow' or line[ALERTTYPE]=='boxSunny'):
            #    style = 'shadow'

            # Sysname
            row.append((line[SYSNAME],
                        '/ipdevinfo/%s/' % line[SYSNAME],
                        None,style))

            # Handler
            row.append((str(line[DESCR]),None,None,style))
 

            # From
            row.append((line[FROM].strftime('%Y-%m-%d %H:%M'),
                       None, None, style))

            # To
            if not line[TO] or line[TO]==INFINITY:
                row.append(('Still exceeded',None,None,style))
            else:
                row.append((line[TO].strftime('%Y-%m-%d %H:%M'),
                           None, None, style))

            # Duration
            duration = str(line[DURATION].absvalues()[0]) + ' d, ' + \
                           line[DURATION].strftime('%H') + ' h, ' +\
                           line[DURATION].strftime('%M') + ' min'
            row.append((duration,None,None,style))

            # History
            if not self.dataid:
                row.append((None,
                            BASEPATH + 'history/?type=thresholds&id=%s' \
                            % (line[DATASOURCEID],),
                            ('/images/status/status-history.png',
                            'View history for this datasource'),
                            style))
            
            self.rows.append([line[self.sortBy],row])
        self.sort()
