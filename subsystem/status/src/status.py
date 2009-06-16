# -*- coding: ISO8859-1 -*-
# $Id$
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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#
"""
Contains the handler for the status pages
(status, history and status preferences)
"""

#################################################
## Imports

import datetime
import re,nav.db.manage

from mod_python import util,apache
from nav.web.templates.StatusTemplate import StatusTemplate

from StatusPrefs import *
from StatusSections import *

#################################################
## Constants

FILTER_ALL_SELECTED = 'all_selected_tkn'
HISTORY_DEFAULT_NO_DAYS = 7
HISTORY_TYPE_BOXES = 'boxes'
HISTORY_TYPE_SERVICES = 'services'
HISTORY_TYPE_MODULES = 'modules'
HISTORY_TYPE_THRESHOLD = 'thresholds'
BASEPATH = '/status/'
INFINITY = datetime.datetime.max

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
        req.content_type = "text/html"
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
    template.path = [('Home','/'),('Status',None)]
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
                self.sections.append(NetboxSectionBox(controlBaseName, args,
                    title, filters))
            elif typeId == 'netboxmaint':
                self.sections.append(NetboxMaintenanceSectionBox(
                    controlBaseName, args, title, filters))
            elif typeId == 'service':
                self.sections.append(ServiceSectionBox(controlBaseName, args,
                    title, filters))
            elif typeId == 'servicemaint':
                self.sections.append(ServiceMaintenanceSectionBox(
                    controlBaseName, args, title, filters))
            elif typeId == 'module':
                self.sections.append(ModuleSectionBox(controlBaseName, args,
                    title, filters))
            elif typeId == 'threshold':
                self.sections.append(ThresholdSectionBox(controlBaseName, args,
                    title, filters))

        # check http get arguments and sort the lists
        for section in self.sections:
            sortArg = args.getArgs(section.sortId)
            if not sortArg:
                section.sortBy = section.defaultSort
            elif sortArg:
                sortReverse = False
                sortBy = int(sortArg[0])
                if sortBy < 0:
                    sortBy = abs(sortBy)
                    sortReverse = True
                section.sortBy = sortBy-1
                section.sortReverse = sortReverse

        for section in self.sections:
            section.fill()

class HistoryPage:
    " Class representing the history page "

    selid = None

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
            # Default is boxes
            seltype = HISTORY_TYPE_BOXES

        # Get the selected id from form data
        if req.form.has_key(CNAME_ID):
            selid = req.form[CNAME_ID]
        else:
            selid = None

        # Looking at history for one box
        if selid and seltype==HISTORY_TYPE_BOXES:
            sysname = nav.db.manage.Netbox(selid).sysname
            self.title = 'History for %s' % (sysname,)
        elif selid and seltype==HISTORY_TYPE_SERVICES:
            service = nav.db.manage.Service(selid)
            handler = service.handler
            sysname = service.netbox.sysname
            self.title = "History for '%s' on %s" % (handler,sysname) 
        elif selid and seltype==HISTORY_TYPE_MODULES:
            module = nav.db.manage.Module(selid)
            moduleno = str(module.module)
            sysname = module.netbox.sysname
            self.title = "History for module '%s' on %s" % (moduleno,sysname) 
        elif selid and seltype==HISTORY_TYPE_THRESHOLD:
            datasource = nav.db.manage.Rrd_datasource(selid)
            sql = "SELECT sysname FROM rrddatasourcenetbox WHERE " +\
                  "rrd_datasourceid='%s'" % (selid,)
            connection = nav.db.getConnection('status', 'manage')
            database = connection.cursor()
            database.execute(sql)
            result = database.fetchone()
            sysname = ''
            if result:
                sysname = result[0]
                                
            descr = datasource.descr
            self.title = "History for datasource '%s' on '%s'" % \
                         (descr,sysname) 

        # Data for the selection bar
        self.action = BASEPATH + 'history/'
        self.method = 'GET'
        self.onChange = 'this.form.submit()'
        self.seltype = seltype

        self.typeText = 'Show history for'
        self.typeValue = seltype
        self.typeOptions = [(HISTORY_TYPE_BOXES,'boxes'),
                            (HISTORY_TYPE_SERVICES,'services'),
                            (HISTORY_TYPE_MODULES,'modules'),
                            (HISTORY_TYPE_THRESHOLD,'thresholds')]
        self.typeCname = CNAME_TYPE

        self.idCname = CNAME_ID
        self.selid = selid
        self.daysText = ' the last '
        self.daysValue = str(days)
        self.daysCname = CNAME_DAYS
        self.daysOptions = [('1','day')]
        for i in range(2,31):
            self.daysOptions.append((str(i),str(i) + ' days'))

        # Add one section per day
        counter = 1
        now = datetime.datetime.now()
        for i in range(0,days):
            date = now.strftime('%Y-%m-%d')
            control = str(counter)
            if seltype == HISTORY_TYPE_BOXES:
                self.sections.append(NetboxHistoryBox(control,args,date,date,
                selid))
            elif seltype == HISTORY_TYPE_SERVICES:
                self.sections.append(ServiceHistoryBox(control,
                args,date,date,selid))
            elif seltype == HISTORY_TYPE_MODULES:
                self.sections.append(ModuleHistoryBox(control,
                args,date,date,selid)) 
            elif seltype == HISTORY_TYPE_THRESHOLD:
                self.sections.append(ThresholdHistoryBox(control,
                args,date,date,selid))
              
            counter += 1
            now = now - datetime.timedelta(days=1)

        # check http get arguments and sort the lists
        for section in self.sections:
            sortArg = args.getArgs(section.sortId)
            if not sortArg:
                section.sortBy = section.defaultSort
            elif sortArg:
                sortReverse = False
                sortBy = int(sortArg[0])
                if sortBy < 0:
                    sortBy = abs(sortBy)
                    sortReverse = True
                section.sortBy = sortBy-1
                section.sortReverse = sortReverse

        for section in self.sections:
            section.fill()

        # Remove empty sections (days)
        keep = []
        for section in self.sections:
            if len(section.rows):
                keep.append(section)
        self.sections = keep

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
