#!/usr/bin/env python

import re

from Navigator import Navigator
from Table import Table
from Row import Row
from Cell import Cell
from Headers import Headers
from Footers import Footers
from URI import URI

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

        self.formatted = database.result
        self.rowcount = database.rowcount
        self.sums = database.sums

        self.limit = self.setLimit(configuration.limit)
        self.offset = self.setOffset(configuration.offset)

        self.address = self.stripPath(path) 

        self.header = configuration.header
        self.hide = configuration.hidden
        self.extra = configuration.extra

        self.name = configuration.name
        self.explain = configuration.explain
        self.uri = configuration.uri
        
        self.fields = configuration.sql_select + self.extra
        self.fieldNum = self.fieldNum(self.fields)
        self.fieldsSum = len(self.fields)
        self.shown = self.hideIndex()

        self.uri = self.remakeURI(self.uri)

        self.table = self.makeTableContents()
        footers = self.makeTableFooters(self.sums)
        self.table.setFooters(footers)
        headers = self.makeTableHeaders(self.name,self.uri,self.explain)
        self.table.setHeaders(headers)

        self.navigator = Navigator()
        self.navigator.setNavigator(self.limit,self.offset,self.address,self.rowcount)


    def setLimit(self,config):
        """
        returns the limit according to the configuration or the default (100)

        - config : the limit of the configuration

        returns the limit of the configuration or 100
        """
        
        if config:
            
            return config
        
        else:

            return 100

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
        
        stripFields = ['limit','offset']

        if stripFields:

            for field in stripFields:

                path = re.sub("\&?" + field + "=\S+?(?:\&|$)", "", path, re.I)

        res = re.search("\&",path)

        if res:
            resq = re.search("\?",path)

            if not resq:
                path = re.sub("\&","?",path,1)

        return path

    def fieldNum(self,fields):
        """
        returns a hash associating the field names to the field numbers

        - fields : a list containing the field names

        returns the hash with fieldname=>fieldnumber pairs
        """
        
        fieldNum = {}

        for field in fields:

            fieldNum[field] = fields.index(field)

        return fieldNum
    

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


    def makeTableHeaders(self,name,uri,explain):
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

        ## for each of the cols that will be displayed
        for header in self.shown:
            ## get the name of it
            title = self.fields[header]
            explanation = ""
            uri = URI(self.address)
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
                thisSum.setSum(str(sum[title]))

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
                if not field >= len(self.shown) - len(self.extra):
                    text = line[field]
                else:
                    text = self.fields[field]


                newfield.setText(text)
                
                if self.uri.has_key(field):

                    uri = self.uri[field]

                    links = linkFinder.findall(uri)
                    if links:
                        for link in links:
                            to = line[self.fieldNum[link]]
                            uri = re.sub("\$"+link,to,uri)
                    newfield.setUri(uri)
                
                newline.append(newfield)

            newtable.append(newline)

        return newtable


## hvis det er mulig for uri-handler å ta imot to like, så angir
##dette motsatt sortering

