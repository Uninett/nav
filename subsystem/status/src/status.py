"""
$Id$

This file id part of the NAV project.

Contains the handler for the status pages
(status, history and status preferences)

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
"""

#################################################
## Imports


import StatusTables,mx.DateTime,re

from mod_python import util,apache
from nav.web.templates.StatusTemplate import StatusTemplate

from nav.web import urlbuilder

from StatusPrefs import *
from StatusSections import *

#################################################
## Constants

FILTER_ALL_SELECTED = 'all_selected_tkn'
DEFAULT_PREFS_FILENAME = 'tmp/default-prefs.pickle'
HISTORY_DEFAULT_NO_DAYS = 7
HISTORY_TYPE_BOXES = 'boxes'
HISTORY_TYPE_SERVICES = 'services'
BASEPATH = '/status/'
INFINITY = mx.DateTime.DateTime(999999,12,31,0,0,0)

#################################################
## Default handler

def handler(req):
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)

    path = req.uri.split('status/')[1]
    path = path.split('/')

    if path[0] == 'prefs':
        output = indexPrefs(req)
    elif path[0] == 'history':
        output = indexHistory(req)
    else:
        output = indexInternal(req)
    
    if output:
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND

def indexHistory(req):
    " Shows the history page "
    historyPage = HistoryPage(req) 

    nameSpace = {'status': None, 'prefs': None, 'history': historyPage}
    template = StatusTemplate(searchList=[nameSpace])
    template.path = [('Home','/'),
                     ('Tools','/toolbox'),
                     ('Status',BASEPATH),
                     ('History',None)]
    return template.respond()


def indexPrefs(req):
    " Shows the preferences page "

    prefsPage = HandleStatusPrefs(req)
 
    nameSpace = {'status': None, 'prefs': prefsPage, 'history': None}
    template = StatusTemplate(searchList=[nameSpace])
    template.path = [('Home','/'),
                     ('Preferences','/preferences'),
                     ('Status page preferences',None)]
    return template.respond()

       
def indexInternal(req):
    " Shows the internal status page, based upon the users prefs "
    prefs = HandleStatusPrefs.loadPrefs(req)
    statusPage = StatusPage(req,prefs)

    nameSpace = {'status': statusPage, 'prefs': None, 'history': None}
    template = StatusTemplate(searchList=[nameSpace])
    template.path = [('Home','/'),('Tools','/toolbox'),('Status',None)]
    return template.respond()

#################################################
## Page handler classes

class StatusPage:
    """ This is the main Status Page"""

    sections = []

    """ main status page """
    def __init__(self,req,prefs):
        form = req.form
        args = ManageGetArgs(form)
        self.sections = []
        self.title = 'Status'

        for section in prefs.sections:
            controlBaseName, typeId, title, filters = section

            if typeId == 'netbox':
                self.sections.append(NetboxSectionBox(controlBaseName,args,\
                title,filters))
            elif typeId == 'service':
                self.sections.append(ServiceSectionBox(controlBaseName,args,\
                title,filters))
            elif typeId == 'module':
                self.sections.append(ModuleSectionBox(controlBaseName,args,\
                title,filters))

        # check http get arguments and sort the lists
        for section in self.sections:
            sortArg = args.getArgs(section.sortId)
            if not sortArg:
                sortArg = section.defaultSort
            if sortArg:
                colNumber = int(sortArg[0])
                if colNumber > 0:
                    section.sort(colNumber)
                else:
                    colNumber = colNumber * (-1)
                    section.sortReverse(colNumber)

class HistoryPage:
    " Class representing the history page "

    def __init__(self,req):
        CNAME_DAYS = 'days'
        CNAME_TYPE = 'type'
        CNAME_ID = 'id'

        self.title = 'Status history'
        args = ManageGetArgs(req.form)
        self.sections = []

        # Get numbre of days from form data
        if req.form.has_key(CNAME_DAYS):
            days = int(req.form[CNAME_DAYS])
        else:
            days = HISTORY_DEFAULT_NO_DAYS

        # Get the selected type from form data
        if req.form.has_key(CNAME_TYPE):
            seltype = req.form[CNAME_TYPE]
        else:
            seltype = HISTORY_TYPE_BOXES

        # Looking at history for one box?
        if req.form.has_key(CNAME_ID):
            boxid = req.form[CNAME_ID]
            sysname = StatusTables.Netbox(boxid).sysname
            self.title = 'History for %s' % (sysname,)
        else:
            boxid = None

        # Data for the selection bar
        self.action = BASEPATH + 'history/'
        self.method = 'GET'
        self.onChange = 'this.form.submit()'

        self.boxValue = boxid
        self.boxCname = CNAME_ID

        self.typeText = 'Show history for'
        self.typeValue = seltype
        self.typeOptions = [(HISTORY_TYPE_BOXES,'boxes'),(HISTORY_TYPE_SERVICES,'services')]
        self.typeCname = CNAME_TYPE

        self.daysText = ' the last '
        self.daysValue = str(days)
        self.daysCname = CNAME_DAYS
        self.daysOptions = [('1','1 day')]
        for i in range(2,31):
            self.daysOptions.append((str(i),str(i) + ' days'))

        # Add one section per day
        counter = 1
        now = mx.DateTime.now()
        for i in range(0,days):
            date = now.strftime('%Y-%m-%d')
            control = str(counter)
            if seltype == HISTORY_TYPE_BOXES:
                self.sections.append(NetboxHistoryBox(control,args,date,date,boxid))
            elif seltype == HISTORY_TYPE_SERVICES:
                self.sections.append(ServiceHistoryBox(control,args,date,date))
              
            counter += 1
            now = now - mx.DateTime.oneDay

        # Remove empty sections
        keep = []
        for section in self.sections:
            if len(section.columns[0].rows):
                keep.append(section)
        self.sections = keep

        # check http get arguments and sort the lists
        for section in self.sections:
            sortArg = args.getArgs(section.sortId)
            if sortArg:
                colNumber = int(sortArg[0])
                if colNumber > 0:
                    section.sort(colNumber)
                else:
                    section.sortReverse(colNumber*-1)


#################################################
## Section Subclasses

class NetboxHistoryBox(SectionBox):
    " Section showing the history of netboxes that have been down or in shadow "
    
    def __init__(self,controlBaseName,getArgs,title,date,boxid=None):
        self.headings = []
        self.rows = []
        self.columns = []

        SectionBox.__init__(self,controlBaseName,title,getArgs,None) 
        self.initColumns(date,boxid)
        self.fill()
        return
 
    def initColumns(self,date,boxid):
        where_clause = "eventtypeid = 'boxState' " +\
                       "and date(start_time) = '%s' " % (date,)
                       #"and end_time != 'infinity' "

        if boxid:
            where_clause += " and netboxid = '%s'" % (boxid,)
 
        orderBy = 'start_time'
        entries = StatusTables.AlerthistStatusNetbox.getAll(where_clause,
                                                            orderBy=orderBy)
        counter = 1
        sysnames = []
        ips = []
        froms = []
        tos = []
        downtimes = []
        shadows = []
        ups2 = []
        for row in entries:
            sysnames.append((row.sysname,counter))
            ips.append((row.ip,counter))
            froms.append((row.start_time,counter))
            tos.append((row.end_time,counter))
            downtimes.append((row.start_time,counter))
            shadows.append((row.up,counter))
            ups2.append((row.up,counter))
            counter += 1

        self.addColumnPrefilled('Sysname',sysnames)
        self.addColumnPrefilled('Ip',ips)
        self.addColumnPrefilled('From',froms)
        self.addColumnPrefilled('To',tos)
        self.addColumnPrefilled('Downtime',downtimes)
        self.addColumnPrefilled('Shadow',shadows,show=False)
         
        if not boxid:
            self.addColumnPrefilled('',ups2)

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

        for i in range(0,height):
            row = []

            # håndtere hver kolonne manuelt            
            up,counter = self.columns[4].rows[i]

            # Sysname 
            data,counter = self.columns[0].rows[i]
            style = None
            if up == 'n':
                style = None
            elif up == 's':
                style = 'shadow'

            netbox = StatusTables.Netbox
            boxid = netbox.getAllIDs(("sysname='%s'" % data))[0]
            row.append((data,urlbuilder.createUrl(id=boxid,division='netbox'),
                                                  style))
 
            # IP
            ip,counter = self.columns[1].rows[i]
            row.append((ip,'',None))

            # From
            start,counter = self.columns[2].rows[i]
            row.append((start.strftime('%H:%M %d-%m-%y'),'',None))

            # To
            end,counter = self.columns[3].rows[i]
            if not end or end == INFINITY:
                row.append(('Still down','',None))
            else:
                row.append((end.strftime('%H:%M %d-%m-%y'),'',None))

            # Downtime
            if not end or end == INFINITY:
                diff = mx.DateTime.now() - start
            else:
                diff = end - start
            delta = repr(diff.absvalues()[0]) + ' d, ' + \
            diff.strftime('%H') + ' h, ' + diff.strftime('%M') + ' min'
            row.append((delta,'',None))

            # History
            if len(self.columns) == 6:
                row.append(('<img border="0" src="/~hansjorg/icon.png">',
                            BASEPATH + 'history/?type=boxes&id=%s' % (boxid,),
                            None))
            
            self.rows.append(row)
        return

class ServiceHistoryBox(SectionBox):
    " Section showing history for services "

    def __init__(self, controlBaseName,getArgs,title,date):
        self.headings = []
        self.rows = []

        self.columns = []
        self.table = None
        SectionBox.__init__(self, controlBaseName,title,getArgs,None) 
        self.initColumns(date)
        self.fill()
        return
 
    def initColumns(self,date):
        where_clause = "eventtypeid = 'serviceState' and " +\
                       "date(start_time) = '%s' and end_time " % (date,) +\
                       "!= 'infinity'" 
  
        orderBy = 'start_time' 
        self.addColumn('Sysname','AlerthistStatusService',\
        ['sysname'],orderBy,where_clause)
        self.addColumn('Service','AlerthistStatusService',\
        ['handler'],orderBy,where_clause)
        self.addColumn('From','AlerthistStatusService',\
        ['start_time'],orderBy,where_clause)
        self.addColumn('To','AlerthistStatusService',\
        ['end_time'],orderBy,where_clause)
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

        for i in range(0,height):
            row = []

            # håndtere hver kolonne manuelt            
            up,counter = self.columns[5].rows[i]
            # Sysname 
            data,counter = self.columns[0].rows[i]
            style = ''
            if up == 'n':
                style = 'down'
            elif up == 's':
                style = 'shadow'

            netbox = StatusTables.Netbox
            boxid = netbox.getAllIDs(("sysname='%s'" % data))[0]
            row.append((data,urlbuilder.createUrl(id=boxid,division='netbox'),
                                                  style))
            # Handler
            data,counter = self.columns[1].rows[i]
            row.append((data,urlbuilder.createUrl(id=data,
                                                  division='service'),None))
 
            # From
            start,counter = self.columns[2].rows[i]
            row.append((start.strftime('%H:%M %d-%m-%y'),'',None))

            # To
            end,counter = self.columns[3].rows[i]
            row.append((end.strftime('%H:%M %d-%m-%y'),'',None))

            # Downtime
            diff = end - start
            delta = repr(diff.absvalues()[0]) + ' d, ' + \
            diff.strftime('%H') + ' h, ' + diff.strftime('%M') + ' m'
            row.append((delta,'',None))

            self.rows.append(row)
        return


#################################################
## Other stuff

class ManageGetArgs:
    """ 
    Get,set and "remember" HTTP GET arguments 
    """
    inputArgs = None

    # The char which seperates different values. Ex: sort=value1,value2,..
    valueSeperator = ','

    def __init__(self, inputArgs):
        # inputArgs is an instance of the mod_python.util.FieldStorage class
        inputDict = dict([(field.name, field.value) for \
        field in inputArgs.list]) 
        self.inputArgs = inputDict

    def getArgs(self,argName):
        # returns a list of argument values for the argument argName
        if self.inputArgs.has_key(argName):
            argValues = []
            for value in self.inputArgs[argName].split(self.valueSeperator):
                argValues.append(value)
            return argValues
        else:
            return None

    def addArg(self,newKey,newValue):
        result = ''

        keyAdded = False
        for key,value in self.inputArgs.items():
            if newKey == key:
                key = newKey
                value = newValue
                keyAdded = True
            result += key + '=' + value + '&'

        if not keyAdded:
            result += newKey + '=' + newValue
        
        # remove last char if it's a '&'
        if result[len(result)-1] == '&':
            result = result[0:len(result)-1]

        return result

    def getLastArgs(self):
        result = ''
        fieldList = self.inputArgs.list
        for field in fieldList:
            result += field.name + '=' + field.value
    
        return result
