#
# $Id: treeSelect.py 2773 2004-06-04 18:00:00Z hansjorg $
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

import nav.db,re

from mod_python import util

class selectTreeLayoutBox:
    ''' Contains a list of selects that will be outputted horizontaly after
        eachother by the template. This layout is completely independent
        from the structure of the selectTree and could also contain selects
        from different selectTrees. For maximum control of layout, you
        can make one selectTreeLayouBox for each select and place them
        anywhere. '''

    onChange = 'this.form.submit()'
    emptySelectText = 'Select a '

    def __init__(self,
                 showEmptySelects=False,
                 showHelpTexts=True,
                 showTitles=True,
                 minimumSelectWidth=False,
                 exactSelectWidth=False):

        self.selectList = []
        self.showEmptySelects = showEmptySelects
        self.showHelpTexts=showHelpTexts
        self.showTitles = True
        self.minimumSelectWidth = minimumSelectWidth
        self.exactSelectWidth = exactSelectWidth

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
                select.fill()

        # Set all selected options and fill updateselect()s
        for select in self.selectList:
            
            selected = []
            if form.has_key(select.controlName):
                selected = form[select.controlName]
                if type(selected) is str:
                    # If only one entry is selected, fieldstorage
                    # returns a string, so we have to make a list of it
                    selected = [selected]
            
            # Set preselected entries
            for preSelected in select.preSelected:
                # preSelected ids may be ints, so str()
                if not selected.count(str(preSelected)):
                    selected.append(str(preSelected))

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
        in a selectTree '''

    simpleSelect = True
    maxOptionTextLength = 0

    def __init__(self,
                 title,
                 controlName,
                 sqlTuple,
                 preSelected=[],
                 optionFormat='$2',
                 valueFormat='$1',
                 postOnChange=True,
                 selectMultiple=True,
                 multipleHeight=5):

        # simpleSelect does never have any prevSelect
        self.prevSelect = None

        self.title = title
        self.controlName = controlName
        self.sqlTuple = sqlTuple
        self.preSelected = preSelected
        self.optionFormat = optionFormat
        self.valueFormat = valueFormat
        self.postOnChange = postOnChange
        self.selectMultiple = selectMultiple
        self.multipleHeight = multipleHeight

        self.onChange = None
        if postOnChange:
            self.onChange = 'this.form.submit()'
        # List of selectOption()s
        self.options = []
        # List of selected rows. Save for optgroupformat for next select.
        self.rows = []

    def fill(self):
        ''' Fill select from database (using sqltuple) '''

        # Dict with optgroup entries for next select
        self.nextOptgroupList = {}

        # Make sql query
        fields,tables,join,where,orderBy = self.sqlTuple
        
        sql = 'SELECT ' + fields + ' FROM ' + tables + ' '
        if where:
            sql += 'WHERE ' + where + ' '           
        if orderBy:
            sql += 'ORDER BY ' + orderBy + ' '

        # Execute sql query (replace editdb with treeSelect user)
        connection = nav.db.getConnection('editdb','manage')
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

            # Find the longest optiontext (used for width of
            # the select in template)
            if len(optionText) > self.maxOptionTextLength:
                self.maxOptionTextLength = len(optionText)

            option = selectOption(optionText,value)
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
    ''' A select which is updated by a previous select. '''

    simpleSelect = False

    def __init__(self,
                 prevSelect,
                 prevTableIdKey,
                 title,
                 controlName,
                 sqlTuple,
                 preSelected=[],
                 optionFormat='$2',
                 valueFormat='$1',
                 optgroupFormat=None,
                 postOnChange=True,
                 selectMultiple=True,
                 multipleHeight=5):

        # Link with previous select
        self.prevSelect = prevSelect
        self.prevTableIdKey = prevTableIdKey

        self.title = title
        self.controlName = controlName
        self.sqlTuple = sqlTuple
        self.preSelected = preSelected
        self.optionFormat = optionFormat
        self.valueFormat = valueFormat
        self.optgroupFormat = optgroupFormat
        self.postOnChange = postOnChange
        self.selectMultiple = selectMultiple
        self.multipleHeight = multipleHeight

        self.onChange = None
        if postOnChange:
            self.onChange = 'this.form.submit()'
        # List of selectOption()s
        self.options = []
        # List of selected rows. Save for optgroupformat for next select.
        self.rows = []

    def fill(self):
        ''' Fill select from database (using sqltuple and prevselected).
            Checks the list of selected entries from the prevSelect 
            select. '''

        # Any of the options in the previous select selected?
        #raise(repr(self.prevSelected))
        #if self.prevSelected:
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
                sql += where + ' '           
            if orderBy:
                sql += 'ORDER BY ' + orderBy + ' '

            # Execute sql query (replace editdb with treeSelect user)
            connection = nav.db.getConnection('editdb','manage')
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
