#!/usr/bin/env python

import re,string

class ArgumentParser:
    """
    Handler of the uri arguments
    """

    def __init__(self,configuration):
        """
        Initializes the configuration
        """

        self.configuration = configuration

    def parseQuery(self,query):
        """
        Parses the arguments of the uri, and modifies the ReportConfig-object configuration

        - query : a hash representing the argument-part of the uri

        """
        
        ## config is the configuration obtained from the configuration file
        config = self.configuration

        for key,value in query.items():

            if key == "sql" or key == "query":
                #error("Access to make SQL-querys permitted")
                pass
            elif key == "overskrift" or key == "header":
                config.header = value
            elif key == "order_by" or key == "sort":
                config.orderBy = string.split(value,",") + config.orderBy
            elif key == "skjul" or key == "hidden" or key == "hide":
                config.hidden.extend(string.split(value,","))
            elif key == "ekstra" or key == "extra":
                config.extra.extend(string.split(value,","))
            elif key == "sum" or key == "total":
                config.sum.extend(string.split(value,","))
            elif key == "offset":
                config.offset = value
            elif key == "limit":
                config.limit = value
            else:
                reObject = re.compile("^(?P<group>\S+?)_(?P<groupkey>\S+?)$")
                reResult = reObject.search(key)

                if reResult:
                    if reResult.group('group') == "navn" or reResult.group('group') == "name":
                        config.name[reResult.group('groupkey')] = value
                    elif reResult.group('group') == "url" or reResult.group('group') == "uri":
                        config.uri[reResult.group('groupkey')] = value
                    elif reResult.group('group') == "forklar" or reResult.group('group') == "explain" or reResult.group('group') == "description":
                        config.explain[reResult.group('groupkey')] = value
                else:
                    config.where.append(key + "='" + value + "'")

         
    def parseArguments(self,args):
        """
        Parses the argument part of the uri and makes a hash representation of it

        - args : the argument part of the uri

        returns a hash representing the arguments in the uri
        """
        
        queryString = {}

        if args:

            for arg in args.split("&"):

                if arg:
                    (key,val) = arg.split("=")
                    queryString[key] = val

        return queryString
    
