#!/usr/bin/env python

import re,string

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
        select = self.sql_select[0]
        
        sql = self.selectstring(select) + self.fromstring() + self.wherestring() + self.groupstring()
        return sql

    def makeSumSQL(self):
        ## jukser her! count != sum
        
        sum = []
        for s in self.sum:
            s = "count("+s+")"
            sum.append(s)
            #sumString = string.join(self.sum,",")
        sql = self.selectstring(sum) + self.fromstring() + self.wherestring() + self.groupstring()
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
        if self.orderBy + self.sql_order:
            return " ORDER BY " + string.join(self.orderBy + self.sql_order,",")
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
            limit = "200"
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
            return ([ self.rstrip(word) for word in select],select)
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

    
