# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2005 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Representing a report object."""

import re
import string

from nav.web.URI import URI

class Field:

    def __init__(self):
        self.title = ""
        self.raw = ""

    def __repr__(self):
        return "<Field %s = %s>" % (self.title, self.raw)

class Report:
    """
    A nice formatted Report object, ready for presentation
    """


    def __init__(self,configuration,database,path):
        """
        The constructor of the Report class

        - configuration : a ReportConfig object containing all the configuration
        - database      : a DatabaseResult object that will be modified according
                          to the configuration
        - path          : the address of the requested page
        """

        self.rowcount = database.rowcount
        self.sums = database.sums

        self.limit = int(str((self.setLimit(configuration.limit))))
        self.offset = int(str(self.setOffset(configuration.offset)))

        # oh, the smell, it kills me!
        if self.limit:
            self.formatted = database.result[self.offset:self.limit+self.offset]
        else:
            self.formatted = database.result
        self.dbresult = database.result
        
        self.address = self.stripPath(path)

        self.title = configuration.title
        self.hide = configuration.hidden
        self.extra = configuration.extra

        self.name = configuration.name
        self.explain = configuration.explain
        self.uri = configuration.uri

        self.fields = configuration.sql_select + self.extra
        self.sql_fields = configuration.sql_select
        self.fieldNum,self.fieldName = self.fieldNum(self.fields)
        self.fieldsSum = len(self.fields)
        self.shown = self.hideIndex()

        self.uri = self.remakeURI(self.uri)

        self.table = self.makeTableContents()
        footers = self.makeTableFooters(self.sums)
        self.table.setFooters(footers)
        headers = self.makeTableHeaders(self.name,self.uri,self.explain,configuration.orderBy)
        self.table.setHeaders(headers)

        self.navigator = Navigator()
        self.navigator.setNavigator(self.limit,self.offset,self.address,self.rowcount)

        self.form = self.makeForm(self.name)

        if database.error:
            self.navigator.setMessage(database.error)

    def setLimit(self,config):
        """
        returns the limit according to the configuration or the default (1000)

        - config : the limit of the configuration

        returns the limit of the configuration or 1000
        """

        if config:

            return config

        else:

            return 1000

    def setOffset(self,config):
        """
        returns the offset according to the configuration or the default (0)

        - config : the offset according th the configuration

        returns the offset of the configuration or 0
        """

        if config:

            return config

        else:

            return 0

    def stripPath(self,path):
        """
        removes the 'limit' and 'offset' arguments from the uri that will used on the page

        - path : the path that will get its 'limit' and 'offset'- fields removed

        returns the new path
        """
        uri = URI(path)
        stripFields = ['limit','offset']
        for field in stripFields:
            if field in uri.args:
                del uri.args[field]
        return uri.make()

    def fieldNum(self,fields):
        """
        returns a hash associating the field names to the field numbers

        - fields : a list containing the field names

        returns the hash with fieldname=>fieldnumber pairs
        """

        fieldNum = {}
        fieldName = {}

        for field in fields:

            number = fields.index(field)
            fieldNum[field] = number
            fieldName[number] = field

        return fieldNum,fieldName


    def remakeURI(self,uri):
        """
        takes a hash of uris associated to their names, and returns a hash of uris associated to their field numbers. this is a more effective approach than doing queries to a dictionary.

        - uri : a hash of fieldnames and their uris

        returns a hash of fieldnumbers and their uris
        """

        uri_hash = uri
        uri_new = {}

        for key,value in uri_hash.items():

            if self.fields.count(key):
                key_index = self.fields.index(key)

                if self.shown.count(key_index):

                    uri_new[key_index] = value

        return uri_new


    def makeTableHeaders(self,name,uri,explain,sortList=[]):
        """
        makes the table headers

        - name    : a hash containing the numbers and names of the fields
        - uri     : a hash containing the numbers of the fields and their uris
        - explain : a hash containing the numbers of the fields and the fields explicit explanations

        returns a list of cells that later will represent the headers of the table
        """

        name_hash = name
        explain_hash = explain

        #bruker ikke uri ennå
        uri_hash = uri
        headers = Headers()

        sorted = ""
        if sortList:
            sorted = sortList[0]

        ## for each of the cols that will be displayed
        for header in self.shown:
            ## get the name of it
            title = self.fields[header]
            explanation = ""
            uri = URI(self.address)
            if sorted == title:
                uri.setArguments(['sort','order_by'],"-"+title)
            else:
                uri.setArguments(['sort','order_by'],title)
            uri = uri.make()

            ## change if the name exist in the overrider hash
            if name_hash.has_key(title):
                title = name_hash[title]

            if explain_hash.has_key(title):
                explanation = explain_hash[title]

            field = Cell(title,uri,explanation)
            headers.append(field)

        return headers


    def makeTableFooters(self,sum):
        """
        makes the table footers. ie. the sum of the columns if specified

        - sum : a list containing the numbers of the fields that will be summarized

        returns a list of cells that later will represent the footers of the table
        """

        footers = Footers()

        ## for each of the cols that will be displayed
        for footer in self.shown:
            ## get the name of it
            title = self.fields[footer]

            thisSum = Cell()

            ## change if the name exist in the overrider hash
            if sum.has_key(title):
                
                ## Summmarize the results for a given title
                part_sum = 0
                for a in self.formatted: 
                    if a[footer] != None:
                        part_sum += int(str(a[footer]))
                
                total_sum = 0
                for a in self.dbresult: 
                    if a[footer] != None:
                        total_sum += int(str(a[footer]))

                if part_sum == total_sum:
                    thisSum.setSum(str(part_sum))
                
                elif sum[title] == 0:
                    thisSum.setSum("0")
                
                else:
                    thisSum.setSum(str(part_sum) + "/" + str(total_sum))

            footers.append(thisSum)

        return footers


    def hideIndex(self):
        """
        makes a copy of the list of all fields where those that will be hidden is ignored

        returns the list of fields that will be displayed in the report
        """

        #print self.fields

        shown = []
        for field in range(0,self.fieldsSum):

            if not self.hide.count(self.fields[field]):

                shown.append(field)

        return shown


    def makeTableContents(self):
        """
        makes the contents of the table of the report

        returns a table containing the data of the report (without header and footer etc)
        """

        linkFinder = re.compile("\$(.+?)(?:$|\$|\&|\"|\'|\s|\;)",re.M)

        newtable = Table()
        for line in self.formatted:

            newline = Row()
            for field in self.shown:

                newfield = Cell()

                ## the number of fields shown may be larger than the size
                ## of the tuple returned from the database
                try:

                    if self.extra.count(self.fieldName[field]):
                        text = self.fields[field]
                    else:
                        #if not field >= len(self.shown) - len(self.extra)+2:
                        text = line[field]
                    #else:
                        #text = self.fields[field]

                except KeyError,e:
                    text = "feil"

                newfield.setText(text)

                if self.uri.has_key(field):

                    uri = self.uri[field]

                    links = linkFinder.findall(uri)
                    if links:
                        for link in links:
                            to = line[self.fieldNum[link]]
                            if to:
                                to = unicode(to).encode('utf-8')
                            else:
                                to = ""
                            hei = re.compile("\$"+link)
                            try:
                                uri = hei.sub(to,uri)
                            except TypeError:
                                uri = uri + to
                    newfield.setUri(uri)

                newline.append(newfield)

            newtable.append(newline)

        return newtable


    def makeForm(self,name):

        form = []

        for no,field in self.fieldName.items():
            f = None
            ## does not use aggregate function elements
            if not self.extra.count(field) and not self.sql_fields[no].count("("):
                f = Field()
                f.raw = self.sql_fields[no]
                if name.has_key(field):
                    f.title = name[field]
                else:
                    f.title = field

                form.append(f)

        return form


class Navigator:
    """
    An object that represents the next-previous-status (navigation) parts of the page displayed
    """

    def __init__(self):

        self.view = ""
        self.previous = ""
        self.next = ""

    def setMessage(self,message):
        """
        Sets the view-field (the line under the title of the page) to "message"

        - message : the new message to appear at the page
        """

        self.view = message

    def setNavigator(self,limit,offset,address,number):
        """
        Sets the values of the navigator object

        - limit  : the number of results per page
        - offset : the number of the first result displayed on the page
        - address : the uri used when making the next an previous buttons
        - number : total number of restults returned from the query

        """

        number_int = int(number)
        number = str(number)
        offset_int = int(offset)
        offset = str(offset)
        limit_int = int(limit)
        limit = str(limit)
        number_int = int(number)
        number = str(number)

        next = str(offset_int+limit_int)
        previous = str(offset_int-limit_int)
        view_from = str(offset_int+1)
        view_to_int = offset_int + limit_int
        view_to = str(view_to_int)

        if offset_int:

            uri = URI(address)
            uri.setArguments(['limit'],limit)
            uri.setArguments(['offset'],previous)

            self.previous = uri.make()

        if limit_int+offset_int<number_int:

            uri = URI(address)
            uri.setArguments(['limit'],limit)
            uri.setArguments(['offset'],next)

            self.next = uri.make()

        if number_int:
            if limit_int>number_int:
                self.view = number+" hits"
            elif view_to_int>number_int:
                self.view = view_from+" - "+number+" of "+number
            else:
                self.view = view_from+" - "+view_to+" of "+number
        else:
            self.view = "Sorry, your search did not return any results"

class Table:
    """
    A table that will contain the results of the report
    """

    def __init__(self):

        self.rows = []
        self.header = []
        self.footer = []

    def append(self,row):
        """
        Appends a row to the table

        - row : the row to be appended to the table

        """

        self.rows.append(row)

    def extend(self,listOfRows):
        """
        Extends the table with a list of rows

        - listOfRows : the list of rows to append to the table

        """

        self.rows.extend(listOfRows)

    def setHeaders(self,header):
        """
        Sets the headers of the table

        - header : the list of cells that represents the header

        """

        self.header = header

    def setFooters(self,footer):
        """
        Sets the footers of the table

        - footer : the list of cells that represents the footer (the bottom line)

        """

        self.footer = footer

    def setContents(self,contents):
        """
        Sets the contents of the table

        - contents : the new contents of the table

        """

        self.rows = contents


class Row:
    """
    A row of a table
    """

    def __init__(self):

        self.cells = []

    def append(self,cell):
        """
        Appends a cell to the row

        - cell : the cell to be appended

        """

        self.cells.append(cell)

class Cell:
    """
    One cell of the table
    """

    def __init__(self,text=u"",uri=u"",explanation=u""):

        self.setText(text)
        self.setUri(uri)
        self.setExplanation(explanation)
        self.sum = u""

    def setText(self,text):
        """
        Sets the contents of the cell to the text specified

        - text : the text to be used

        """

        self.text = unicode_utf8(text)


    def setUri(self,uri):
        """
        Sets the uri of the cell to the text specified

        - uri : the text to be used as the uri

        """

        self.uri = unicode_utf8(uri)


    def setExplanation(self,explanation):
        """
        Sets the explanation of the column to the text specified

        - explanation : the text to be used as the explanation

        """

        self.explanation = unicode_utf8(explanation)

    def setSum(self,sum):
        """
        Sets the sum of the column to the text specified

        - sum : the text to be used as the sum of the column

        """

        self.sum = unicode_utf8(sum)


class Headers:
    """
    The top row of the report table. Where the titles and descriptions etc, is displayed
    """

    def __init__(self):

        self.cells = []

    def append(self,cell):
        """
        Appends a cell to the list of headers

        - cell : the cell to be appended

        """

        self.cells.append(cell)

class Footers:
    """
    The bottom row of the report table. Where the sum of some columns is displayed
    """

    def __init__(self):

        self.cells = []

    def append(self,cell):
        """
        Appends a cell to the list of footers

        - cell : the cell to be appended

        """

        self.cells.append(cell)

def unicode_utf8(thing):
    """Casts thing to unicode, assuming utf-8 encoding if a string."""
    if isinstance(thing, str):
        return thing.decode('utf-8')
    else:
        return unicode(thing)

