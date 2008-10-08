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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#

import nav.db,re

from mod_python import util

class selectTreeLayoutBox:
    ''' Contains a list of selects that will be outputted horizontaly after
        eachother by the template. This layout is completely independent
        from the structure of the selectTree and could also contain selects
        from different selectTrees. For maximum control of layout, you
        can make one selectTreeLayouBox for each select and place them
        anywhere. 
        
        showEmptySelects = BOOLEAN, if True even empty selectboxes will be
                           rendered by the template.
        showHelpTexts = BOOLEAN, if True help texts will be displayed when
                        there is no select to display and showEmptySelects
                        is false. The help texts says 'Select a $PREVTITLE$'
                        where $PREVTITLE$ is the title of the previous select.
        showTitles = BOOLEAN, if True the title of each select is rendered in
                     a <th> table element above the select.
        minimumSelectWidth = The minimum width of the select in pixels
                             (not respected by IE).
        exactSelectWidth = BOOLEAN, set the width of the select to x elements
                           where x is the length of the longest option string.
        htmlId = HTML id for this layoutbox. Makes it possible to
                 jump to this layoutbox in the page.
        '''

    onChange = 'this.form.submit()'
    emptySelectText = 'Select a '

    def __init__(self,
                 showEmptySelects=False,
                 showHelpTexts=True,
                 showTitles=True,
                 minimumSelectWidth=False,
                 exactSelectWidth=False,
                 htmlId=None):

        self.selectList = []
        self.showEmptySelects = showEmptySelects
        self.showHelpTexts = showHelpTexts
        self.showTitles = showTitles
        self.minimumSelectWidth = minimumSelectWidth
        self.exactSelectWidth = exactSelectWidth
        self.htmlId = htmlId

    def addSelect(self,select):
        ''' Adds a select to this layoutBox '''
        self.selectList.append(select)

class selectTree:
    ''' Contains a list of selects. The selects need not be consecutive,
        (ie. the last select need not be updated by the second to last,
        but can be updated by any of the other selects) but they are all 
        updated when update() is called. '''

    def __init__(self):
        self.selectList = []

    def addSelect(self,select):
        ''' Adds a select to the selectTree '''
        self.selectList.append(select)

    def update(self,form):
        ''' Must be called each time the form is posted 
            form: FieldStorage object from mod_python.util '''

        # Fill all simpleselect()s
        for select in self.selectList:
            if not select.prevSelect:
                firstLoad = True
                if form.has_key(select.controlName):
                    firstLoad = False
                select.firstLoad = firstLoad
                select.fill()

        # Set all selected options and fill updateselect()s

        # Set firstLoad=True so that fill() knows that any
        # entries in the addEntryList must be selected if
        # they are set to be. If firstLoad is false all
        # entries in the addEntryList defaults to select=false.
        firstLoad = True
        for select in self.selectList:
            
            selected = []
            if form.has_key(select.controlName):
                selected = form[select.controlName]
                if type(selected) is str:
                    # If only one entry is selected, fieldstorage
                    # returns a string, so we have to make a list of it
                    selected = [selected]
                firstLoad = False
            else: 
                # Set preselected entries, but only if the form hasn't
                # got this select (controlName) posted. Ie. only set
                # preselected entries when the page first loads, then
                # update normally.
                if firstLoad:
                    for preSelected in select.preSelected:
                        # preSelected ids may be ints, so str()
                        if not selected.count(str(preSelected)):
                            selected.append(str(preSelected))
            select.firstLoad = firstLoad

            if not select.prevSelect:
                # simpleSelect, entries in selected are
                # guaranteed to be present and thus selected
                select.selected = selected
                if selected:
                    for option in select.options:
                        if selected.count(option.value):
                            if not (option.optgroup or option.optgroupEnd):
                                option.selected = True
            else:
                # updateSelect, entries in selected might be options
                # which are no longer available if the parent id was
                # deselected in the previous select. Set possiblySelected
                # and use it when filling the updateSelect()s
                select.possiblySelected = selected

                if select.prevSelect.simpleSelect:
                    select.prevSelected = select.prevSelect.selected
                else:
                    select.prevSelected = select.prevSelect.possiblySelected
                select.fill()

class simpleSelect:
    ''' A select which is not updated by any other select, but takes it's 
        list of options directly from a table. Usually the first select
        in a selectTree.
        
        title = Title which can be displayed above the select. If it is
                displayed or not depends on how the layoutbox is setup.
        controlName = HTML control name for the select.
        sqlTuple = Tuple of (fields to get,from tables,join with,
                   where,order by). The strings are merged to give the
                   sql which gets all the entries for the select.
        preSelected = List of id's which must be marked as selected. Used
                      when a search has been done for example.
        addEntryList = List of entries that's added after filling the list
                       from sql. Used to manually add entries which is
                       excluded from the sql for some reason. The entries
                       are tuples (id,text,selected=True|False).
        optionFormat = Format string for the option text in the select.
                       $x is replaced by field x in the sql result.
        valuleFormat = Format string for the value of an option in the select.
                       $x is replaced by field x in the sql result.
                       The default is $1 which means that the sql should
                       get the id field as field number one (or this string
                       must be set otherwise).
        setOnChange =  BOOLEAN, if True the form the select is in will be
                       posted each time a change is made (ie. something is
                       selected or deselected. Usually set to false for
                       the last select in a chain.
        actionOnChange = STRING, script which overrides the usual 
                         this.form.post().
        selectMultiple = BOOLEAN, if True the select gets the HTML attribute
                         multiple.
        multipleHeight = INT, the height of the select in lines.
        disabled       = BOOLEAN, disable select
        '''

    simpleSelect = True
    maxOptionTextLength = 0

    def __init__(self,
                 title,
                 controlName,
                 sqlTuple,
                 preSelected=[],
                 addEntryList=[],
                 optionFormat='$2',
                 valueFormat='$1',
                 setOnChange=True,
                 actionOnChange=None,
                 selectMultiple=True,
                 multipleHeight=5,
                 disabled=False):

        # simpleSelect does never have any prevSelect
        self.prevSelect = None

        self.title = title
        self.controlName = controlName
        self.sqlTuple = sqlTuple
        self.preSelected = preSelected
        self.addEntryList = addEntryList
        self.optionFormat = optionFormat
        self.valueFormat = valueFormat
        self.setOnChange = setOnChange
        self.selectMultiple = selectMultiple
        self.multipleHeight = multipleHeight
        self.disabled = disabled

        self.onChange = None
        if setOnChange:
            self.onChange = 'this.form.submit()'
            if actionOnChange:
                self.onChange = actionOnChange
        # List of selectOption()s
        self.options = []
        # List of selected rows. Save for optgroupformat for next select.
        self.rows = []
        # List of values (id's) in the select
        self.values = []

    def fill(self):
        ''' Fill select from database (using sqltuple) '''

        # Dict with optgroup entries for next select
        self.nextOptgroupList = {}

        # Make sql query
        result = []
        if self.sqlTuple:
            fields,tables,join,where,orderBy = self.sqlTuple
        
            sql = 'SELECT ' + fields + ' FROM ' + tables + ' '
            if where:
                sql += 'WHERE ' + where + ' '           
            if orderBy:
                sql += 'ORDER BY ' + orderBy + ' '

            connection = nav.db.getConnection('default','manage')
            database = connection.cursor()
            database.execute(sql)
            result = database.fetchall()
            connection.commit()
           
        self.maxOptionTextLength = 0 
        for row in result:
            # Save row for optgroupformat in next select
            self.rows.append(row)

            optionText = self.parseFormatstring(self.optionFormat,row)
            value = self.parseFormatstring(self.valueFormat,row)
            self.values.append(value)

            # Find the longest optiontext (used for width of
            # the select in template)
            if len(optionText) > self.maxOptionTextLength:
                self.maxOptionTextLength = len(optionText)

            option = selectOption(optionText,value)
            self.options.append(option)
        # Add entries from the addEntryList
        for entry in self.addEntryList:
            # Check if value (id) is already in select
            if not entry[0] in self.values:
                state = entry[2]
                if not self.firstLoad:
                    state = False
                option = selectOption(entry[1],entry[0],state)
                self.options.append(option)

    def parseFormatstring(self,formatString,fetchedRow):
        ''' Parses format strings for options, values and optgroups.
            $x is replaced by column number x in the sql query. '''
        match = True
        while(match):
            match = re.match('.*\$(\d).*',formatString)
            if match:
                column = match.groups()[0]
                if fetchedRow[int(column)-1]:
                    formatString = formatString.replace('$' + column,
                                   str(fetchedRow[int(column)-1]))
                else:
                    # Empty field, set to ''
                    formatString = ''         
        return formatString

    def optgroupParse(self,formatString,selectedId):
        optgroupText = 'optgroup format error'
        for row in self.rows:
            if str(row[0]) == selectedId:
                optgroupText = self.parseFormatstring(formatString,row)
                break
        return optgroupText

class updateSelect(simpleSelect):
    ''' A select which is updated by a previous select.
        
        prevSelect = The previous select object in the chain.
        prevTableIdKey = The id key used by the table in the
                         previous select.        
        title = Title which can be displayed above the select. If it is
                displayed or not depends on how the layoutbox is setup.
        controlName = HTML control name for the select.
        sqlTuple = Tuple of (fields to get,from tables,join with,
                   where,order by). The strings are merged to give the
                   sql which gets all the entries for the select.
        preSelected = List of id's which must be marked as selected. Used
                      when a search has been done for example.
        addEntryList = List of entries that's added after filling the list
                       from sql. Used to manually add entries which is
                       excluded from the sql for some reason. The entries
                       are tuples (optgroupid,id,text,selected=True|False).
        optionFormat = Format string for the option text in the select.
                       $x is replaced by field x in the sql result.
        valuleFormat = Format string for the value of an option in the select.
                       $x is replaced by field x in the sql result.
                       The default is $1 which means that the sql should
                       get the id field as field number one (or this string
                       must be set otherwise).
        optgroupFormat = Format string for the optgroup text. $x is replaced
                         by field x in the sql result.
        setOnChange =  BOOLEAN, if True the form the select is in will be
                       posted each time a change is made (ie. something is
                       selected or deselected. Usually set to false for
                       the last select in a chain.
        actionOnChange = STRING, script which overrides the usual
                         this.form.post()
        selectMultiple = BOOLEAN, if True the select gets the HTML attribute
                         multiple.
        multipleHeight = INT, the height of the select in lines. 
        disabled       = BOOLEAN, disable select '''

    simpleSelect = False

    def __init__(self,
                 prevSelect,
                 prevTableIdKey,
                 title,
                 controlName,
                 sqlTuple,
                 preSelected=[],
                 addEntryList=[],
                 optionFormat='$2',
                 valueFormat='$1',
                 optgroupFormat=None,
                 setOnChange=True,
                 actionOnChange=None,
                 selectMultiple=True,
                 multipleHeight=5,
                 disabled=False):

        # Link with previous select
        self.prevSelect = prevSelect
        self.prevTableIdKey = prevTableIdKey

        self.title = title
        self.controlName = controlName
        self.sqlTuple = sqlTuple
        self.preSelected = preSelected
        self.addEntryList = addEntryList
        self.optionFormat = optionFormat
        self.valueFormat = valueFormat
        self.optgroupFormat = optgroupFormat
        self.setOnChange = setOnChange
        self.selectMultiple = selectMultiple
        self.multipleHeight = multipleHeight
        self.disabled = disabled

        self.onChange = None
        if setOnChange:
            self.onChange = 'this.form.submit()'
            if actionOnChange:
                self.onChange = actionOnChange
        # List of selectOption()s
        self.options = []
        # List of selected rows. Save for optgroupformat for next select.
        self.rows = []
        # List of values (id's) in the select
        self.values = []

    def fill(self):
        ''' Fill select from database (using sqltuple and prevselected).
            Checks the list of selected entries from the prevSelect 
            select. '''

        # Any of the options in the previous select selected?
        # Make sql query
        fields,tables,join,where,orderBy = self.sqlTuple
       
        confirmedSelected = []
        self.maxOptionTextLength = 0
        if not self.prevSelected:
            self.prevSelected = []
        for s in self.prevSelected:
            sql = 'SELECT ' + fields + ' FROM ' + tables + ' '
            sql += 'WHERE ' + self.prevTableIdKey + "='" + s + "' "
                
            if where:
                sql += 'AND ' + where + ' '           
            if orderBy:
                sql += 'ORDER BY ' + orderBy + ' '

            connection = nav.db.getConnection('default','manage')
            database = connection.cursor()
            database.execute(sql)
            result = database.fetchall()
            connection.commit()
            
            if self.optgroupFormat:
                optgroupText=self.prevSelect.optgroupParse(
                                  self.optgroupFormat,s)
            else:
                optgroupText=s
            optgroup = selectOption(optgroupText,'',optgroup=True)
            self.options.append(optgroup)
            # Add options
            for row in result:
                # Save row for optgroupformat in next select
                self.rows.append(row)
                optionText = self.parseFormatstring(self.optionFormat,row)
                value = self.parseFormatstring(self.valueFormat,row)
                self.values.append(value)

                # Find the longest optiontext (used for width of
                # the select in template)
                if len(optionText) > self.maxOptionTextLength:
                    self.maxOptionTextLength = len(optionText)

                selected = False
                # Any candidates for marking as selected?
                # Possibly selected means that an entry was marked as
                # selected in the select, but since the entry in the
                # previous select which gave these options could have
                # been deselected, we must check if it is still present
                if self.possiblySelected:
                    if self.possiblySelected.count(value):
                        selected = True
                        # This entry is confirmed as both selected in
                        # the posted select, and still present after
                        # considering what is selected in the previous
                        # select. Add this id (value) to the list of
                        # confirmed selections. The list of possibly
                        # selected is then replaced by the list of
                        # confirmed selected after filling. This ensures
                        # that the next select is correctly updated.
                        confirmedSelected.append(value)
                option = selectOption(optionText,value,selected)
                self.options.append(option)
            # Add entries from addEntryList
            for entry in self.addEntryList:
                if (s == entry[0]):
                    # This is the right optgroup for this entry
                    # Save row for optgroupformat in next select
                    # NB: only works with default optgroupformat! FIX
                    self.rows.append((entry[1],entry[2]))

                    if not entry[1] in self.values:
                        # Value (id) isn't already present
                        state = entry[3]
                        if not self.firstLoad:
                            # If this isn't the first load of the page
                            # then selected defaults to false no matter
                            # what the addEntryList entry says
                            state = False
                        if self.possiblySelected.count(entry[1]):
                            # But the user could have selected it
                            state = True
                        option = selectOption(entry[2],entry[1],state)
                        self.options.append(option)
                        if state == True:
                            confirmedSelected.append(entry[1])
            # Add end of optgroup tag to list of options
            optgroup = selectOption('','',optgroupEnd=True)
            self.options.append(optgroup)
        self.possiblySelected = confirmedSelected

class selectOption:
    ''' An option in a select. '''
    def __init__(self,text,value,selected=False,
                 optgroup=False,optgroupEnd=False,disabled=False):
        self.text = text
        self.value = value
        self.selected = selected
        self.optgroup = optgroup
        self.optgroupEnd = optgroupEnd
        self.disabled = disabled
