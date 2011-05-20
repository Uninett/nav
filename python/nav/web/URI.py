#
# Copyright (C) 2003 Norwegian University of Science and Technology
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
"""Classes for URI manipulation."""

import re, string
from urllib import unquote_plus as unquote
from urlparse import urlsplit

class URI:
    """
    An object representing a uri, that may replace parts of itself.
    """
    
    def __init__(self, uri):
        """
        Constructor of the URI class. Sets the original uri.

        - uri : the original uri that will be used

        """
        
        parsed_uri = urlsplit(uri)
        args_array = parsed_uri[3].split("&")
        if args_array:
            args = {}
            for arg in args_array:
                if arg:
                    keyvallist = arg.split("=")
                    if keyvallist[0]:
                        args[keyvallist[0]] = keyvallist[1]
            self.args = args
        else:
            self.args = []
        
        self.path = parsed_uri[2]
        

    
    def setArguments(self, fields, string):
        """
        Replaces the values of the arguments in the uri that has one of the keys listed in fields with string.

        - fields : a list of keys that will be removed or where the values will be replaced
        - string : the string used to override the old values

        """
        
        path = self.path

        if fields:
            count = 0
            
            for field in fields:

                if self.args.has_key(field):

                    count += 1
                    self.args[field] = string

            if not count:

                self.args[fields[0]] = string

    def make(self):

        uri = self.path

        args = []
        for arg, val in self.args.items():

            args.append(arg+"="+val)

        args = string.join(args,"&")

        if args:

            uri += "?"+args

        return uri

    def get(self, var):

        if self.args.has_key(var):
            return unquote(self.args[var])
        else:
            return
