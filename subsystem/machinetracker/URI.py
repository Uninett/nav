#!/usr/bin/env python

import re,string
from urlparse import urlsplit

class URI:
    """
    An object representing a uri, that may replace parts of itself.
    """
    
    def __init__(self,uri):
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
        

    
    def setArguments(self,fields,string):
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
        for arg,val in self.args.items():

            args.append(arg+"="+val)

        args = string.join(args,"&")

        if args:

            uri += "?"+args

        return uri

    def get(self,var):

        if self.args.has_key(var):
            return self.args[var]
        else:
            return
