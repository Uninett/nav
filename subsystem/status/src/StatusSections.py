"""
$Id$

This file id part of the NAV project.

Contains classes representing different sections (netboxes down,
services down, etc.) on the status and history page

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
"""

#################################################
## Imports

import nav.db.manage,mx.DateTime,nav
from nav.web import urlbuilder

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
    urlRoot = 'status.py'):
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
        self.historyLink = [BASEPATH + 'history/?type=services','(history)']
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
        filterSettings = self.filterSettings
    
        sql = "SELECT netbox.sysname,service.handler," +\
              "alerthist.start_time,now()-alerthist.start_time," +\
              "service.up,service.serviceid,netbox.netboxid " +\
              "FROM alerthist,netbox,service " + \
              "WHERE alerthist.netboxid=netbox.netboxid AND " +\
              "alerthist.subid=service.serviceid AND " +\
              "alerthist.end_time='infinity' AND " +\
              "alerthist.eventtypeid='serviceState' "
 
        # parse filter settings
        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " or "
                    where_clause += "netbox.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # catid
            if not filterSettings['handler'].count(FILTER_ALL_SELECTED):
                where_clause += " AND ("
                first_line = True
                for handler in filterSettings['handler']:
                    if not first_line:
                        where_clause += " or "
                    where_clause += "service.handler = '" + handler + "'"
                    first_line = False
                where_clause += ") "
            # state
            self.listStates = filterSettings['state']
            if not filterSettings['state'].count(FILTER_ALL_SELECTED):
                where_clause += " and ("
                first_line = True
                for state in filterSettings['state']:
                    if not first_line:
                        where_clause += " or "
                    where_clause += "service.up = '" + state + "'"
                    first_line = False
                where_clause += ") "
            else: 
              where_clause += "AND (service.up = 'n' OR service.up='s') "

        sql = sql + where_clause + " ORDER BY now()-start_time" 

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        
  
        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        servicesDown = 0
        servicesShadow = 0

        SYSNAME = 0
        HANDLER = 1
        STARTTIME = 2
        DOWNTIME = 3
        UP = 4
        SERVICEID = 5
        BOXID = 6
        
        for line in result:
            row = []
            style = None    

            if line[UP] == 's':
                servicesShadow += 1
                #style = 'shadow' 
            else:
                servicesDown += 1 

            # Sysname
            row.append((line[SYSNAME],
                        urlbuilder.createUrl(id=line[BOXID],division='netbox'),
                        None,style))

            # Handler
            row.append((line[HANDLER],urlbuilder.createUrl(id=line[HANDLER],
                        division='service'),None,style))
 
            # Start
            row.append((line[STARTTIME].strftime('%H:%M %d-%m-%y'),None,None,
                        style))

            # Downtime
            downTime = str(line[DOWNTIME].absvalues()[0]) + ' d, ' + \
                       line[DOWNTIME].strftime('%H') + ' h, ' + \
                       line[DOWNTIME].strftime('%M') + ' m'
            row.append((downTime,None,None,style))

            # History link
            row.append((None,
                        BASEPATH + 'history/?type=services&id=%s' \
                        % (line[SERVICEID],),
                        ('/images/status/status-history.png',
                        'View history for this service'),
                        None))

            self.rows.append([line[self.sortBy],row])

        self.rows.sort()
        if self.sortReverse:
            self.rows.reverse()

        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = str(servicesDown) + ' services down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = str(servicesShadow) + ' services in shadow'
        else:
            self.summary = str(servicesDown) + ' services down, ' + \
                           str(servicesShadow) + ' in shadow'

    def getFilters(controlBaseName,orgList):
        """
        Returns the filters that this section box accepts
        """
        filterHeadings = ['Organisation','Service','State']

        filterSelects = []
        table = nav.db.manage.Org()

        # Org
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        for org in table.getAllIterator(orderBy = 'orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Handler
        optionsList = [(FILTER_ALL_SELECTED,'All')]
        filterSelects.append((controlBaseName + '_' + 'handler',\
        [(FILTER_ALL_SELECTED,'All',True),('dns','dns',False),\
        ('imaps','imaps',False),('imap','imap',False),('http','http',False),
        ('pop3','pop3',False),('rpc','rpc',False),('smb','smb',False),
        ('ssh','ssh',False),('smtp','smtp',False)]))

        # State
        filterSelects.append((controlBaseName + '_' + 'state',\
        [(FILTER_ALL_SELECTED,'All',True),('n','Down',False),\
        ('s','Shadow',False)]))
        return (filterHeadings,filterSelects)
    getFilters = staticmethod(getFilters)


class NetboxSectionBox(SectionBox):
    " Section displaying services that are down or in shadow "

    # attribs for preferences
    name = 'Boxes down'
    typeId = 'netbox'

    prefsOptions = None

    defaultSort = 3
    sortReverse = False 
    sortBy = defaultSort

    def __init__(self, controlBaseName,getArgs,title,filterSettings):
        # Sort reverse by column 4 (downtime)

        self.headings = []
        self.headingDefs = [('Sysname',None),
                            ('IP',None),
                            ('Down since',None),
                            ('Downtime',None),
                            ('',None)]
        self.rows = []
        self.summary = None
        self.historyLink = [BASEPATH + 'history/?type=boxes','(history)']
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
        filterSettings = self.filterSettings
    
        sql = "SELECT netbox.sysname,netbox.ip," +\
              "alerthist.start_time,now()-alerthist.start_time," +\
              "netbox.up,alerttype.alerttype,netbox.netboxid FROM " + \
              "alerthist,netbox,alerttype " + \
              "WHERE alerthist.netboxid=netbox.netboxid AND " +\
              "alerttype.alerttypeid=alerthist.alerttypeid AND " +\
              "alerthist.end_time='infinity' AND " +\
              "alerthist.eventtypeid='boxState' AND " +\
              "(netbox.up='n' OR netbox.up='s') "
 
        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " and ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " or "
                    where_clause += "netbox.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # catid
            if not filterSettings['catid'].count(FILTER_ALL_SELECTED):
                where_clause += " and ("
                first_line = True
                for cat in filterSettings['catid']:
                    if not first_line:
                        where_clause += " or "
                    where_clause += "netbox.catid = '" + cat + "'"
                    first_line = False
                where_clause += ") "
            # state
            self.listStates = filterSettings['state']
            if not filterSettings['state'].count(FILTER_ALL_SELECTED):
                where_clause += " and ("
                first_line = True
                for state in filterSettings['state']:
                    if not first_line:
                        where_clause += " or "
                    if state=='n':
                        # Down
                        state = 'boxDown'
                    elif state=='s':
                        # Shadow
                        state = 'boxShadow'
                    where_clause += "alerttype.alerttype = '" + state + "'"
                    first_line = False
                where_clause += ") "
            else:
                where_clause += " AND (alerttype.alerttype='boxDown' or " +\
                                "alerttype.alerttype='boxShadow') "

        sql = sql + where_clause + " ORDER BY now()-start_time" 

        connection = nav.db.getConnection('status', 'manage')
        database = connection.cursor()
        database.execute(sql)
        result = database.fetchall()        
 
        height = len(result)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        boxesDown = 0
        boxesShadow = 0

        SYSNAME = 0
        IP = 1
        STARTTIME = 2
        DOWNTIME = 3
        UP = 4
        ALERTTYPE = 5
        BOXID = 6

        for line in result:
            row = []
            style = None    

            if line[ALERTTYPE] == 'boxShadow':
                boxesShadow += 1
                #style = 'shadow' 
            else:
                boxesDown += 1 

            # Sysname
            row.append((line[SYSNAME],
                        urlbuilder.createUrl(id=line[BOXID],division='netbox'),
                        None,
                        style))

            # Ip
            row.append((line[IP],None,None,style))
 
            # Down since
            row.append((line[STARTTIME].strftime('%H:%M %d-%m-%y'),
                        None,None,style))

            # Downtime
            downTime = str(line[DOWNTIME].absvalues()[0]) + ' d, ' + \
                       line[DOWNTIME].strftime('%H') + ' h, ' + \
                       line[DOWNTIME].strftime('%M') + ' m'

            row.append((downTime,None,None,style))

            # History icon
            row.append((None,
                        BASEPATH + 'history/?type=boxes&id=%s' % (line[BOXID],),
                        ('/images/status/status-history.png',
                        'View history for this box'),
                        None))

            self.rows.append([line[self.sortBy],row])

        self.rows.sort()
        if self.sortReverse:
            self.rows.reverse()

        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = str(boxesDown) + ' boxes down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = str(boxesShadow) + ' boxes in shadow'
        else:
            self.summary = str(boxesDown) + ' boxes down, ' + \
                           str(boxesShadow) + ' in shadow'

    def getFilters(controlBaseName,orgList):
        """
        Return the filters that this section accepts
        """

        filterHeadings = ['Organisation','Category','State']

        filterSelects = []

        # Org
        table = nav.db.manage.Org()
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for org in table.getAllIterator(orderBy='orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Cat
        table = nav.db.manage.Cat()
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
                            ('IP',None),
                            ('Module',None),
                            ('Down since',None),
                            ('Downtime',None),
                            ('',None)]
        self.rows = []
        self.summary = None
        self.historyLink = [BASEPATH + 'history/?type=modules','(history)']
        self.filterSettings = filterSettings

        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.addHeadings()
        return
 
    def fill(self):
        filterSettings = self.filterSettings
    
        sql = "SELECT netbox.sysname,netbox.ip," +\
              "module.module,alerthist.start_time," +\
              "now()-alerthist.start_time,netbox.up," +\
              "alerttype.alerttype,module.moduleid,netbox.netboxid FROM " + \
              "alerthist,netbox,alerttype,module " + \
              "WHERE alerthist.netboxid=netbox.netboxid AND " +\
              "alerthist.subid = module.moduleid AND " +\
              "alerttype.alerttypeid=alerthist.alerttypeid AND " +\
              "alerthist.end_time='infinity' AND " +\
              "alerthist.eventtypeid='moduleState' AND " +\
              "alerttype.alerttype='moduleDown' "
 
        where_clause = ''
        if filterSettings:
            # orgid
            if not filterSettings['orgid'].count(FILTER_ALL_SELECTED):
                where_clause += " and ("
                first_line = True
                for org in filterSettings['orgid']:
                    if not first_line:
                        where_clause += " or "
                    where_clause += "netbox.orgid = '" + org + "'"
                    first_line = False
                where_clause += ") "
            # catid
            if not filterSettings['catid'].count(FILTER_ALL_SELECTED):
                where_clause += " and ("
                first_line = True
                for cat in filterSettings['catid']:
                    if not first_line:
                        where_clause += " or "
                    where_clause += "netbox.catid = '" + cat + "'"
                    first_line = False
                where_clause += ") "
            # state
            self.listStates = filterSettings['state']
            if not filterSettings['state'].count(FILTER_ALL_SELECTED):
                where_clause += " and ("
                first_line = True
                for state in filterSettings['state']:
                    if not first_line:
                        where_clause += " or "
                    where_clause += "module.up = '" + state + "'"
                    first_line = False
                where_clause += ") "
            else:
              where_clause += "AND (module.up='n' OR module.up='s') "

        sql = sql + where_clause + " ORDER BY now()-start_time" 

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
                        urlbuilder.createUrl(id=line[BOXID],division='netbox'),
                        None,
                        style))

            # Ip
            row.append((line[IP],None,None,style))
 
            # Module
            row.append((str(line[MODULE]),None,None,style))

            # Down since
            row.append((line[STARTTIME].strftime('%H:%M %d-%m-%y'),
                        None,None,style))

            # Downtime
            downTime = str(line[DOWNTIME].absvalues()[0]) + ' d, ' + \
                       line[DOWNTIME].strftime('%H') + ' h, ' + \
                       line[DOWNTIME].strftime('%M') + ' m'

            row.append((downTime,None,None,style))

            # History icon
            row.append((None,
                        BASEPATH + 'history/?type=modules&id=%s' \
                        % (line[MODULEID],),
                        ('/images/status/status-history.png',
                        'View history for this module'),
                        None))

            self.rows.append([line[self.sortBy],row])

        self.rows.sort()
        if self.sortReverse:
            self.rows.reverse()

        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = str(modulesDown) + ' modules down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = str(modulesShadow) + ' modules in shadow'
        else:
            self.summary = str(modulesDown) + ' modules down, ' + \
                           str(modulesShadow) + ' modules in shadow'

    def getFilters(controlBaseName,orgList):
        """
        Return the filters that this section accepts
        """

        filterHeadings = ['Organisation','Category','State']

        filterSelects = []

        # Org
        table = nav.db.manage.Org()
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for org in table.getAllIterator(orderBy='orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Cat
        table = nav.db.manage.Cat()
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
                                ('IP',None),
                                ('From',None),
                                ('To',None),
                                ('Downtime',None),
                                ('boxState',None)]
                                
        else:
            self.headingDefs = [('Sysname',None),
                                ('IP',None),
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
                        urlbuilder.createUrl(id=line[BOXID],division='netbox'),
                        None,style))

            # IP
            row.append((line[IP],None,None,style))
 

            # From
            row.append((line[FROM].strftime('%H:%M %d-%m-%y'),
                       None,None,style))

            # To
            if not line[TO] or line[TO]==INFINITY:
                row.append(('Still down',None,None,style))
            else:
                row.append((line[TO].strftime('%H:%M %d-%m-%y'),
                           None,None,style))

            # Downtime
            downTime = str(line[DOWNTIME].absvalues()[0]) + ' d, ' + \
                           line[DOWNTIME].strftime('%H') + ' h, ' +\
                           line[DOWNTIME].strftime('%M') + ' min'
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

        self.rows.sort()
        if self.sortReverse:
            self.rows.reverse()
        return

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
              "alerthist.subid=service.serviceid AND " +\
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
                        urlbuilder.createUrl(id=line[BOXID],division='netbox'),
                        None,style))

            # Handler
            row.append((line[HANDLER],None,None,style))
 

            # From
            row.append((line[FROM].strftime('%H:%M %d-%m-%y'),
                       None,None,style))

            # To
            if not line[TO] or line[TO]==INFINITY:
                row.append(('Still down',None,None,style))
            else:
                row.append((line[TO].strftime('%H:%M %d-%m-%y'),
                           None,None,style))

            # Downtime
            downTime = str(line[DOWNTIME].absvalues()[0]) + ' d, ' + \
                           line[DOWNTIME].strftime('%H') + ' h, ' +\
                           line[DOWNTIME].strftime('%M') + ' min'
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

        self.rows.sort()
        if self.sortReverse:
            self.rows.reverse()
        return


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

        sql = "SELECT netbox.sysname,module.module," +\
              "alerthist.start_time,alerthist.end_time,netbox.netboxid,"+\
              "alerttype.alerttype,module.moduleid FROM netbox,"+\
              "module,alerthist LEFT JOIN alerttype using(alerttypeid) "+\
              "WHERE alerthist.netboxid = netbox.netboxid AND "+\
              "alerthist.subid=module.moduleid AND " +\
              "alerthist.eventtypeid='moduleState' AND " +\
              "date(start_time) = '%s' " %(self.date,)
            
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
                        urlbuilder.createUrl(id=line[BOXID],division='netbox'),
                        None,style))

            # Handler
            row.append((str(line[MODULE]),None,None,style))
 

            # From
            row.append((line[FROM].strftime('%H:%M %d-%m-%y'),
                       None,None,style))

            # To
            if not line[TO] or line[TO]==INFINITY:
                row.append(('Still down',None,None,style))
            else:
                row.append((line[TO].strftime('%H:%M %d-%m-%y'),
                           None,None,style))

            # Downtime
            downTime = str(line[DOWNTIME].absvalues()[0]) + ' d, ' + \
                           line[DOWNTIME].strftime('%H') + ' h, ' +\
                           line[DOWNTIME].strftime('%M') + ' min'
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

        self.rows.sort()
        if self.sortReverse:
            self.rows.reverse()
        return
