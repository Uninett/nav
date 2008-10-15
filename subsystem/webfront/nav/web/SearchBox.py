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
Contains a class for a searchbox
"""

import nav.db.manage,re
from socket import gethostbyaddr,gaierror

# Class for displaying a search box
class SearchBox:
    formCname = 'sb_form'
    inputCname = 'sb_input'
    typeCname = 'sb_searchtype'
    submitCname = 'sb_submit'
    submitText = 'Search'

    method = 'post'
    title = 'Search'
    inputSize = '10'

    def __init__(self,req,help,title=None,form=True):
        if title:
            self.title = title

        self.help = help
        self.error = None
        self.result = None
        self.searches = {}
        self.form = form
    
        self.selected = None
        if req.form.has_key(self.typeCname):
            self.selected = req.form[self.typeCname]

    def addSearch(self,sid,name,table,columns,where=None,like=None,call=None):
        " Adds a new search type to the searchbox "
        self.searches[sid] = (name,table,columns,where,like,call)

    def getQuery(self,req):
        " Returns the query entered into the searchbox "
        result = None
        if req.form.has_key(self.inputCname):
            if len(req.form[self.inputCname]):
                result = req.form[self.inputCname]
        return result 

    def getResults(self,req):
        " Returns the results from the source as a dict "
        results = {}
        for sid,options in self.searches.items():
            name,table,columns,where,like,call = options
            for key,columns in columns.items():
                results[key] = []

        validSearch = True
        if req.form.has_key(self.typeCname):
            for sid,options in self.searches.items():
                if req.form[self.typeCname] == sid:
                    name,table,columns,where,like,call = options
                    db = getattr(nav.db.manage,table)

                    if req.form.has_key(self.inputCname):
                        input = req.form[self.inputCname]
                        if where:
                            where = where % (input,)
                        elif like:
                            where = like + " LIKE '%" + input + "%'" 
                        elif call:
                            (success,val) = call(input)
                            if success:
                                where = val
                            else:
                                self.error = val
                                validSearch = False

                    if validSearch:
                        entryList = db.getAll(where=where)
                        # Status messages
                        if len(entryList):
                            if len(entryList) == 1:
                                self.result = "1 match"     
                            else:
                                self.result = "%d matches" % \
                                              (len(entryList),)
                        else:
                            self.error = "No matches"

                        for entry in entryList:
                            for key,column in columns.items():
                                value = entry
                                if type(value) == type(None):
                                    continue
                                for c in column:
                                    # This must be done recursively
                                    # allowing to specify
                                    # netbox.catid as valid column
                                    for i in c.split('.'):
                                        try:
                                            value = getattr(value,i)
                                        except:
                                            pass
                                if type(value) not in (list, str, int):
                                    # a bit ugly, but we must ensure that we use the
                                    # id field
                                    results[key].append(value._getID()[0])
                                else:
                                    results[key].append(str(value))
        return results


# Callback function for SearchBoxes with a sysname/ip search
# Checks if input is an ip or a hostname, returns a where clause
def checkIP(input):
    result = re.match('^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})',input)
    if result:
        # this is an ip address
        try:
            gethostbyaddr(input)
        except gaierror:
            return (False,"Invalid IP")
        except:
            # No error if there is no dns record for this ip for example
            pass
        #for octet in result.groups():
        #    if (int(octet) > 255) or (int(octet) < 0):
        #        return(False,"Invalid IP")
        where = "ip='%s'" % (input,)
    else:
        # this is a hostname
        where = "sysname like '%" + input + "%'"
    return (True,where)
