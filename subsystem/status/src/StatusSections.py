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

import StatusTables,mx.DateTime
from nav.web import urlbuilder

#################################################
## Constants

FILTER_ALL_SELECTED = 'all_selected_tkn'
BASEPATH = '/status/'

#################################################
## Classes

class SectionBox:
    " A general section on the status or history page "

    controlBaseName = None
    title = None
    maxHeight = None

    # list of columns (left to right)
    columns = []
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
        self.columns = []
        self.title = title
        return

    def addColumn(self,heading,table,field,orderBy,whereClause=None,show=True):
        self.columns.append(SectionColumn(heading,table,field,orderBy,\
        whereClause,show))
        return

    def sort(self, columnNumber):
        columnNumber -= 1

        permutation = self.columns[columnNumber].sort()

        for column in self.columns:
            if column.sortState == SectionColumn.SORTED_BY_OTHER:
                column.sortBy(permutation)

        # refill
        self.fill()
        return 

    def sortReverse(self, columnNumber):

        columnNumber -= 1

        permutation = self.columns[columnNumber].sortReverse()

        for column in self.columns:
            if column.sortState == SectionColumn.SORTED_BY_OTHER:
                column.sortBy(permutation)

        # refill
        self.fill()
        return


    def fill(self):
        " Fill columns with data from database "
        for column in self.columns:
            column.fill()  
        return

    def addHeadings(self):
        i = 1
        for column in self.columns:
            if column.show:
                colNumber = i
                if (self.getArgs.getArgs(self.sortId)):
                    if int(self.getArgs.getArgs(self.sortId)[0]) == colNumber:
                        # we're already sorting by this row, reverse the sort
                        # next time
                        colNumber = -i
                
                args = self.getArgs.addArg(self.sortId,repr(colNumber))
                url = '%s?%s#%s' % (self.urlRoot,args,self.controlBaseName)
                style = ''
                id = ''
                if column.sortState == SectionColumn.SORTED_BY_THIS:
                    style = 'sortedBy'
                    id = 'ascending'
                elif column.sortState == SectionColumn.SORTED_BY_THIS_REVERSE:
                    style = 'sortedBy'
                    id = 'descending'
                self.headings.append((column.heading,url,style,id))
            i += 1


class SectionColumn:
    " A column in a SectionBox "

    # constants
    SORT_BY_THIS = 0 
    SORTED_BY_THIS = 1
    SORTED_BY_OTHER = 2
    SORTED_BY_THIS_REVERSE = 3

    sortState = None

    heading = None
    table = None
    field = []
    whereClause = None
    show = True

    orderBy = ''
    rows = []

    def __init__(self,heading,table,field,orderBy,whereClause,show):
        self.rows = []

        self.orderBy = orderBy
        self.show = show
        self.sortState = self.SORTED_BY_OTHER
        self.heading = heading
        self.table = table
        self.field = field
        self.whereClause = whereClause
        return

    def fill(self):
        " Fill this column with rows from database "
        table = getattr(StatusTables,self.table)

        fields = self.field

        if self.whereClause:
            iterator = table.getAllIterator((self.whereClause),\
            orderBy=self.orderBy)
        else:
            iterator = table.getAllIterator(orderBy=self.orderBy)

        counter = 0

        for row in iterator:
            for field in fields:
                object = getattr(row, field)
                row = object

            self.rows.append((row,counter))
            counter += 1
        return

    def sort(self):
        " Sort section by this column "
        self.sortState = self.SORTED_BY_THIS

        self.rows.sort()

        permutation = []

        for row in self.rows:
            data,counter = row
            permutation.append(counter)
            
        return permutation

    def sortReverse(self):
        " Sort section by this column, descending "
        self.sortState = self.SORTED_BY_THIS_REVERSE

        self.rows.sort()
        self.rows.reverse()

        permutation = []

        for row in self.rows:
            data,counter = row
            permutation.append(counter)
            
        return permutation

    def sortBy(self,permutation):
        " Sort this column by another column "
        self.sortState = self.SORTED_BY_OTHER

        # Make an empty list of the same length
        sortedList = []

        counter = 0
        for index in permutation:
            data,counterOld = self.rows[index]
            sortedList.append((data,counter))
            counter += 1

        self.rows = sortedList
        return


#################################################
## Sections that inherits from SectionBox
        
class ServiceSectionBox(SectionBox):
    " Section displaying services that are down or in shadow "

    # attribs for preferences
    description = 'Section for services'
    name = 'Services down'
    typeId = 'service'

    prefsOptions = None

    headings = []
    rows = []

    def __init__(self, controlBaseName,getArgs,title,filterSettings):
        # Sort reverse by column 3 (down time)
        self.defaultSort = [-3]

        self.headings = []
        self.rows = []
        self.summary = None
        self.historyLink = [BASEPATH + 'history/?type=services','(history)']
        self.columns = []
        self.table = None

        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.initColumns(filterSettings)
        self.fill()
        return
 
    def initColumns(self,filterSettings):
        where_clause = "eventtypeid = 'serviceState' and end_time = 'infinity'"
  
        # parse filter settings
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
            if not filterSettings['handler'].count(FILTER_ALL_SELECTED):
                where_clause += " and ("
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
  
        orderBy = 'start_time' 
        self.addColumn('Sysname','AlerthistStatusService',\
        ['sysname'],orderBy,where_clause)
        self.addColumn('Service','AlerthistStatusService',\
        ['handler'],orderBy,where_clause)
        self.addColumn('Down since','AlerthistStatusService',\
        ['start_time'],orderBy,where_clause)
        self.addColumn('Downtime','AlerthistStatusService',\
        ['start_time'],orderBy,where_clause)
        self.addColumn('Up','AlerthistStatusService',\
        ['up'],orderBy,where_clause,show=False)

        for column in self.columns:
            column.fill() 
        return

    def fill(self):
        self.rows = []
        self.headings = []

        self.addHeadings()

        height = len(self.columns[0].rows)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight


        servicesDown = 0
        servicesShadow = 0
 
        for i in range(0,height):
            row = []

            # håndtere hver kolonne manuelt            
            up,counter = self.columns[4].rows[i]
            style = None
            if up == 'n':
                servicesDown += 1
                style = None
            elif up == 's':
                servicesShadow += 1
                style = 'shadow'

            # Sysname 
            data,counter = self.columns[0].rows[i]
            netbox = StatusTables.Netbox
            boxid = netbox.getAllIDs(("sysname='%s'" % data))[0]
            row.append((data,urlbuilder.createUrl(id=boxid,division='netbox'),
                                                  style))
            # Handler
            data,counter = self.columns[1].rows[i]
            row.append((data,urlbuilder.createUrl(id=data,
                                                  division='service'),None))
 
            # Down since
            start,counter = self.columns[2].rows[i]
            row.append((start.strftime('%H:%M %d-%m-%y'),'',None))

            # Downtime
            start,counter = self.columns[3].rows[i]
            diff = mx.DateTime.now() - start
            delta = repr(diff.absvalues()[0]) + ' d, ' + \
            diff.strftime('%H') + ' h, ' + diff.strftime('%M') + ' m'
            row.append((delta,'',None))

            self.rows.append(row)
        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = str(servicesDown) + ' services down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = str(servicesShadow) + ' services in shadow'
        else:
            self.summary = str(servicesDown) + ' services down, ' + \
                           str(servicesShadow) + ' in shadow'
        return

    def getFilters(controlBaseName,orgList):
        """
        Returns the filters that this section box accepts
        """
        filterHeadings = ['Organisation','Service','State']

        filterSelects = []
        table = StatusTables.Org()

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
    " Section displaying netboxes that are down or in shadow "
    
    # attribs for preferences
    name = 'Boxes down'
    typeId = 'netbox'     
    
    def __init__(self,controlBaseName,getArgs,title,filterSettings):
        # Sort reverse by column 3 (down time)
        self.defaultSort = [-3]

        self.headings = []
        self.rows = []
        self.columns = []
        self.summary = None
        self.historyLink = [BASEPATH + 'history/?type=boxes','(history)']

        SectionBox.__init__(self,controlBaseName,title,getArgs,None) 
        self.initColumns(filterSettings)
        self.fill()
        return
 
    def initColumns(self,filterSettings):
        # basic where
        where_clause = "eventtypeid = 'boxState' " +\
                       "and end_time = 'infinity'"

        # parse filter settings
        ##raise(repr(filterSettings))
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
                    where_clause += "netbox.up = '" + state + "'"
                    first_line = False
                where_clause += ") "

        self.addColumn('Sysname','AlerthistStatusNetbox',['sysname'],\
        'start_time',where_clause)
        self.addColumn('IP','AlerthistStatusNetbox',['ip'],\
        'start_time',where_clause)
        self.addColumn('Down since','AlerthistStatusNetbox',['start_time'],\
        'start_time',where_clause,show=True)
        self.addColumn('Downtime','AlerthistStatusNetbox',['start_time'],\
        'start_time',where_clause,show=True)
        self.addColumn('Shadow','AlerthistStatusNetbox',['up'],\
        'start_time',where_clause,show=False)
        self.addColumn('','AlerthistStatusNetbox',['up'],\
        'start_time',where_clause,show=True)

        for column in self.columns:
            column.fill() 
        return

    def fill(self):
        self.rows = []
        self.headings = []

        self.addHeadings()

        height = len(self.columns[0].rows)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        boxesDown = 0
        boxesShadow = 0
        for i in range(0,height):
            row = []

            # håndtere hver kolonne manuelt            
            up,counter = self.columns[5].rows[i]

            style = None
            if up == 'n':
                style = None 
                boxesDown += 1
            elif up == 's':
                style = 'shadow'
                boxesShadow += 1

            # Sysname 
            data,counter = self.columns[0].rows[i]
            netbox = StatusTables.Netbox
            boxid = netbox.getAllIDs(("sysname='%s'" % data))[0]
            row.append((data,urlbuilder.createUrl(id=boxid,division='netbox'),
                                                  style))
            # IP
            data,counter = self.columns[1].rows[i]
            row.append((data,None,style))
 
            # Down since
            start,counter = self.columns[2].rows[i]
            row.append((start.strftime('%H:%M %d-%m-%y'),'',None))

            # Downtime
            start,counter = self.columns[3].rows[i]
            diff = mx.DateTime.now() - start
            delta = repr(diff.absvalues()[0]) + ' d, ' + \
            diff.strftime('%H') + ' h, ' + diff.strftime('%M') + ' m'
            row.append((delta,'',None))

            # History
            row.append(('<img border="0" src="/~hansjorg/icon.png">',
                        BASEPATH + 'history/?type=boxes&id=%s' % (boxid,),
                        None))
            self.rows.append(row)

        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = str(boxesDown) + ' boxes down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = str(boxesShadow) + ' boxes in shadow'
        else:
            self.summary = str(boxesDown) + ' boxes down, ' + \
                           str(boxesShadow) + ' in shadow'
        return

    def getFilters(controlBaseName,orgList):
        """
        Return the filters that this section accepts
        """

        filterHeadings = ['Organisation','Category','State']

        filterSelects = []

        # Org
        table = StatusTables.Org()
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for org in table.getAllIterator(orderBy='orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Cat
        table = StatusTables.Cat()
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
    
    def __init__(self,controlBaseName,getArgs,title,filterSettings):
        # Sort reverse by column (down time)
        self.defaultSort = [-3]

        self.headings = []
        self.rows = []
        self.columns = []
        self.historyLink = [BASEPATH + 'history/?type=modules','(history)']
        self.summary = None

        SectionBox.__init__(self,controlBaseName,title,getArgs,None) 
        self.initColumns(filterSettings)
        self.fill()
        return
 
    def initColumns(self,filterSettings):
        # basic where
        where_clause = "eventtypeid = 'moduleState' " +\
                       "and end_time = 'infinity'"

        # parse filter settings
        ##raise(repr(filterSettings))
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
                    where_clause += "netbox.up = '" + state + "'"
                    first_line = False
                where_clause += ") "

        self.addColumn('Sysname','AlerthistStatusNetbox',['sysname'],\
        'start_time',where_clause)
        self.addColumn('IP','AlerthistStatusNetbox',['ip'],\
        'start_time',where_clause)
        self.addColumn('Module','AlerthistStatusNetbox',['subid'],\
        'start_time',where_clause)
        self.addColumn('Down since','AlerthistStatusNetbox',['start_time'],\
        'start_time',where_clause,show=True)
        self.addColumn('Downtime','AlerthistStatusNetbox',['start_time'],\
        'start_time',where_clause,show=True)
        self.addColumn('Shadow','AlerthistStatusNetbox',['up'],\
        'start_time',where_clause,show=False)
        self.addColumn('','AlerthistStatusNetbox',['up'],\
        'start_time',where_clause,show=True)

        for column in self.columns:
            column.fill() 
        return

    def fill(self):
        self.rows = []
        self.headings = []

        self.addHeadings()

        height = len(self.columns[0].rows)
        if self.maxHeight:
            if height > self.maxHeight:
                height = self.maxHeight

        modulesDown = 0
        modulesShadow = 0
        for i in range(0,height):
            row = []

            # håndtere hver kolonne manuelt            
            up,counter = self.columns[5].rows[i]
            style = None
            if up == 'n':
                modulesDown += 1
                style = None
            elif up == 's':
                modulesShadow += 1
                style = 'shadow'

            # Sysname 
            data,counter = self.columns[0].rows[i]
            netbox = StatusTables.Netbox
            boxid = netbox.getAllIDs(("sysname='%s'" % data))[0]
            row.append((data,urlbuilder.createUrl(id=boxid,division='netbox'),
                                                  style)) 
            # IP
            data,counter = self.columns[1].rows[i]
            row.append((data,None,style)) 

            # Module
            data,counter = self.columns[2].rows[i]
            module = StatusTables.Module(data)
            row.append((Module.module,'/',''))
 
            # Down since
            start,counter = self.columns[3].rows[i]
            row.append((start.strftime('%H:%M %d-%m-%y'),'',None))

            # Downtime
            start,counter = self.columns[4].rows[i]
            diff = mx.DateTime.now() - start
            delta = repr(diff.absvalues()[0]) + ' d, ' + \
            diff.strftime('%H') + ' h, ' + diff.strftime('%M') + ' m'
            row.append((delta,'',None))

            # History
            row.append(('<img border="0" src="/~hansjorg/icon.png">',
                        BASEPATH + 'history/?type=boxes&id=%s' % (boxid,),
                        None))

            self.rows.append(row)
        if not self.listStates.count('s') and self.listStates.count('n'):
            self.summary = str(modulesDown) + ' modules down'
        elif not self.listStates.count('n') and self.listStates.count('s'):
            self.summary = str(modulesShadow) + ' modules in shadow'
        else:
            self.summary = str(modulesDown) + ' modules down, ' + \
                           str(modulesShadow) + ' in shadow'
        return

    def getFilters(controlBaseName,orgList):
        """
        Return the filters that this section accepts
        """

        filterHeadings = ['Organisation','Category','State']

        filterSelects = []

        # Org
        table = StatusTables.Org()
        # Restrict to orgs where user belongs
        #whereOrg = makeWhereList(orgList)
        optionsList = [(FILTER_ALL_SELECTED,'All',True)]
        for org in table.getAllIterator(orderBy='orgid'):
            optionsList.append((org.orgid,org.orgid,False))
        filterSelects.append((controlBaseName + '_' + 'orgid',optionsList))

        # Cat
        table = StatusTables.Cat()
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


