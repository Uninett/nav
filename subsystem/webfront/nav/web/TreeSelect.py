# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
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
Contains three classes for constructing a tree select.
The TreeSelect class is a continer for Select instances.
Select represents a general select, and UpdateableSelect
is a select that is generated dynamically based on input
in the Select and the other UpdateableSelects.
"""

#################################################
## Imports

import nav.db.manage

#################################################
## class TreeSelect

class TreeSelect:
    """ TreeSelect is a container class for Select and UpdateableSelect
    objects. The select objects are instantiated and then added with the
    addSelect method. When the form is submitted by a change in one of
    the selects, update() must be called to make changes to the selects. """

    # List of elements in this TreeSelect
    elementList = None
    defaultWidth = '300'
    formName = 'treeselect'

    def __init__(self):
        self.elementList = []
        return

    def addSelect(self, select):
        " Adds a select object to the element list. "
        self.elementList.append(select)
        return

    def update(self,form):
        " Updates the selects in the element list based on the form. "
        for select in self.elementList:
            if select.updateThis:
                select.selectedList = []
                maybe_selected = []

                if form.has_key(select.elementName):
                    # maybe_selected is the rows indicated as selected from the
                    # form. since there may be rows which are selected, but
                    # doesn't exist after updating the previous box, the list
                    # must be checked against the existing rows in the prev select
                    maybe_selected = form[select.elementName] 

                    # if only one row is selected, the mod_python FieldObject
                    # returns a string, not a list. Checks and makes a list. 
                    if not type(maybe_selected) is list:
                        maybe_selected = [maybe_selected]

                if select.prevElement:
                    # does this select have a previous select element?
                    # ie. another select box to the left of it
                    for selected in maybe_selected:
                        
                        if(form.has_key(select.elementName + '_' + selected)):
                            # this row was selected the last time
                            # should it still be selected?
                            last_key = form[select.elementName + '_' + selected]
                            if select.prevElement.selectedList.count(last_key):
                                select.selectedList.append(selected)
                        else:
                            # this row was just selected now, so it must be added
                            select.selectedList.append(selected)
                else:
                    # if this is the first select, then the selected rows in
                    # the form are always correct (the first list is static)
                    select.selectedList = maybe_selected

                # Are there any preselected items?
                # In that case, add them now
                for id in select.preSelected:
                    if not select.selectedList.count(id):
                        select.selectedList.append(id)

        # Recurse through the elements and update the options
        # start with the first element
        if select.updateThis:
            select = self.elementList[0] 
            next = select.nextElement

            while(next):
                next.updateOptions(next.prevElement.selectedList)
                next = next.nextElement 

            # update the selected rows (selected in form -> Option.selected = true)
            for select in self.elementList:
                select.updateSelected()


#################################################
## Class Select


class Select:
    """ Select is a simple select. Used for the first select in the TreeSelect
    It is not possible to update it dynamically. The options list is populated
    by the initOptions() method, each time the Select is instantiated. """

    # Update this select with TreeSelect.update()?
    updateThis = True

    # html element name
    elementName = None

    # list of options and default options
    options = []
    optionsDefault = []

    # multiple select [True|False] and the size in rows of the select
    multiple = False
    multipleSize = None

    # the table and columns used to initialize the options
    initTable = None
    initTextColumn = None
    initIdColumn = None

    # html onchange attrib (script)
    onchange = None

    # points to the next and previous selects
    nextElement = None
    prevElement = None

    # copy of the list of selected entries for this select
    selectedList = []

    def __init__(self,
                 elementName,
                 title,
                 optionsDefault = None,
                 multiple = False,
                 multipleSize = None,
                 initTable = None,
                 initTextColumn = None,
                 initIdColumn = None,
                 onchange = 'this.form.submit()',
                 preSelected = [],
                 optionFormat = None,
                 optgroupFormat = None,
                 orderByValue = False):

        """ 
        elementName = html element name for this select
        optionsDefault = list of default Option()'s for top of select
        multiple = [True|False], multiple select allowed or not
        multipleSize = number of rows displayed if multiple select is on
        initTable = name of the table that initializes this select
        initTextColumn = the column used for text on each option
        initIdColumn = the primary key used for each options value
        onchange = script for submitting on each change
        preSelected = list of preselected id's (from QuickSelect for ex.)
        optionFormat = format string for the <option>s $v = value, $d = descr
        optgroupFormat = format string for <optgroup>s $v = value, $d = descr
        orderByValue = True|False, order by value? else order by descr
        """

        self.elementName = elementName
        self.title = title
        self.onchange = onchange
        self.preSelected = preSelected
        self.optionFormat = optionFormat
        self.optgroupFormat = optgroupFormat
        self.orderByValue = orderByValue

        # Add the default options
        self.options = []
        if optionsDefault:
            self.optionsDefault = optionsDefault
            self.addDefaultOptions()
 
        if multiple:
            self.multiple = True
        self.multipleSize = multipleSize

        # Populate the options list
        self.initTable = initTable
        self.initTextColumn = initTextColumn
        self.initIdColumn = initIdColumn
        if self.initTable:
            self.initOptions()
        return

    def initOptions(self):
        " Populate the options list from the initTable. "
        table = getattr(nav.db.manage, self.initTable)

        ob = self.initTextColumn
        if self.orderByValue:
            ob = self.initIdColumn

        for row in table.getAllIterator(orderBy=ob):
            descr = getattr(row, self.initTextColumn)
            value = getattr(row, self.initIdColumn)

            if self.optionFormat:
                text = self.optionFormat
                text = text.replace('$v',value)
                text = text.replace('$d',descr)
            else:
                text = descr
            selected = False
            
            self.options.append(Option(text,value,selected)) 
        return

    def updateSelected(self):
        " Updates the selected options. Must be called for each update(). "
        if type(self.selectedList) is str:
            string = self.selectedList
            self.selectedList = []
            self.selectedList.append(string)

        for option in self.options:
            value = option.value
            if self.selectedList.count(value):
                option.selected = True
        return

    def addDefaultOptions(self):
        " Adds the default options for this select. Called for each init "
        for option in self.optionsDefault:
            self.options.append(option)
        return

    def lastKeys(self):
        """ Makes hidden inputs for the form. Last_keys tells what keys in 
        the previous table which were used to get these keys. FIX """
        output = ''
        for option in self.options:
            if option.selected:
                output += '<input type="hidden" name="%s_%s" value="%s">\n' \
                % (self.elementName, option.value, option.last_key)
        return output

    def getAttribs(self):
        """
        Returns the html attributes for this select element
        """
        attribs = 'size="' + str(self.multipleSize) + '"'
        if self.multiple:
            attribs += ' multiple="multiple"' 
        return attribs


#################################################
## class UpdateableSelect

class UpdateableSelect(Select):
    """ 
    UpdateableSelect inherits from Select. It can be dynamically updated
    based on the table in updateFromTable. The updateOptions() method must
    be called when the selections in the previous select has changed.
    """

    updateFromTable = None

    textColumn = None
    idColumn = None
    foreignColumn = None
   
    def __init__(self,
                 prevElement,
                 elementName,
                 title,
                 updateFromTable,
                 textColumn,
                 idColumn,
                 foreignColumn,
                 optionsDefault = None,
                 multiple = False,
                 multipleSize = None,
                 initTable = None,
                 initTextColumn = None,
                 initIdColumn = None,
                 onchange = 'this.form.submit()',
                 preSelected = [],
                 optionFormat = None,
                 optgroupFormat = None,
                 orderByValue = False):

        """ 
        prevElement = the previous select in the TreeSelect
        updateFromTable = the table used to dynamically update the select
        textColumn = the column containing the text for the Option()
        idColumn = the column containing the primary key (value for Option)
        foreignColumn = corresponding to the primary key in the last select
        """

        # link together with the last select
        self.prevElement = prevElement
        prevElement.nextElement = self

        self.updateFromTable = updateFromTable
        self.textColumn = textColumn
        self.idColumn = idColumn
        self.foreignColumn = foreignColumn

        # call the constructor of the anecstor (Select)
        Select.__init__(self,
                        elementName,
                        title,
                        optionsDefault = optionsDefault,
                        multiple = multiple,
                        multipleSize = multipleSize,
                        initTable = initTable,
                        initTextColumn = initTextColumn,
                        initIdColumn = initIdColumn,
                        onchange = onchange,
                        preSelected = preSelected,
                        optionFormat = optionFormat,
                        optgroupFormat = optgroupFormat,
                        orderByValue = orderByValue)
        return

    def updateOptions(self, selectedList):
        """ Takes a list of selected entries (ids) from the previous table
        and updates the options in this select. """

        table = getattr(nav.db.manage, self.updateFromTable)

        for selected in selectedList:
            optgroupText = selected
            if self.prevElement.initTable:
                # this is the first updateable select, so get optgroup
                # text from the initTable of the first select element
                prevTable = getattr(nav.db.manage, self.prevElement.initTable)
                optgroupDescr = str(getattr(prevTable(selected),\
                                    self.prevElement.initTextColumn))
                optgroupValue = str(selected)
                if self.optgroupFormat:
                    optgroupText = self.optgroupFormat
                    optgroupText = optgroupText.replace('$v',optgroupValue)
                    optgroupText = optgroupText.replace('$d',optgroupDescr)
                else:
                    optgroupText = optgroupDescr + ' (' + optgroupValue + ')'
            else:
                # this is any other updateable select, so get opgroup
                # text from the last updateable select
                prevTable = getattr(nav.db.manage, self.prevElement.updateFromTable)
                optgroupDescr = str(getattr(prevTable(selected),\
                                    self.prevElement.textColumn))
                optgroupValue = str(selected)

                if self.optgroupFormat:
                    optgroupText = self.optgroupFormat
                    optgroupText = optgroupText.replace('$v',optgroupValue)
                    optgroupText = optgroupText.replace('$d',optgroupDescr)
                else:
                    optgroupText = optgroupDescr + ' (' + optgroupValue + ')'
 
            self.options.append(Option('',optgroupText,optgroup=True))

            where_clause = self.foreignColumn + " = '" + selected + "'" 

            ob = self.textColumn
            if self.orderByValue:
                ob = self.idColumn
            for row in table.getAllIterator((where_clause),
                                            orderBy=ob):
                value = getattr(row, self.idColumn)
                descr = getattr(row, self.textColumn)

                if not type(value) is str:
                    value = repr(value)

                if not type(descr) is str:
                    descr = repr(descr)

                if self.optionFormat:
                    text = self.optionFormat
                    text = text.replace('$v',value)
                    text = text.replace('$d',descr)
                else:
                    text = descr

                self.options.append(Option(text,value,selected = False,\
                last_key=selected))
        return

# Class SimpleSelect

class SimpleSelect(Select):
    # Don't update this with TreeSelect.update()
    updateThis = False
    onchange = None

    def __init__(self,
                 elementName,
                 title,
                 initTable,
                 initTextColumn,
                 initIdColumn,
                 initIdList,
                 multiple = False,
                 multipleSize = None,
                 optionFormat=None,
                 orderByValue=False):

        self.options = []
        self.elementName = elementName
        self.title = title
        self.initTable = initTable
        self.initTextColumn = initTextColumn
        self.initIdColumn = initIdColumn
        self.initIdList = initIdList
        self.multiple = multiple
        self.multipleSize = multipleSize
        self.optionFormat = optionFormat
        self.orderByValue = orderByValue

        self.initOptions()

    def initOptions(self):
        " Populate the options list from the initTable. "
        table = getattr(nav.db.manage, self.initTable)

        ob = self.initTextColumn
        if self.orderByValue:
            ob = self.initIdColumn

        if len(self.initIdList):
            where = ''
            for id in self.initIdList:
                if where:
                    where += " OR "
                where += self.initIdColumn + "='%s' " % (id,)

            for row in table.getAllIterator(orderBy=ob,where=where):
                descr = getattr(row, self.initTextColumn)
                value = getattr(row, self.initIdColumn)

                if self.optionFormat:
                    text = self.optionFormat
                    text = text.replace('$v',str(value))
                    text = text.replace('$d',str(descr))
                else:
                    text = descr
                selected = False
                
                self.options.append(Option(text,value,selected)) 
        return
    
    def lastKeys(self):
        return None

#################################################
## class Option

class Option:
    """ 'Struct' describing a single option in any select """
    def __init__(self, text, value, last_key = None, selected = False, \
    optgroup = False, disabled=False):
        self.last_key = last_key
        self.disabled = disabled
        self.value = value
        self.text = text
        self.selected = selected
        self.optgroup = optgroup
        return
