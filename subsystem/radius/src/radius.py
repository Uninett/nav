# -*- coding: utf-8 -*-
#
# Copyright 2008 University of Tromsø 
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
# Authors: Roger Kristiansen <roger.kristiansen@gmail.com>
#          Kai Arne Bjørnenak <kai.bjornenak@cc.uit.no>
#

import time
import re
import nav.path
import os.path
from nav.web.URI import URI
from nav import db
from radius_config import *
from socket import gethostbyname_ex, gaierror
from mod_python import apache

connection = db.getConnection(DB_USER, DB)
database = connection.cursor()


def handler(req):

    # Mod_python caches these modules if we just import them
    # like we would usually do. Enable the DEBUG flag during 
    # development to get around this.
    
    if DEBUG:
        AcctSearchTemplate = apache.import_module(
            "nav.web.templates.AcctSearchTemplate", autoreload = 1)
        AcctDetailTemplate = apache.import_module(
            "nav.web.templates.AcctDetailTemplate", autoreload = 1)
        AcctChartsTemplate = apache.import_module(
            "nav.web.templates.AcctChartsTemplate", autoreload = 1)
        LogTemplate = apache.import_module(
            "nav.web.templates.LogTemplate", autoreload = 1)
        LogDetailTemplate = apache.import_module(
            "nav.web.templates.LogDetailTemplate", autoreload = 1)
        radiuslib = apache.import_module("radiuslib", autoreload = 1)
    

    from nav.web.templates.AcctSearchTemplate import AcctSearchTemplate
    from nav.web.templates.AcctDetailTemplate import AcctDetailTemplate
    from nav.web.templates.AcctChartsTemplate import AcctChartsTemplate
    from nav.web.templates.LogTemplate import LogTemplate
    from nav.web.templates.LogDetailTemplate import LogDetailTemplate
    from radiuslib import makeTimeHumanReadable, makeBytesHumanReadable

    args = URI(req.unparsed_uri) 

    # Get basename and section part of the URI
    baseurl = ""
    section = ""
    s = re.search("(?P<baseurl>\w+)\/(?P<section>\w+?)(?:\/$|\?|\&|$)",req.uri)
    if s:
        baseurl = s.group("baseurl")
        section = s.group("section")


    menu = []
    if nav.auth.hasPrivilege(req.session['user'],
                             "web_access", "/" + baseurl + "/" + "acctsearch"):
        menu.append({'link': 'acctsearch', 
                     'text': 'Accounting Log', 
                     'admin': False})
    if nav.auth.hasPrivilege(req.session['user'],
                             "web_access", "/" + baseurl + "/" + "acctcharts"):
        menu.append({'link': 'acctcharts', 
                     'text': 'Accounting Charts', 
                     'admin': False})
    if nav.auth.hasPrivilege(req.session['user'],
                             "web_access", "/" + baseurl + "/" + "logsearch"):
        menu.append({'link': 'logsearch', 
                     'text': 'Error Log', 
                     'admin': False})

    page = AcctSearchTemplate()
    page.menu = menu

    if section.lower() == "logsearch":
        page = LogTemplate()
        page.current = "logsearch"
        page.search = None
        page.error = None
        page.dbfields = LOG_SEARCHRESULTFIELDS #Infofields to display 
        page.menu = menu

        try:
            page.form = LogSearchForm(
                            args.get("searchstring"), 
                            args.get("searchtype"), 
                            args.get("logentrytype"), 
                            args.get("timemode"), 
                            args.get("timestamp"), 
                            args.get("timestampslack"), 
                            args.get("hours"), 
                            args.get("sortfield"),
                            args.get("sortorder")
                                )
    
            page.form.checkInput()

            if args.get("send"):
                query = LogSearchQuery(
                            page.form.searchstring, 
                            page.form.searchtype, 
                            page.form.logentrytype, 
                            page.form.timemode, 
                            page.form.timestamp, 
                            page.form.timestampslack, 
                            page.form.hours, 
                            page.form.sortfield, 
                            page.form.sortorder
                                )
                page.search = query
                page.search.loadTable()

        except UserInputSyntaxWarning, e:
            page.error = e 

    elif section.lower() == "logdetail":
        page = LogDetailTemplate()
        page.error = None
        page.menu = menu
        page.dbfields = LOG_DETAILFIELDS #Infofields to display 

        query = LogDetailQuery(args.get("id"))
        page.detailQuery = query
        page.detailQuery.loadTable()

    elif section.lower() == "acctdetail":
        page = AcctDetailTemplate()
        page.error = None
        page.menu = menu
        page.dbfields = ACCT_DETAILSFIELDS #Infofields to display 
        
        query = AcctDetailQuery(args.get("acctuniqueid"))
        page.detailQuery = query
        page.detailQuery.loadTable()

    elif section.lower() == "acctcharts":
        page = AcctChartsTemplate()
        page.current = "acctcharts"
        page.error = None
        page.menu = menu

        try:
            page.form = AcctChartForm( 
                                  args.get("overallchart"),
                                  args.get("uploadchart"),
                                  args.get("downloadchart"),
                                  args.get("days")
                                  )
            page.form.checkInput()

            page.sentChartQuery = None
            page.recvChartQuery = None
            page.sentrecvChartQuery = None

            if page.form.uploadchart:
                # Get the top uploaders
                query = AcctChartsQuery("sent", page.form.days)
                page.sentChartQuery = query
                page.sentChartQuery.loadTable()

            if page.form.downloadchart:
                # Get the top leechers
                query = AcctChartsQuery("recv", page.form.days)
                page.recvChartQuery = query
                page.recvChartQuery.loadTable()

            if page.form.overallchart:
                # Get the top overall bandwidth hogs
                query = AcctChartsQuery("sentrecv", page.form.days)
                page.sentrecvChartQuery = query
                page.sentrecvChartQuery.loadTable()

        except UserInputSyntaxWarning, e:
            page.error = e 

    else:
        page = AcctSearchTemplate()
        page.current = "acctsearch"
        if DEBUG: page.refreshCache()
        page.search = None
        page.error = None
        page.menu = menu

        page.dbfields = ACCT_SEARCHRESULTFIELDS #Infofields to display

        try:
            page.form = AcctSearchForm(
                            args.get("searchstring"), 
                            args.get("searchtype"), 
                            args.get("nasporttype"), 
                            args.get("timemode"), 
                            args.get("timestamp"), 
                            args.get("timestampslack"), 
                            args.get("days"), 
                            args.get("userdns"), 
                            args.get("nasdns"),
                            args.get("sortfield"),
                            args.get("sortorder")
                                )
            page.form.checkInput()

            if args.get("send"):
                query = AcctSearchQuery(
                            page.form.searchstring, 
                            page.form.searchtype, 
                            page.form.nasporttype, 
                            page.form.timemode, 
                            page.form.timestamp, 
                            page.form.timestampslack, 
                            page.form.days, 
                            page.form.userdns, 
                            page.form.nasdns, 
                            page.form.sortfield, 
                            page.form.sortorder
                                )
                page.search = query
                page.search.loadTable()
        
        except UserInputSyntaxWarning, e:
            page.error = e

#    connection.close()

    req.content_type = "text/html"
    req.send_http_header()
    req.write(page.respond())
    page.shutdown()
    return apache.OK


#
# General classes
#

class SQLQuery:
    """
    Superclass for other query classes.
    """

    def execute(self):
        database.execute(self.sqlQuery, self.sqlParameters)

        # Create tuple of dictionaries
        colnames = [t[0] for t in database.description]
        rows = [dict(zip(colnames, tup)) for tup in database.fetchall()]
        self.result = rows

    def getTable(self):
        pass

    def loadTable(self):
        self.table = self.getTable()


#
# Accounting related classes
#

class AcctSearchForm:
    """
    Takes input from search form and sets attributes. Offers a method to
    error check the input
    """

    searchstring=""
    searchtype=""
    nasporttype=""
    timemode=""
    timestamp=""
    timestampslack=""
    days=""
    userdns=""
    nasdns=""
    sortfield=""
    sortorder=""

    def __init__(self, searchstring, searchtype, nasporttype, timemode, timestamp, timestampslack, days, userdns, nasdns, sortfield, sortorder):
        """
        Set attributes
        """

        self.searchstring = searchstring 
        self.searchtype = searchtype
        self.nasporttype = nasporttype
        self.timemode = timemode
        self.timestamp = timestamp
        self.timestampslack = timestampslack
        self.days = days
        self.sortfield = sortfield
        self.sortorder = sortorder
        if userdns: self.userdns = userdns  # Don't inlude in instance
        if nasdns: self.nasdns = nasdns     # if checkbox not checked

    def checkInput(self):
        """
        Verify that the input has correct format.
        """

        if self.searchstring:
            # Leading or trailing whitespace is probably in there by 
            # mistake, so remove it.
            self.searchstring = self.searchstring.strip()
        else:
            # An empty Searchstring is no good
            raise EmptySearchstringWarning


        if self.timestamp:
            # Leading or trailing whitespace is probably in there by 
            # mistake, so remove it.
            self.timestamp = self.timestamp.strip()
            self.timestampslack = self.timestampslack.strip()

            if self.timemode == "timestamp":
                # Matches a date on the format "YYYY-MM-DD hh:mm"
                if not re.match("^(19|20)\d\d[-](0[1-9]|1[012])[-](0[1-9]|[12][0-9]|3[01])\ ([01][0-9]|[2][0-3])\:[0-5][0-9]$", self.timestamp):
                    raise TimestampSyntaxWarning
                
                if not re.match("^\d*$", self.timestampslack):
                    raise TimestampSlackSyntaxWarning

        if self.timemode == "days":
            # Leading or trailing whitespace is probably in there by 
            # mistake, so remove it.
            self.days = self.days.strip()

            # Match integers and floats
            if not re.match("(^\d+$)|(^\d+\.{1}\d+)", self.days):
                raise DaysSyntaxWarning


class AcctChartForm:
    """
    Takes input from the charts form and sets attributes. Offers a method to
    error check the input
    """

    def __init__(self, overallchart="", uploadchart="", downloadchart="", 
            days="7"):
        """
        Set attributes
        """
        self.days = days
        self.overallchart = overallchart
        self.downloadchart = downloadchart
        self.uploadchart = uploadchart

        # TODO: For some reason the default value for days doesn't seem to 
        # be working. Find out why.
        if not self.days:
            self.days = "7"

    def checkInput(self):
        """
        Verify that the input has correct format.
        """ 

        if self.days:
            self.days = self.days.strip()

            # Everything but integers and floats throws exception
            if not re.match("(^\d+$)|(^\d+\.{1}\d+)", self.days):
                raise DaysSyntaxWarning


class AcctChartsQuery(SQLQuery):
    """
    Get top bandwidth hogs for specified period, 

    Can generate SQL queries for top uploaders, top downloaders, and top
    overall bandwidth (ab)users
    """

    def __init__(self, chart, days="7", topx="10"):
        """
        Construct query

        Keyword arguments:
        chart       - "sent", "recv" or "sentrecv" for top upload, top
                      download and top overall, respectively. 
        days        - How many of the last days we want chart for
        topx        - Tells the query how many users to return (default 10).
        """

        if chart == "sent": field = "acctinputoctets" 
        if chart == "recv": field = "acctoutputoctets"
        if chart == "sentrecv": field = "acctoutputoctets+acctinputoctets"

        # TODO: for some reason the default value for days doesn't seem to
        # be working. Find out why.
        if not days: days = "7"

        """
        In this SQL query, we sum up some fields in the database according
        to what kind of chart we are making,
        
        Since freeradius (v1.0.4) has a tendency to insert some sessions
        twice in the database, we eliminate this in the nested select-query,
        by just working on entries with distinct acctuniqueid fields. The
        two entries should be pretty much identical anyway. By "pretty much
        identical", I mean exatcly identical, except for acctstarttime, 
        which probably differs by a few hundreds of a second, and doesn't
        make any real difference here anyway.
        """
        if chart == "sent" or chart == "recv" or chart == "sentrecv":

            self.sqlQuery = """
                    SELECT 
                    username, 
                    realm, 
                    CAST(SUM(%s) as BIGINT) AS sortfield,
                    CAST(SUM(acctsessiontime) AS BIGINT) as acctsessiontime,
                    SUM(%s) IS NULL as fieldisnull
                    FROM 
                        (SELECT DISTINCT 
                            acctuniqueid, 
                            acctinputoctets, 
                            acctoutputoctets, 
                            username, 
                            acctsessiontime, 
                            realm 
                            FROM %s 
                            WHERE acctstoptime > NOW()-interval '%s days')
                        as elminatedupes
                    GROUP BY username, realm 
                    ORDER BY fieldisnull, sortfield DESC
                    LIMIT %s
                    """ % (field, field, ACCT_TABLE, days, topx)

            # Fields we need escaped go here 
            self.sqlParameters = ()

    def getTable(self):
        """
        Execute the SQL query and return a list containing ResultRows.
        """
        self.execute()
        return self.result 



class AcctDetailQuery(SQLQuery):
    """
    Get all details about a specified session
    """

    def __init__(self, sessionid):
        """
        Construct SQL query

        Keyword arguments:
        sessionid   - ID of the session we want to get details on.
        """
        self.sessionid = sessionid

        self.sqlQuery = """SELECT 
                           acctuniqueid,
                           username,
                           realm,
                           nasipaddress,
                           nasporttype,
                           cisconasport,
                           acctstarttime,
                           acctstoptime,
                           acctsessiontime,
                           acctterminatecause,
                           acctinputoctets,
                           acctoutputoctets,
                           calledstationid,
                           callingstationid,
                           framedprotocol,
                           framedipaddress
                           FROM %s 
                           WHERE acctuniqueid = %%s
                        """ % (ACCT_TABLE)
        self.sqlParameters = (self.sessionid,)


    def getTable(self):
        self.execute()
        searchResult = self.result[0]
        return searchResult 





class AcctSearchQuery(SQLQuery):
    """
    Get search result
    """

    def __init__(self, searchstring, searchtype, nasporttype, timemode, 
            timestamp, timestampslack, days, userdns, nasdns, sortfield, 
            sortorder):
        """
        Construct search query from user input
        """

        # Make "*" wildcard character
        if searchstring:
            searchstring = searchstring.lower().replace("*","%")

        self.userdns = userdns
        self.nasdns = nasdns

        self.sqlQuery = """(SELECT
                        acctuniqueid,
                        username,
                        realm,
                        framedipaddress,
                        nasipaddress,
                        nasporttype,
                        acctstarttime,
                        acctstoptime,
                        acctsessiontime,
                        acctoutputoctets,
                        acctinputoctets
                        FROM %s 
                        """ % ACCT_TABLE

        if (searchstring and searchstring != "%") \
                or nasporttype \
                or timemode:
            self.sqlQuery += " WHERE"

        # Contains all parameters we want to escape
        self.sqlParameters = ()

        # Check what we are searching for. It's either a username, realm,
        # or an IP address/hostname. If searching for all users, skip this
        # where clause all together.
        if (searchtype == "username" or searchtype == "realm") \
                and searchstring != "%":
            self.sqlQuery += " LOWER(%s) LIKE %%s" % (searchtype)
            self.sqlParameters += (searchstring,)

        # Address
        if (searchtype == "framedipaddress" \
                or searchtype == "nasipaddress"):
            # Split search string into hostname and, if entered, cisco nas 
            # port.
            match = re.search("^(?P<host>[[a-zA-Z0-9\.\-]+)[\:\/]{0,1}(?P<swport>[\S]+){0,1}$", searchstring)
            # Get all ip addresses, if a hostname is entered
            try: 
                addressList = gethostbyname_ex(match.group("host"))[2]
            except (AttributeError, gaierror): 
                # AttributeError triggered when regexp found no match, and
                # thus is None
                raise IPAddressNotFoundWarning

            self.sqlQuery += " ("
            for address in addressList:
                self.sqlQuery += "%s = INET(%%s)" % (searchtype)
                self.sqlParameters += (address,)
                if address != addressList[-1]: 
                    self.sqlQuery += " OR "
            self.sqlQuery += ")"

            # Search for Cisco NAS port, if it has been entered
            if match.group("swport"):
                self.sqlQuery += " AND LOWER(cisconasport) = %s"
                self.sqlParameters += tuple(match.group("swport").lower().split())

               
        
        if searchtype == "iprange":
            if searchstring.find('%'):
                self.sqlQuery += " %s << %%s" % ('framedipaddress')
                self.sqlParameters += (searchstring,)
                
        

        if nasporttype:
            if nasporttype.lower() == "isdn": nasporttype = "ISDN"
            if nasporttype.lower() == "vpn": nasporttype = "Virtual"
            if nasporttype.lower() == "modem": nasporttype = "Async"
            if nasporttype.lower() == "dot1x": nasporttype = "Ethernet"
            else:
                if searchstring != "%":
                    self.sqlQuery += " AND "
            
                self.sqlQuery += " nasporttype = %s"
                self.sqlParameters += (nasporttype,)

       
        """
        Searching for entries in a specified time interval.

        This might be a bit confusing, so I'll try to explain..

        First, some notes about the accounting entries:
        1) All entries have a date+time in the 'acctstarttime' field.
        2) All entries does not necessarily have an entry in 'acctstoptime'
        3) All entries for sessions that have lasted longer than the
           re-authentication-interval, have an integer value in the
           'acctsessiontime' field.
        4) Since the date in 'acctstarttime' is actually just the time
           when freeradius received EITHER a Start message, or an Alive
           message with a Acct-Unique-Session-Id that wasn't in the
           database, a session can have started prior to the 'acctstarttime'
           Thus if 'acctstoptime' != NULL, we might have actually gotten a
           Stop message with an Acct-Session-Time that tells ut how long the
           session has really lasted. We can therefore extract the real
           starting time by subtracting 'acctsessiontime' from 
           'acctstoptime'
        5) To match entries for sessions that have not yet ended, we have to
           add 'acctsessiontime' to 'acctstarttime' 
           and see if the resulting time interval touches our search 
           interval.

        """

        if timemode:

            # If we have already specified some criteria, we need to AND 
            # it with the date search
            if self.sqlQuery.find("WHERE", 0, -5) != -1:
                self.sqlQuery += " AND "

            if timemode == "days":
                # Search for entries active from x*24 hours ago, until now.
                searchtime = float(days)*86400        
                searchstart = time.strftime(DATEFORMAT_SEARCH, \
                                time.localtime(time.time()-searchtime))
                # searchstop = time.strftime(DATEFORMAT_SEARCH, 
                # time.localtime(time.time()))
       
                # Ok, let's make this really hairy. We want to separate the
                # following clauses into two queries, which we then UNION
                # together. This is done to be able to utilize the indices.
                # For some reason postgres doesn't use the indices when we
                # OR all three of these clauses together.
                tmpWhereClause = ""
                tmpWhereClause += """ 
                    (
                    (   -- Finding sessions that ended within our interval
                        acctstoptime >= timestamp '%(searchstart)s'
                    ) OR (
                        -- Finding sessions that started within our interval
                        acctstarttime >= timestamp '%(searchstart)s')
                    )
                    )
                    UNION """ % {"searchstart": searchstart}
                self.sqlQuery += tmpWhereClause + self.sqlQuery
                self.sqlParameters += self.sqlParameters
                self.sqlQuery += """

                    (
                        -- Find sessions without acctstoptime, but where 
                        -- acctstarttime+acctsessiontime is in our interval
                        (acctstoptime is NULL AND 
                        (acctstarttime + (acctsessiontime * interval '1 sec'
                        )) >= timestamp '%(searchstart)s')
                    )
                                """ % {"searchstart": searchstart}

            if timemode == "timestamp":

                if timestampslack == "": timestampslack=0

                # Search for entries between (given timestamp - 
                # timestampslack) and (given timestamp + timestampslack)
                unixtimestamp = time.mktime(
                        time.strptime(timestamp, DATEFORMAT_SEARCH))
                searchstart = time.strftime(
                        DATEFORMAT_SEARCH,time.localtime(
                            unixtimestamp-(int(timestampslack)*60)))
                searchstop = time.strftime(
                        DATEFORMAT_SEARCH,time.localtime(
                            unixtimestamp+(int(timestampslack)*60)))



                # We pull the same trick here as in the section where 
                # timemode == "days", and UNION two queries together, to
                # make use of the indices.

                self.sqlQuery += """ (
            (

                    -- Finding sessions that ended within our interval
                    acctstoptime BETWEEN timestamp '%(searchstart)s' 
                        AND timestamp '%(searchstop)s'
            ) OR (
                    -- Finding sessions that started within our interval
                    acctstarttime BETWEEN timestamp '%(searchstart)s' 
                        AND timestamp '%(searchstop)s'
            ) OR (
                    -- Finding sessions that seems to have started after our
                    -- interval, but where acctsessiontime reveals that our
                    -- registered acctstarttime wasn't the actual starttime
                    (acctstarttime >= timestamp '%(searchstop)s')
                    AND
                    (acctstoptime-(acctsessiontime * interval '1 sec') 
                        <= timestamp  '%(searchstop)s')
            ) OR ( 
                    -- Finding sessions that started before our interval
                    (acctstarttime <= timestamp '%(searchstop)s')
                    AND ( 
                            -- .. and either stopped inside or after our 
                            -- interval
                            (acctstoptime >= timestamp '%(searchstart)s')
                            -- .. or where the starttime+acctsessiontime 
                            -- reveals that
                            -- this session was active in the interval
                            OR (acctstoptime is NULL 
                                AND (acctstarttime+(acctsessiontime * 
                                    interval '1 sec') 
                                        >= timestamp '%(searchstart)s')
                                    )
                        )
                )
            )
            """ % {"searchstart": searchstart, "searchstop": searchstop}

        self.sqlQuery += ")" # End select
        self.sqlQuery += " ORDER BY %(sortfield)s %(sortorder)s" % {"sortfield": sortfield, "sortorder": sortorder}

        #raise Exception, self.sqlQuery + " " + str(self.sqlParameters)

    def getTable(self):
        """
        Execute SQL query and return a list of ResultRows
        """

        self.execute()
        return self.result 


#
# Radius error log related classes
#

class LogSearchForm:
    """
    Takes input from search form and sets attributes. Offers a method to
    error check the input
    """

    searchstring=""
    searchtype=""
    logentrytype=""
    timemode=""
    timestamp=""
    timestampslack=""
    hours=""
    sortfield=""
    sortorder=""

    def __init__(self, searchstring, searchtype, logentrytype, timemode, 
            timestamp, timestampslack, hours, sortfield, sortorder):
        """
        Set attributes
        """

        self.searchstring = searchstring 
        self.searchtype = searchtype
        self.logentrytype = logentrytype
        self.timemode = timemode
        self.timestamp = timestamp
        self.timestampslack = timestampslack
        self.hours = hours
        self.sortfield = sortfield
        self.sortorder = sortorder

    def checkInput(self):
        """
        Verify that the input has correct format.
        """

        if self.searchstring:
            # Get rid of whitespace from user input 
            self.searchstring = self.searchstring.strip()

        if self.timestamp:
            # Get rid of whitespace from user input 
            self.timestamp = self.timestamp.strip()
            self.timestampslack = self.timestampslack.strip()

            if self.timemode == "timestamp":
                # Matches a date on the format "YYYY-MM-DD hh:mm"
                if not re.match("^(19|20)\d\d[-](0[1-9]|1[012])[-](0[1-9]|[12][0-9]|3[01])\ ([01][0-9]|[2][0-3])\:[0-5][0-9]$", self.timestamp):
                    raise TimestampSyntaxWarning

                if not re.match("^\d*$", self.timestampslack):
                    raise TimestampSlackSyntaxWarning

        if self.timemode == "hours":
            # Get rid of whitespace from user input 
            self.hours = self.hours.strip()

            # Match integers and floats
            if not re.match("(^\d+$)|(^\d+\.{1}\d+)", self.hours):
                raise HoursSyntaxWarning



class LogSearchQuery(SQLQuery):
    """
    Get search result
    """

    def __init__(self, searchstring, searchtype, logentrytype, timemode, 
            timestamp, timestampslack, hours, sortfield, sortorder):
        """
        Construct search query from user input
        """

        # Make "*" wildcard character
        if searchstring:
            searchstring = searchstring.lower().replace("*","%")

        
        self.sqlQuery = """SELECT
                        id,
                        time,
                        message,
                        type
                        FROM %s 
                        """ % LOG_TABLE

        if (searchstring and searchstring != "%") or logentrytype \
                or timemode:
            self.sqlQuery += " WHERE"

        # Contains all parameters we want to escape
        self.sqlParameters = ()

        # Check what we are searching for. It's either a username, realm,
        # or an IP address/hostname. If searching for all users, skip this
        # where clause all together.
        if searchstring and searchstring != "%":
            self.sqlQuery += " LOWER(%s) LIKE %%s" % (searchtype)
            self.sqlParameters += (searchstring.lower(),)

        if logentrytype:
            if searchstring and searchstring != "%": 
                self.sqlQuery += " AND "
            self.sqlQuery += " LOWER(type) LIKE %%s" % ()
            self.sqlParameters += (logentrytype.lower(),)
            #pass


        # Searching for entries in a specified time interval.
        if timemode:
            # If we have already specified some criteria, we need to AND 
            # it with this time interval search
            if self.sqlQuery.find("WHERE", 0, -5) != -1:
                self.sqlQuery += " AND "

            if timemode == "hours":
                # Search for entries active from x*24 hours ago, until now.
                searchtime = float(hours)*3600
                searchstart = time.strftime(
                        DATEFORMAT_SEARCH, time.localtime(
                            time.time()-searchtime))

                self.sqlQuery += " (time >= timestamp '%s') " % (searchstart)

            if timemode == "timestamp":
                if not timestampslack: timestampslack=0

                # Search for entries between (given timestamp - slack) 
                # and (given timestamp + slack)
                unixtimestamp = time.mktime(
                        time.strptime(timestamp, DATEFORMAT_SEARCH))
                searchstart = time.strftime(
                        DATEFORMAT_SEARCH,time.localtime(
                            unixtimestamp-(int(timestampslack)*60)))
                searchstop = time.strftime(
                        DATEFORMAT_SEARCH,time.localtime(
                            unixtimestamp+(int(timestampslack)*60)))

                self.sqlQuery += """ (
                        -- Finding sessions that ended within our interval
                        time BETWEEN timestamp '%(searchstart)s' 
                            AND timestamp '%(searchstop)s'
                        ) """ \
                    % {"searchstart": searchstart, "searchstop": searchstop}

        self.sqlQuery += " ORDER BY %(sortfield)s %(sortorder)s" % {"sortfield": sortfield, "sortorder": sortorder}
        #raise Exception, self.sqlQuery

    def getTable(self):
        """
        Execute SQL query and return a list of ResultRows
        """

        self.execute()
        return self.result 



class LogDetailQuery(SQLQuery):
    """
    Get all details about specified log entry 
    """

    def __init__(self, logid):
        """
        Construct SQL query

        Keyword arguments:
        logid   - ID of the log entry we want to get details on.
        """
        self.logid = logid

        self.sqlQuery = """SELECT 
                           *
                           FROM %s 
                           WHERE id = %%s
                        """ % (LOG_TABLE)
        self.sqlParameters = (self.logid,)


    def getTable(self):
        self.execute()
        searchResult = self.result[0]
        return searchResult 




#
#  Exception Classes
#


class UserInputSyntaxWarning(SyntaxWarning):
    pass

class IPAddressNotFoundWarning(UserInputSyntaxWarning):
    def __str__(self): 
        return "IP Address could not be resolved"

class TimestampSyntaxWarning(UserInputSyntaxWarning):
    def __str__(self):
        return """Wrong format in timestamp. Please enter a 
                timestamp in the format: YYYY-MM-DD hh:mm"""

class TimestampSlackSyntaxWarning(UserInputSyntaxWarning):
    def __str__(self):
        return  "The timestamp slack field kan only contain integers."

class DaysSyntaxWarning(UserInputSyntaxWarning):
    def __str__(self):
        return "The days field kan only contain integer or float numbers"

class HoursSyntaxWarning(UserInputSyntaxWarning):
    def __str__(self):
        return "The hour field can only contain integer or float numbers"

class EmptySearchstringWarning(UserInputSyntaxWarning):
    def __str__(self): 
        return "Searchstring can not be empty"
