# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Contains classes for the status preferences page
"""

#################################################
## Imports

import cPickle
import re
import copy
import logging

import nav.db
from nav.models.profiles import Account
from StatusSections import *

logger = logging.getLogger('nav.web.status.StatusPrefs')

#################################################
## Constants

BASEPATH = '/status/'
ADMIN_USER_ID = '1'

#################################################
## Classes

class HandleStatusPrefs:
    """ 
    This class displays the prefs page and handles 
    loading and saving of preferences 
    """

    STATUS_PROPERTY = 'statusprefs'

    sectionBoxTypes = []
    editSectionBoxes = []

    addBarTitle = None
    addBarSelectOptions = []
    addBarSelectName = None
    addBarSubmitName = None
    addBarSubmitTitle = None
    addBarSaveName = None
    addBarSaveTitle = None

    actionBarUpName = None
    actionBarDelName = None
    radioButtonName = None
    formAction = BASEPATH + 'prefs/status.py'

    isAdmin = False
    adminHeader = 'Save default prefs (admin only)'
    adminHelp = 'Save this layout as a default for users without any ' + \
                'saved status page preference.'
    adminButton = 'Save as default'

    def __init__(self,req):
        self.editSectionBoxes = []

        self.req = req
        form = req.form
        
        # Admin gets to select between all orgs and can save def prefs
        if str(req.session['user']['id']) == Account.ADMIN_ACCOUNT:
            self.isAdmin = True
        orgs = Account.objects.get(id=req.session['user']['id']).organizations
        self.orgList = orgs.values_list('id', flat=True)
        # Make a list of the available SectionBox types
        sectionBoxTypeList = []
        sectionBoxTypeList.append(NetboxSectionBox)
        sectionBoxTypeList.append(NetboxMaintenanceSectionBox)
        sectionBoxTypeList.append(ServiceSectionBox)
        sectionBoxTypeList.append(ServiceMaintenanceSectionBox)
        sectionBoxTypeList.append(ModuleSectionBox)
	sectionBoxTypeList.append(ThresholdSectionBox)
        # Make a dictionary of typeId,SectionBox
        self.sectionBoxTypes = dict([(section.typeId,section) for \
        section in sectionBoxTypeList])
       
        # Create the add bar select options
        self.addBarSelectOptions = [] 
        for typeId,section in self.sectionBoxTypes.items():
            self.addBarSelectOptions.append((typeId,section.name))

        # Define the addbar and the action bar
        self.addBarTitle = 'Select a section to add'
        self.addBarSelectName = 'prefs_sel'
        self.addBarSubmitTitle = 'Add'
        self.addBarSubmitName = 'prefs_add'
        self.addBarSaveName = 'prefs_save'
        self.addBarSaveTitle = 'Save'
        self.addBarSaveDefName = 'prefs_save_def'
        self.addBarSaveDefTitle = 'Save default'
        self.actionBarUpName = 'prefs_up'
        self.actionBarDelName = 'prefs_del'
        self.radioButtonName = 'prefs_radio'

        # Parse the form and add the sections that are already present
        # If this is the initial loading of the prefs page, nothing
        # will be present, and the prefs will be loaded further down
        for field in form.list:
            if field:
                control = re.match('([a-zA-Z]*)_([0-9]+)$',field.name)
                if control:
                    if len(control.groups()) == 2:
                        controlType = control.group(1)
                        controlNumber = control.group(2)

                        controlBaseName = control.string
                        
                        if self.sectionBoxTypes.has_key(controlType):
                            # read settings from the form, and pass them on
                            # to recreate the section box
                            settings = []
                            # field.value contains the title
                            settings.append(field.value)

                            # go through the form controls and add the
                            # list of filter options to the settings
                            selectDict = dict()
                            for selectfield in form.list:
                                #select = re.match('([a-zA-Z]*)_(' + \
                                #controlNumber + ')_([a-zA-Z]+)',\
                                #selectfield.name)
                                
                                select = re.match(controlType + '_(' + \
                                controlNumber + ')_([a-zA-Z]+)',\
                                selectfield.name)

                                if select:
                                    if len(select.groups()) == 2:
                                        # regexp matches, this is a select
                                        # control
                                        control = select.string
                                        if not selectDict.has_key(control):
                                            selectDict[control] = []
                                        value = selectfield.value
                                        if not value:
                                            # Nothing is selected
                                            # equals "All" selected
                                            value = FILTER_ALL_SELECTED
                                        selectDict[control].append(value)
                            # append filtersettings
                            settings.append(selectDict)
                            self.addSectionBox(controlType,settings,
                                               controlBaseName)
        
        # Handle all possible actions
        if form.has_key(self.addBarSubmitName):
            # Add button pressed
            self.addSectionBox(req.form[self.addBarSelectName])
        elif req.form.has_key(self.addBarSaveName):
            # Save button pressed
            self.savePrefs()
        elif req.form.has_key(self.addBarSaveDefName):
            # Save default pressed
            self.saveDefaultPrefs()
        elif (req.form.has_key(self.actionBarDelName) or \
        req.form.has_key(self.actionBarUpName)):
            # Handle action buttons (move up and delete)
            if form.has_key(self.radioButtonName):
                selected = form[self.radioButtonName]
                if form.has_key(self.actionBarDelName):
                    # delete selected
                    index = 0
                    for editSectionBox in self.editSectionBoxes:
                        if editSectionBox.controlBaseName == selected:
                            break
                        index += 1
                    del(self.editSectionBoxes[index])
                    
                elif form.has_key(self.actionBarUpName):
                    # move up selected
                    index = 0
                    for editSectionBox in self.editSectionBoxes:
                        if editSectionBox.controlBaseName == selected:
                            break
                        index += 1
                    if index > 0:
                        tempBox = self.editSectionBoxes[index]
                        self.editSectionBoxes[index] = \
                        self.editSectionBoxes[index-1]
                        
                        self.editSectionBoxes[index-1] = tempBox
        else:
            # No buttons submitted, initial load of the prefs page.
            # Get saved prefs from the database.
            prefs = self.loadPrefs(req)
            self.setPrefs(prefs)
        return

    def addSectionBox(self,addTypeId,settings=None,controlBaseName=None):
        sectionType = self.sectionBoxTypes[addTypeId]

        controlNumber = self.getNextControlNumber(addTypeId)

        self.editSectionBoxes.append(EditSectionBox(sectionType,\
        controlNumber,settings,controlBaseName,self.orgList)) 
        return

    def getNextControlNumber(self,typeId):
        """
        Get the next free control basename for section of type typeId 
        (for example if service_0_orgid exists, next free controlnumber is 1)
        """
        # make a list of the basenames already in use
        baseNameList = []
        for section in self.editSectionBoxes:
            baseNameList.append(section.controlBaseName)

        # find the next available control number, start at 0
        controlNumber = 0
        newBaseName = typeId + '_' + repr(controlNumber)

        while baseNameList.count(newBaseName):
            controlNumber += 1
            newBaseName = typeId + '_' + repr(controlNumber)

        return controlNumber

    def getPrefs(self):
        " returns a StatusPrefs object with the current preferences "
        prefs = StatusPrefs()

        for section in self.editSectionBoxes:
            if section.title == 'Mail':
                raise('jepp'+repr(section.filterSettings))


            newFilterSettings = {}
            # Change filterSettings to use name instead of control name 
            # ie. org instead of netbox_0_org
            for controlName,selected in section.filterSettings.items():
                name = re.match('.*_([a-zA-Z]*)$',controlName) 
                filterName = name.group(1)
                newFilterSettings[filterName] = selected
            prefs.addSection(section.controlBaseName,section.typeId,
            section.title,newFilterSettings)
        return prefs

    def setPrefs(self, prefs):
        """
        Set current preferences for this instance (from loaded prefs)
        """

        for section in prefs.sections:
            controlBaseName,typeId,title,filterSettings = section

            # Must convert filterSettings used by the main status page to
            # the format used by the prefs page (kludgy)
            # the stored name is just the filtername, the full filtername
            # should be controlBaseName + '_' + filtername
            # (this is the reverse of what is done in getPrefs())

            convertedFilterSettings = {}
            for filterName,selected in filterSettings.items():
                newFilterName = controlBaseName + '_' + filterName
                convertedFilterSettings[newFilterName] = selected 
            
            settings = []
            settings.append(title)  
            settings.append(convertedFilterSettings)

            self.addSectionBox(typeId,settings,controlBaseName)
        return

    def savePrefs(self, accountid=None):
        """Pickles and saves the preferences.

        If the accountid parameter is omitted, the currently logged in
        user's preferences are saved.  If set, the preferences will be
        saved for the given account id.

        """
        if accountid is None:
            accountid = self.req.session['user']['id']

        prefs = self.getPrefs()
                
        connection = nav.db.getConnection('status', 'navprofile')
        database = connection.cursor()

        data = cPickle.dumps(prefs.sections)
        sqlParams = {
            'id': accountid,
            'property': self.STATUS_PROPERTY,
            'data': data,
            }

        sql = "SELECT property FROM accountproperty " + \
              "WHERE accountid=%(id)s AND property=%(property)s"
        database.execute(sql, sqlParams)
        result = database.fetchall()

        if result:
            # Prefs exist, update
            sql = "UPDATE accountproperty SET value=%(data)s " + \
                  "WHERE accountid=%(id)s AND property=%(property)s"
        else:
            # No prefs previously saved
            sql = "INSERT INTO accountproperty (accountid,property,value)" + \
                  " VALUES (%(id)s, %(property)s, %(data)s)"
        database.execute(sql, sqlParams)
        connection.commit()

    def loadPrefs(cls,req):
        accountid = req.session['user']['id']

        connection = nav.db.getConnection('status', 'navprofile')
        database = connection.cursor()

        # Attempt to load custom prefs from the user's profile,
        # fallback to admin users's custom prefs if none are found,
        # finally fall back to hardcoded defaults from this module.
        sql = "SELECT value FROM accountproperty WHERE accountid=%s " \
              "and property=%s" 
        for uid in (accountid, ADMIN_USER_ID):
            database.execute(sql, (uid, cls.STATUS_PROPERTY))
            data = database.fetchone()
            if data:
                break
        if data:
            (data,) = data
            prefs = StatusPrefs()
            try:
                prefs.sections = cPickle.loads(str(data))
            except (AssertionError, ImportError), exc:
                # Unpickle failed, probably because of mod_python's
                # import behaviour and the user having saved status
                # prefs in an older version of NAV/mod_python.
                # Instead of attempting to fix the users's prefs, we
                # return the hardcoded defaults and log this incident.
                logger.warning("Ignoring faulty statusprefs for user %s", 
                               req.session['user']['login'])
                logger.debug("The unpickle exception was: ", exc_info=True)
            else:
                # Although we expect the pickle to be a list, it might
                # be that we successfully unpickled an old StatusPrefs
                # object.  If so, we return the unpickled object
                # as-is.
                if isinstance(prefs.sections, StatusPrefs):
                    return prefs.sections
                else:
                    return prefs

        # No system default prefs found (admin users prefs)
        # load from DEFAULT_STATUSPREFS variable
        data = DEFAULT_STATUSPREFS
        prefs = StatusPrefs()
        prefs.sections = copy.deepcopy(data)

        return prefs
    loadPrefs = classmethod(loadPrefs)

    def saveDefaultPrefs(self):
        " Saves current prefs as default preferences "
        return self.savePrefs(accountid=ADMIN_USER_ID)

class EditSectionBox:
    """
    An editable section box on the prefs page.
    """

    name = None
    title = None
    typeId = None
    controlBaseName = None

    # dict of {'controlname': ['selected','entries',...]}
    filterSettings = dict()

    # list of tuples (controlname,list of (value,option,selected=True|False))
    filterSelects = []
    # list of strings ('org','category', etc.)
    filterHeadings = []

    def __init__(self,sectionType,controlNumber,settings,controlBaseName,orgList):
        self.filterSettings = dict()
        self.typeId = sectionType.typeId
        self.orgList = orgList

        # if this is a new section, use the (unique) controlNumber to make
        # a new controlBaseName
        self.controlBaseName = sectionType.typeId + '_' + repr(controlNumber)
        # if this is an existing section, then preserve the controlBaseName
        if controlBaseName:
            self.controlBaseName = controlBaseName

        self.filterHeadings, self.filterSelects = \
        sectionType.getFilters(self.controlBaseName,self.orgList)
        
        self.name = sectionType.name
        self.title = sectionType.name 

        # if settings is present, then this isn't a new section box, so
        # the settings (from the form or loaded prefs) must be preserved
        if settings:
            self.title = settings[0]
            self.filterSettings = settings[1]

            # set selected = True | False based on filterSettings
            newFilterSelects = []
            for controlName, optionList in self.filterSelects:
                newOptionList = []
                for value,option,selected in optionList:
                    # MUST CHECK IF THE RESULT OF THE FORM CONTROL AS
                    # PARSED BY HandleStatusPrefs.__init__ IS PRESENT
                    # FieldStorage(keep_blank_values) SHOULD PREVENT
                    # THE NEED FOR THIS, BUT SOMETHING IS WRONG
                    if not self.filterSettings.has_key(controlName):
                        # If the control name is missing, nothing is selected,
                        # and the 'All' option should be auto selected
                        self.filterSettings[controlName] = [FILTER_ALL_SELECTED]

                    if self.filterSettings[controlName].count(value):
                        selected = True
                    else:
                        selected = False
                        
                    newOptionList.append((value,option,selected))
                newFilterSelects.append((controlName,newOptionList))
            self.filterSelects = newFilterSelects

class StatusPrefs:
    """ 
    class holding a users/groups preference for the status page 
    """

    sections = []

    def __init__(self):
        self.sections = []

    def addSection(self,controlBaseName,typeId,title,filterSettings):
        self.sections.append((controlBaseName,typeId,title,filterSettings))    

DEFAULT_STATUSPREFS = \
[('netbox_0',
  'netbox',
  'IP devices down',
  {'catid': ['all_selected_tkn'],
   'orgid': ['all_selected_tkn'],
   'state': ['n']}),
 ('netbox_1',
  'netbox',
  'IP devices in shadow',
  {'catid': ['all_selected_tkn'],
   'orgid': ['all_selected_tkn'],
   'state': ['s']}),
 ('module_0',
  'module',
  'Modules down',
  {'catid': ['all_selected_tkn'],
   'orgid': ['all_selected_tkn'],
   'state': ['all_selected_tkn']}),
 ('service_0',
  'service',
  'Services down',
  {'handler': ['all_selected_tkn'],
   'orgid': ['all_selected_tkn'],
   'state': ['all_selected_tkn']})]
