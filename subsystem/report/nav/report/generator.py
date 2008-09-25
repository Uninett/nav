# -*- coding: utf-8 -*-
# $Id: Generator.py 3839 2007-01-29 15:53:21Z mortenv $
#
# Copyright 2003-2005 Norwegian University of Science and Technology
# Copyright 2008 UNINETT AS
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
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
#          Jørgen Abrahamsen <jorgen.abrahamsen@uninett.no>
#

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

    def __init__(self):

        self.config = None
        self.answer = None
        self.sql = ""

    def makeReport(self,reportName,configFile,configFileLocal,uri,dbresult):
        """
        Makes a report

        - reportName      : the name of the report that will be represented
        - configFile      : the configuration file where the definition resides
        - configFileLocal : the local configuration file where changes to the default definition resides
        - uri             : the request from the user as a uri

        returns a formatted report object instance or 0
        """

        parsed_uri = urlsplit(uri)
        args = parsed_uri[3]

        configParser = ConfigParser(configFile,configFileLocal)
        parseOK = configParser.parseReport(reportName)

        config = configParser.configuration

        adv = 0
        if parseOK:
            argumentParser = ArgumentParser(config)
            argumentHash = argumentParser.parseArguments(args)

            if argumentHash.has_key("adv"):
                if argumentHash["adv"]:
                    adv = 1
                del argumentHash["adv"]

            (contents,neg,operator) = argumentParser.parseQuery(argumentHash)

            # Check if there exists a database result for the query
            if dbresult != None:
                formatted = Report(config,dbresult,uri)
                formatted.titlebar = reportName + " - report - NAV"

                return (formatted,contents,neg,operator,adv,None)

            else:
                answer = DatabaseResult(config)
                self.sql = answer.sql

                formatted = Report(config,answer,uri)
                formatted.titlebar = reportName + " - report - NAV"

                return (formatted,contents,neg,operator,adv,answer)

        else:
            return (0,None,None,None,adv,None)



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
            if report.header and report.description:
                r = ReportListElement(rep,report.header,report.description)
                self.reports.append(r.getReportListElement())
            else:
                r = ReportListElement(rep,None,None)
                self.reports.append(r.getReportListElement())

    def getReportList(self):
        return self.reports


class ReportListElement:

    def __init__(self,key,description,title=""):

        self.key = key
        self.title = title
        self.description = description

    def getReportListElement(self):

        if self.title and self.description:
            return (self.title,self.key,self.description)

        else:
            return (self.key,self.key,self.key)


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
            if reResultLocal:
                # Local report config overloads default report config.
                self.parseConfiguration(reResult.group(1))
                self.parseConfiguration(reResultLocal.group(1))
                return 1

            self.parseConfiguration(reResult.group(1))
            return 1
        else:
            return 0


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
                config.setQuery(value)
            elif key == "overskrift" or key == "header" or key == "title":
                config.header = value
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
        self.orig_sql = ""
        self.sql = None
        self.header = ""
        self.description = ""
        self.orderBy = []
        self.hidden = []
        self.extra = []
        self.sum = []
        self.name = {}
        self.uri = {}
        self.explain = {}
        self.where = []
        self.offset = ""
        self.limit = ""
        self.sql_from = ""
        self.sql_where = []
        self.sql_group = []
        self.sql_order = []
        self.sql_limit = []
        self.sql_offset = []
        self.sql_select_orig = []


    def setQuery(self,sql):
        self.orig_sql = sql
        self.sql = sql
        (self.sql_select,self.sql_select_orig) = self.parse_select(sql)
        self.sql_from = self.parse_from(sql)
        self.sql_where = self.parse_where(sql)
        self.sql_group = self.parse_group(sql)
        self.sql_order = self.parse_order(sql)
        self.sql_limit = self.parse_limit(sql)
        self.sql_offset = self.parse_offset(sql)

    def makeSQL(self):
        sql = self.selectstring() + self.fromstring() + self.wherestring() + self.groupstring() + self.orderstring()
        return sql

    def fromstring(self):
        return " FROM " + self.sql_from

    def selectstring(self,selectFields = []):
        if not selectFields:
            selectFields = self.sql_select_orig
        if not isinstance(selectFields,str):
            selectFields = string.join(selectFields,",")
        return "SELECT " + selectFields

    def wherestring(self):
        where = self.sql_where + self.where
        if where:
            alias_remover = re.compile("(.+)\s+AS\s+\S+",re.I)
            where = [alias_remover.sub("\g<1>",word) for word in where]
            return " WHERE " + string.join(where," AND ")
        else:
            return ""

    def groupstring(self):
        if self.sql_group:
            return " GROUP BY " + string.join(self.sql_group,",")
        else:
            return ""

    def orderstring(self):
        sort = self.orderBy + self.sql_order
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

    def rstrip(self,string):
        """Returns the last \w-portion of the string"""
        last = re.search("(\w+)\W*?$",string)
        last = last.group(1)
        return last.strip()

    def parse_select(self,sql):
        select = re.search("SELECT\s*(.*?)\s*FROM\s+",sql,re.I|re.S|re.M)
        if select:
            select = select.group(1)

            # Split properly (e.i. not in the middle of ( ) )
            last = 0
            k = 0
            elem = []
            for i in range(len(select)):
                if select[i] == '(': k += 1
                elif select[i] == ')': k -= 1
                elif k == 0 and select[i] == ',':
                    if (last < i):
                        elem.append(select[last:i]);
                    last = i+1
            if last < len(select):
                elem.append(select[last:len(select)])
            select = elem

            return ([ self.rstrip(word) for word in select],[a.strip() for a in select])
        else:
            return ([],[])

    def parse_from(self,sql):
        str = ''
        for elem in sql: str += elem
        fromm = self.findInLevel(0, str, 'FROM', ['WHERE','ORDER','GROUP','LIMIT','OFFSET'])
        if fromm:
            return fromm
        return ""

    def parse_where(self,sql):
        str = ''
        for elem in sql: str += elem
        where = self.findInLevel(0, str, 'WHERE', ['ORDER','GROUP','LIMIT','OFFSET'])
        if where:
            return [where]
        return []

    def parse_group(self,sql):
        str = ''
        for elem in sql: str += elem
        group = self.findInLevel(0, str, 'GROUP BY', ['ORDER','LIMIT','OFFSET'])
        if group:
            return [group]
        return []

    def parse_order(self,sql):
        str = ''
        for elem in sql: str += elem
        order = self.findInLevel(0, str, 'ORDER BY', ['GROUP BY','LIMIT','OFFSET'])
        if order:
            return [order]
        return []

    def parse_limit(self,sql):
        str = ''
        for elem in sql: str += elem
        limit = self.findInLevel(0, str, 'LIMIT', ['OFFSET'])
        if limit:
            return limit
        return ""

    def parse_offset(self,sql):
        str = ''
        for elem in sql: str += elem
        offset = self.findInLevel(0, str, 'OFFSET', [])
        if offset:
            return offset
        return ""

    def strAtIdx(self, idx, str, set):
        for elem in set:
            if str[idx:idx+len(elem)].lower() == elem.lower():
                return 1
        return 0

    def findInLevel(self, level, str, begin, end):
        last = 0
        k = 0
        elem = []
        beginIdx = -1
        endLev = -1
        if (level == 0): endLev = len(str)
        for i in xrange(len(str)):
            if str[i] == '(': k += 1
            elif str[i] == ')':
                if k == level: endLev = i
                k -= 1
            elif k == level:
                if beginIdx == -1 and self.strAtIdx(i, str, [begin]):
                    beginIdx = i + len(begin)
                elif beginIdx >= 0 and self.strAtIdx(i, str, end):
                    return str[beginIdx:i]
        if beginIdx >= 0 and endLev >= 0: return str[beginIdx:endLev]
