#!/usr/bin/env python

import re,string
from urlparse import urlsplit
from urllib import unquote_plus
from DatabaseResult import DatabaseResult
from Report import Report

class Generator:
    """
    The maker and controller of the generating of a report
    """

    def __init__(self):

        self.config = None
        self.answer = None
        self.sql = ""
        self.hei = ""
    
    def makeReport(self,reportName,configFile,uri):
        """
        Makes a report

        - reportName : the name of the report that will be represented
        - configFile : the configuration file where the definittion resides
        - uri        : the request from the user as a uri

        returns a formatted report object instance or 0
        """
        
        parsed_uri = urlsplit(uri)
        args = parsed_uri[3]
            
        configParser = ConfigParser(configFile)
        config = configParser.configuration
        parseOK = configParser.parseReport(reportName)

        adv = 0
        if parseOK:
            argumentParser = ArgumentParser(config)
            argumentHash = argumentParser.parseArguments(args)
            if argumentHash.has_key("adv"):
                if argumentHash["adv"]:
                    adv = 1
                del argumentHash["adv"]
            (contents,neg,operator) = argumentParser.parseQuery(argumentHash)

            answer = DatabaseResult(config)
            #self.hei = answer.error
            self.sql = answer.sql

            formatted = Report(config,answer,uri)
            formatted.titlebar = reportName + " - report - NAV"
        
            return (formatted,contents,neg,operator,adv)

        else:

            return (0,None,None,None,adv)



class ReportList:

    def __init__(self,configurationFile):

        self.reports = []

        reportRe = re.compile("^\s*(\S+)\s*\{.*?\}$",re.M|re.S|re.I)
        fileContents = file(configurationFile).read()
        list = reportRe.findall(fileContents)

        configParser = ConfigParser(configurationFile)

        for rep in list:
            
            configParser.parseReport(rep)
            report = configParser.configuration
            #raise KeyError, report.header
            if report.header:
                r = ReportListElement(rep,report.header)
                self.reports.append(r.getReportListElement())
            else:
                r = ReportListElement(rep)
                self.reports.append(r.getReportListElement())
            
    def getReportList(self):
        return self.reports


class ReportListElement:

    def __init__(self,key,title=""):

        self.key = key
        self.title = title

    def getReportListElement(self):

        if self.title:
            return (self.title,self.key)

        else:
            return (self.key,self.key)


class ConfigParser:
    """
    Loads a configuration file, parses the contents, and returns the results as a ReportConfig object instance
    """

    def __init__(self,configFile):
        """
        Loads the configuration file
        """
        
        self.config = file(configFile).read()
        self.configuration = ReportConfig()
        
        
    def parseReport(self,reportName):
        """
        Parses the configuration file and returns a Report object
        according to the reportName.

        - reportName : the name of the report, tells which part of configuration file to use when making a ReportConfig

        returns 1 when there was a report with that name, 0 otherwise

        the access methods will probably fit here
        """
        
        reportRe = re.compile("^\s*"+reportName+"\s*\{(.*?)\}$",re.M|re.S|re.I)
        reResult = reportRe.search(self.config)
        
        if reResult:
            self.parseConfiguration(reResult.group(1))
            return 1
        else:
            return 0


    def parseConfiguration(self,reportConfiguration):
        """
        Parses the right portion of the configuration and builds a ReportConfig object, stone by stone.

        - reportConfiguration : the part of the configuration to build the configuration from

        """

        configurationRe = re.compile("^\s*\$(\S*)\s*\=\s*\"(.*?)\"\;?",re.M|re.S)
        reResult = configurationRe.findall(reportConfiguration)

        config = self.configuration

        for line in reResult:

            key = line[0]
            value = line[1]

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
        self.hei = ""

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
                    if reResult.group('group') == "navn" or reResult.group('group') == "name":
                        config.name[reResult.group('groupkey')] = value
                    elif reResult.group('group') == "url" or reResult.group('group') == "uri":
                        config.uri[reResult.group('groupkey')] = value
                    elif reResult.group('group') == "forklar" or reResult.group('group') == "explain" or reResult.group('group') == "description":
                        config.explain[reResult.group('groupkey')] = value
                    elif reResult.group('groupkey') == "not":
                        nott[reResult.group('group')] = value
                    elif reResult.group('groupkey') == "op":
                        operator[reResult.group('group')] = value
                else:
                    if value and not key == "r4g3n53nd":
                        fields[key] = unquote_plus(value)
                

        for key,value in fields.items():

            if not operator.has_key(key):
                operator[key] = "eq"

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
                        value = "'" + re.sub("\*","%",value) + "'"
                    elif operator[key] == "gt":
                        if neg:
                            operat = "<="
                            neg = ""
                        else:
                            operat = ">"
                        value = self.intstr(value)
                            
                    elif operator[key] == "geq":
                        if neg:
                            operat = "lt"
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
        #try:
        #    arg = int(arg)
        #    arg = str(arg)
        #except ValueError:
        arg = "'" + arg + "'"
        return arg


class ReportConfig:

    def __init__(self):
        self.orig_sql = ""
        self.sql = None
        self.header = ""
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
        sql = self.selectstring() + self.fromstring() + self.wherestring() + self.groupstring() + self.orderstring() + self.limitoffsetstring()
        return sql

    def makeTotalSQL(self):
        #select = self.sql_select_orig[0]

        #skulle gjerne begrenset dette søket, så det ikke tok sånn tid, ved å bruke select deklarert rett over i selectstring().
        sql = self.selectstring() + self.fromstring() + self.wherestring() + self.groupstring()
        return sql

    def makeSumSQL(self):
        ## jukser her! count != sum --> ikke nå lenger
        
        sum = []
        for s in self.sum:
            s = "sum("+s+")"
            sum.append(s)
            #sumString = string.join(self.sum,",")
        sql = self.selectstring(sum) + self.fromstring() + self.wherestring()# + self.groupstring()
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

    def limitoffsetstring(self):
        if self.offset:
            offset = self.offset
        elif self.sql_offset:
            offset = sql_offset
        else:
            offset = "0"
        
        if self.limit:
            limit = self.limit
        elif self.sql_limit:
            limit = self.sql_limit
        else:
            limit = "100"
        return " LIMIT " + limit + " OFFSET " + offset
       
 
    def rstrip(self,string):
        """Returns the last \w-portion of the string"""
        last = re.search("(\w+)\W*?$",string)
        last = last.group(1)
        return last.strip()

    def parse_select(self,sql):
        select = re.search("SELECT\s*(.*)\s*FROM\s+",sql,re.I|re.S|re.M)
        if select:
            select = select.group(1)
            select = select.split(",")
            return ([ self.rstrip(word) for word in select],[a.strip() for a in select])
        else:
            return ([],[])

    def parse_from(self,sql):
        fromm = re.search("FROM\s*(.*?)\s*(?:WHERE|ORDER|GROUP|LIMIT|OFFSET|$)",sql,re.I|re.S|re.M)
        if fromm:
            return fromm.group(1)
        else:
            return ""

    def parse_where(self,sql):
        where = re.search("WHERE\s*(.*?)\s*(?:ORDER|GROUP|LIMIT|OFFSET|$)",sql,re.I|re.S)
        if where:
            where = where.group(1)
            where = where.split(",")
            return where
        else:
            return []

    def parse_group(self,sql):
        group = re.search("GROUP\ BY\s*(.*?)\s*(?:ORDER|LIMIT|OFFSET|$)",sql,re.I|re.S)
        if group:
            group = group.group(1)
            group = group.split(",")
            return group
        else:
            return []

    def parse_order(self,sql):
        order = re.search("ORDER\ BY\s*(.*?)\s*(?:GROUP|LIMIT|OFFSET|$)",sql,re.I|re.S)
        if order:
            order = order.group(1)
            order = order.split(",")
            return order
        else:
            return []

    def parse_limit(self,sql):
        limit = re.search("LIMIT\s*(.*?)\s*(?:OFFSET|$)",sql,re.I|re.S)
        if limit:
            limit = limit.group(1)
            return limit
        else:
            return ""

    def parse_offset(self,sql):
        offset = re.search("OFFSET\s*(.*?)\s*$",sql,re.I|re.S)
        if offset:
            offset = offset.group(1)
            return offset
        else:
            return ""

