# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2005 Norwegian University of Science and Technology
# Copyright (C) 2008 UNINETT AS
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
"""Generates the query and makes the report."""

from nav.report.dbresult import DatabaseResult
from nav.report.report import Report
from urllib import unquote_plus
from urlparse import urlsplit
import nav.db
import re,string


class Generator:
    """
    The maker and controller of the generating of a report
    """

    def makeReport(self,reportName,configFile,configFileLocal,uri,config,dbresult):
        """
        Makes a report

        - reportName      : the name of the report that will be represented
        - configFile      : the configuration file where the definition resides
        - configFileLocal : the local configuration file where changes to the default definition resides
        - uri             : the request from the user as a uri
        - config          : the parsed configuration object, if cached
        - dbresult        : the database result, if cached

        Returns a formatted report object and search parameters. Also returns a
        parsed ReportConfig object and a DatabaseResult object to be cached.
        """

        parsed_uri = urlsplit(uri)
        args = parsed_uri[3]
        adv = 0

        if not config:
            configParser = ConfigParser(configFile,configFileLocal)
            parseOK = configParser.parseReport(reportName)
            config = configParser.configuration
            if not parseOK:
                return (0,None,None,None,None,None,None)

        argumentParser = ArgumentParser(config)
        argumentHash = argumentParser.parseArguments(args)
        
        # Remove non-query arguments
        if argumentHash.has_key("export"):
            del argumentHash["export"]

        if argumentHash.has_key("exportcsv"):
            del argumentHash["exportcsv"]
            # Export *everything* in CSV file
            argumentHash["offset"] = 0
            argumentHash["limit"] = 0

        if argumentHash.has_key("adv"):
            if argumentHash["adv"]:
                adv = 1
            del argumentHash["adv"]

        (contents,neg,operator) = argumentParser.parseQuery(argumentHash)

        # Check if there exists a cached database result for this query
        if dbresult: # Cached
            report = Report(config,dbresult,uri)
            report.titlebar = reportName + " - report - NAV"

            return (report,contents,neg,operator,adv)

        else: # Not cached
            dbresult = DatabaseResult(config)
            self.sql = dbresult.sql

            report = Report(config,dbresult,uri)
            report.titlebar = reportName + " - report - NAV"

            return (report,contents,neg,operator,adv,config,dbresult)


class ReportList:

    def __init__(self,configFile):

        self.reports = []

        reportRe = re.compile("^\s*(\S+)\s*\{(.*?)\}$",re.M|re.S|re.I)
        fileContents = file(configFile).read()
        list = reportRe.findall(fileContents)

        configParser = ConfigParser(configFile,None)

        for rep in list:
            configtext = rep[1]
            rep = rep[0]
            
            configParser.parseConfiguration(configtext)
            report = configParser.configuration

            if report.title != '' and report.description != '':
                self.reports.append((rep, report.title, report.description))
            
            elif report.title != '':
                self.reports.append((rep, report.title, None))

            elif report.description != '':
                self.reports.append((rep, rep, report.description))

            else:
                self.reports.append((rep, rep, None))

    def getReportList(self):
        return self.reports



class ConfigParser:
    """
    Loads the configuration files, parses the contents - the local
    configuration the default, and returns the results as a ReportConfig object
    instance
    """

    def __init__(self,configFile,configFileLocal):
        """
        Loads the configuration files
        """

        self.configFile = configFile
        self.configFileLocal = configFileLocal
        self.config = None
        self.configLocal = None
        self.configuration = ReportConfig()


    def parseReport(self,reportName):
        """
        Parses the configuration file and returns a Report object
        according to the reportName.

        - reportName : the name of the report, tells which part of configuration files to use when making a ReportConfig

        returns 1 when there was a report with that name, 0 otherwise

        the access methods will probably fit here
        """

        if self.config is None:
            self.config = file(self.configFile).read()
            self.configLocal = file(self.configFileLocal).read()
        reportRe = re.compile("^\s*"+reportName+"\s*\{(.*?)\}$",re.M|re.S|re.I)
        reResult = reportRe.search(self.config)
        reResultLocal = reportRe.search(self.configLocal)

        if reResult:
            self.parseConfiguration(reResult.group(1))
        if reResultLocal:
            # Local report config overloads default report config.
            self.parseConfiguration(reResultLocal.group(1))

        if reResult or reResultLocal:
            return True
        
        else:
            return False


    def parseConfiguration(self,reportConfig):
        """
        Parses the right portion of the configuration and builds a ReportConfig object, stone by stone.

        - reportConfig : the part of the configuration to build the configuration from

        """

        configurationRe = re.compile("^\s*\$(\S*)\s*\=\s*\"(.*?)\"\;?",re.M|re.S)
        reResult = configurationRe.findall(reportConfig)

        config = self.configuration

        for line in reResult:

            key = line[0]
            value = line[1].replace('\n',' ').strip()

            if key == "sql" or key == "query":
                config.sql = value
            elif key == "title":
                config.title = value
            elif key == "order_by" or key == "sort":
                config.orderBy = string.split(value,",") + config.orderBy
            elif key == "skjul" or key == "hidden" or key == "hide":
                config.hidden.extend(string.split(value,","))
            elif key == "ekstra" or key == "extra":
                config.extra.extend(string.split(value,","))
            elif key == "sum" or key == "total":
                config.sum.extend(string.split(value,","))
            elif key == "description":
                config.description = value
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
                    config.where.append(key + "=" + value)

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
        fields = {}
        nott = {}
        operator = {}
        safere = re.compile("(select|drop|update|delete).*(from|where)",re.I)

        for key,value in query.items():

            if key == "sql" or key == "query":
                #error("Access to make SQL-querys permitted")
                pass
            elif key == "title":
                config.title = value
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
                    g = unquote_plus(reResult.group('group'))
                    gk = unquote_plus(reResult.group('groupkey'))
                    if g == "navn" or g == "name":
                        config.name[gk] = value
                    elif g == "url" or g == "uri":
                        config.uri[gk] = value
                    elif g == "forklar" or g == "explain" or g == "description":
                        config.explain[gk] = value
                    elif g == "not":
                        nott[gk] = value
                    elif g == "op":
                        operator[gk] = value
                    else:
                        reResult = None

                if not reResult:
                    if value:
                        fields[unquote_plus(key)] = unquote_plus(value)

        for key,value in fields.items():

            if not operator.has_key(key):
                operator[key] = "eq"
            # Set a default operator
            operat = "="

            if nott.has_key(key):
                neg = "not "
            else:
                neg = ""

            if value == "null":
                if neg:
                    operat = "is not"
                    neg = ""
                else:
                    operat = "is"
            else:
                if safere.search(value):
                    config.error = "You are not allowed to make advanced sql terms"
                else:
                    if operator[key] == "eq":
                        if neg:
                            operat = "<>"
                            neg = ""
                        else:
                            operat = "="
                        value = self.intstr(value)
                    elif operator[key] == "like":
                        operat = "ilike"
                        value = self.intstr(value.replace("*","%"))
                    elif operator[key] == "gt":
                        if neg:
                            operat = "<="
                            neg = ""
                        else:
                            operat = ">"
                        value = self.intstr(value)

                    elif operator[key] == "geq":
                        if neg:
                            operat = "<"
                            neg = ""
                        else:
                            operat = ">="
                        value = self.intstr(value)
                    elif operator[key] == "lt":
                        if neg:
                            operat = ">="
                            neg = ""
                        else:
                            operat = "<"
                        value = self.intstr(value)
                    elif operator[key] == "leq":
                        if neg:
                            operat = ">"
                            neg = ""
                        else:
                            operat = "<="
                        value = self.intstr(value)
                    elif operator[key] == "in":
                        operat = "in"
                        inlist = value.split(",")
                        if inlist:
                            value = "(" + ",".join([ self.intstr(a.strip()) for a in inlist]) + ")"
                        else:
                            config.error = "The arguments to 'in' must be comma separated"

                    elif operator[key] == "between":
                        operat = "between"
                        between = value.split(",")
                        if not len(between) == 2:
                            between = value.split(":")
                        if len(between) == 2:
                            value = self.intstr(between[0]) + " and " + self.intstr(between[1])
                        else:
                            config.error = "The arguments to 'between' must be comma separated"

            config.where.append(key+" "+neg+operat+" "+value)

        return (fields,nott,operator)

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


    def intstr(self,arg):
        return nav.db.escape(arg)


class ReportConfig:

    def __init__(self):
        self.description = ""
        self.explain = {}
        self.extra = []
        self.hidden = []
        self.limit = ""
        self.name = {}
        self.offset = ""
        self.orderBy = []
        self.sql = None
        self.sql_select = []
        self.sum = []
        self.title = ""
        self.uri = {}
        self.where = []

    def makeSQL(self):
        # Group bys are not configured nor supported through the web interface - therefore dropped.
        sql = "SELECT * FROM (" + self.sql + ") AS foo " + self.wherestring() + self.orderstring()
        return sql

    def wherestring(self):
        where = self.where
        if where:
            alias_remover = re.compile("(.+)\s+AS\s+\S+",re.I)
            where = [alias_remover.sub("\g<1>",word) for word in where]
            return " WHERE " + string.join(where," AND ")
        else:
            return ""

    def orderstring(self):
        sort = self.orderBy
        if sort:
            for s in sort:
                if s.startswith("-"):
                    index = sort.index(s)
                    s = s.replace("-","")
                    s += " DESC"
                    sort[index] = s
            return " ORDER BY " + string.join(sort,",")
        else:
            return ""
