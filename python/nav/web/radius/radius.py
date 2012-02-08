# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 University of Tromsø
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""radius accounting interface mod_python handler"""

import time
import re

from nav.web.encoding import encoded_output
from nav.web.URI import URI
from nav import db
from socket import gethostbyname_ex, gaierror
from mod_python import apache

from radius_config import DB_USER, DB, DEBUG, DATEFORMAT_SEARCH
from radius_config import ACCT_SEARCHRESULTFIELDS, LOG_SEARCHRESULTFIELDS
from radius_config import ACCT_DETAILSFIELDS, LOG_DETAILFIELDS
from radius_config import ACCT_TABLE, LOG_TABLE

URL_PATTERN = re.compile("(?P<baseurl>\w+)\/(?P<section>\w+?)(?:\/$|\?|\&|$)")

@encoded_output
def handler(req):
    """mod_python handler for radius UI"""
    global database
    connection = db.getConnection(DB_USER, DB)
    database = connection.cursor()

    from nav.web.templates.AcctSearchTemplate import AcctSearchTemplate
    from nav.web.templates.AcctDetailTemplate import AcctDetailTemplate
    from nav.web.templates.AcctChartsTemplate import AcctChartsTemplate
    from nav.web.templates.LogTemplate import LogTemplate
    from nav.web.templates.LogDetailTemplate import LogDetailTemplate

    args = URI(req.unparsed_uri)

    # Get basename and section part of the URI
    section = ""
    match = URL_PATTERN.search(req.uri)
    if match:
        section = match.group("section")


    menu = []
    menu.append({'link': 'acctsearch',
                 'text': 'Accounting Log',
                 'admin': False})
    menu.append({'link': 'acctcharts',
                 'text': 'Accounting Charts',
                 'admin': False})
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

            page.form.check_input()

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
                page.search.load_table()

        except UserInputSyntaxWarning, error:
            page.error = error

    elif section.lower() == "logdetail":
        page = LogDetailTemplate()
        page.error = None
        page.menu = menu
        page.dbfields = LOG_DETAILFIELDS #Infofields to display

        query = LogDetailQuery(args.get("id"))
        page.detailQuery = query
        page.detailQuery.load_table()

    elif section.lower() == "acctdetail":
        page = AcctDetailTemplate()
        page.error = None
        page.menu = menu
        page.dbfields = ACCT_DETAILSFIELDS #Infofields to display

        query = AcctDetailQuery(args.get("acctuniqueid"))
        page.detailQuery = query
        page.detailQuery.load_table()

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
            page.form.check_input()

            page.sentChartQuery = None
            page.recvChartQuery = None
            page.sentrecvChartQuery = None

            if page.form.uploadchart:
                # Get the top uploaders
                query = AcctChartsQuery("sent", page.form.days)
                page.sentChartQuery = query
                page.sentChartQuery.load_table()

            if page.form.downloadchart:
                # Get the top leechers
                query = AcctChartsQuery("recv", page.form.days)
                page.recvChartQuery = query
                page.recvChartQuery.load_table()

            if page.form.overallchart:
                # Get the top overall bandwidth hogs
                query = AcctChartsQuery("sentrecv", page.form.days)
                page.sentrecvChartQuery = query
                page.sentrecvChartQuery.load_table()

        except UserInputSyntaxWarning, error:
            page.error = error

    else:
        page = AcctSearchTemplate()
        page.current = "acctsearch"
        if DEBUG:
            page.refreshCache()
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
            page.form.check_input()

            if args.get("send"):
                if page.form.searchstring:
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
                else:
                    # Need a non-empty searchstring
                    raise EmptySearchstringWarning

                page.search = query
                page.search.load_table()

        except UserInputSyntaxWarning, error:
            page.error = error

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

    query = None
    parameters = None
    table = None
    result = None

    def execute(self):
        database.execute(self.query, self.parameters)

        # Create tuple of dictionaries
        colnames = [t[0] for t in database.description]
        rows = [dict(zip(colnames, tup)) for tup in database.fetchall()]
        self.result = rows

    def get_table(self):
        pass

    def load_table(self):
        self.table = self.get_table()


#
# Accounting related classes
#

class AcctSearchForm:
    """
    Takes input from search form and sets attributes. Offers a method to
    error check the input
    """

    userdns = ""
    nasdns = ""

    def __init__(self, searchstring, searchtype, nasporttype, timemode,
                 timestamp, timestampslack, days, userdns, nasdns, sortfield,
                 sortorder):
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
        if userdns:
            self.userdns = userdns  # Don't inlude in instance
        if nasdns:
            self.nasdns = nasdns     # if checkbox not checked

    def check_input(self):
        """
        Verify that the input has correct format.
        """
        if self.searchstring:
            # Leading or trailing whitespace is probably in there by
            # mistake, so remove it.
            self.searchstring = self.searchstring.strip()
        if self.searchtype == "iprange":
            if not re.match("^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$",
                            self.searchstring):
                raise IPRangeSyntaxWarning
        if self.timestamp:
            # Leading or trailing whitespace is probably in there by
            # mistake, so remove it.
            self.timestamp = self.timestamp.strip()
            self.timestampslack = self.timestampslack.strip()

            if self.timemode == "timestamp":
                # Matches a date on the format "YYYY-MM-DD hh:mm"
                if not re.match("^(19|20)\d\d[-](0[1-9]|1[012])[-]"
                                "(0[1-9]|[12][0-9]|3[01])\ "
                                "([01][0-9]|[2][0-3])\:[0-5][0-9]$",
                                self.timestamp):
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
                 days=None):
        """
        Set attributes
        """
        self.days = days or "7"
        self.overallchart = overallchart
        self.downloadchart = downloadchart
        self.uploadchart = uploadchart

    def check_input(self):
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

    def __init__(self, chart, days=None, topx="10"):
        """
        Construct query

        Keyword arguments:
        chart       - "sent", "recv" or "sentrecv" for top upload, top
                      download and top overall, respectively.
        days        - How many of the last days we want chart for
        topx        - Tells the query how many users to return (default 10).
        """

        if chart == "sent":
            field = "acctinputoctets"
        if chart == "recv":
            field = "acctoutputoctets"
        if chart == "sentrecv":
            field = "acctoutputoctets+acctinputoctets"
        if not days:
            days = "7"


        # In this SQL query, we sum up some fields in the database according
        # to what kind of chart we are making,
        #
        # Since freeradius (v1.0.4) has a tendency to insert some sessions
        # twice in the database, we eliminate this in the nested select-query,
        # by just working on entries with distinct acctuniqueid fields. The
        # two entries should be pretty much identical anyway. By "pretty much
        # identical", I mean exatcly identical, except for acctstarttime,
        # which probably differs by a few hundreds of a second, and doesn't
        # make any real difference here anyway.
        if chart == "sent" or chart == "recv" or chart == "sentrecv":

            self.query = """
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
            self.parameters = ()

    def get_table(self):
        """
        Execute the SQL query and return a list containing ResultRows.
        """
        self.execute()
        return self.result



class AcctDetailQuery(SQLQuery):
    """
    Get all details about a specified session
    """

    def __init__(self, rad_acct_id):
        """
        Construct SQL query

        """

        self.rad_acct_id = rad_acct_id

        self.query = """SELECT
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
                        WHERE radacctid = %%s
                        """ % (ACCT_TABLE)
        self.parameters = (self.rad_acct_id,)


    def get_table(self):
        self.execute()
        search_result = self.result[0]
        return search_result





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

        self.query = """(SELECT
                        radacctid,
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
            self.query += " WHERE"

        # Contains all parameters we want to escape
        self.parameters = ()

        # Check what we are searching for. It's either a username, realm,
        # or an IP address/hostname. If searching for all users, skip this
        # where clause all together.
        if (searchtype == "username" or searchtype == "realm") \
                and searchstring != "%":
            self.query += " LOWER(%s) LIKE %%s" % (searchtype)
            self.parameters += (searchstring,)

        # Address
        if (searchtype == "framedipaddress" \
                or searchtype == "nasipaddress"):
            # Split search string into hostname and, if entered, cisco nas
            # port.
            match = re.search("^(?P<host>[[a-zA-Z0-9\.\-]+)[\:\/]{0,1}"
                              "(?P<swport>[\S]+){0,1}$",
                              searchstring)
            # Get all ip addresses, if a hostname is entered
            try:
                addresses = gethostbyname_ex(match.group("host"))[2]
            except (AttributeError, gaierror):
                # AttributeError triggered when regexp found no match, and
                # thus is None
                raise IPAddressNotFoundWarning

            self.query += " ("
            for address in addresses:
                self.query += "%s = INET(%%s)" % (searchtype)
                self.parameters += (address,)
                if address != addresses[-1]:
                    self.query += " OR "
            self.query += ")"

            # Search for Cisco NAS port, if it has been entered
            if match.group("swport"):
                self.query += " AND LOWER(cisconasport) = %s"
                self.parameters += tuple(
                    match.group("swport").lower().split())


        if searchtype == "iprange":
            if searchstring.find('%'):
                if re.search('/32', searchstring):
                    self.query += (" (%s = INET(%%s) OR %s = INET(%%s))" %
                                   ('framedipaddress', 'nasipaddress'))
                    self.parameters += (searchstring[:-3], searchstring[:-3])
                else:
                    self.query += (" (%s << INET(%%s) OR %s = INET(%%s))" %
                                   ('framedipaddress', 'nasipaddress'))
                    self.parameters += (searchstring, searchstring)


        if nasporttype:
            if nasporttype.lower() == "isdn":
                nasporttype = "ISDN"
            if nasporttype.lower() == "vpn":
                nasporttype = "Virtual"
            if nasporttype.lower() == "modem":
                nasporttype = "Async"
            if nasporttype.lower() == "dot1x":
                nasporttype = "Ethernet"
            else:
                if searchstring != "%":
                    self.query += " AND "

                self.query += " nasporttype = %s"
                self.parameters += (nasporttype,)


        # Searching for entries in a specified time interval.
        #
        # This might be a bit confusing, so I'll try to explain..
        #
        # First, some notes about the accounting entries:
        # 1) All entries have a date+time in the 'acctstarttime' field.
        # 2) All entries does not necessarily have an entry in 'acctstoptime'
        # 3) All entries for sessions that have lasted longer than the
        #    re-authentication-interval, have an integer value in the
        #    'acctsessiontime' field.
        # 4) Since the date in 'acctstarttime' is actually just the time
        #    when freeradius received EITHER a Start message, or an Alive
        #    message with a Acct-Unique-Session-Id that wasn't in the
        #    database, a session can have started prior to the 'acctstarttime'
        #    Thus if 'acctstoptime' != NULL, we might have actually gotten a
        #    Stop message with an Acct-Session-Time that tells ut how long the
        #    session has really lasted. We can therefore extract the real
        #    starting time by subtracting 'acctsessiontime' from
        #    'acctstoptime'
        # 5) To match entries for sessions that have not yet ended, we have to
        #    add 'acctsessiontime' to 'acctstarttime'
        #    and see if the resulting time interval touches our search
        #    interval.

        if timemode:

            # If we have already specified some criteria, we need to AND
            # it with the date search
            if self.query.find("WHERE", 0, -5) != -1:
                self.query += " AND "

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
                tmp_where_clause = ""
                tmp_where_clause += """
                    (
                    (   -- Finding sessions that ended within our interval
                        acctstoptime >= timestamp '%(searchstart)s'
                    ) OR (
                        -- Finding sessions that started within our interval
                        acctstarttime >= timestamp '%(searchstart)s')
                    )
                    )
                    UNION """ % {"searchstart": searchstart}
                self.query += tmp_where_clause + self.query
                self.parameters += self.parameters
                self.query += """

                    (
                        -- Find sessions without acctstoptime, but where
                        -- acctstarttime+acctsessiontime is in our interval
                        (acctstoptime is NULL AND
                        (acctstarttime + (acctsessiontime * interval '1 sec'
                        )) >= timestamp '%(searchstart)s')
                    )
                                """ % {"searchstart": searchstart}

            if timemode == "timestamp":

                if timestampslack == "":
                    timestampslack = 0

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

                self.query += """ (
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

        self.query += ")" # End select
        self.query += (" ORDER BY %(sortfield)s %(sortorder)s" %
                       {"sortfield": sortfield, "sortorder": sortorder})

        #raise Exception, self.sqlQuery + " " + str(self.sqlParameters)

    def get_table(self):
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

    def check_input(self):
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
                if not re.match("^(19|20)\d\d[-](0[1-9]|1[012])[-]"
                                "(0[1-9]|[12][0-9]|3[01])\ "
                                "([01][0-9]|[2][0-3])\:[0-5][0-9]$",
                                self.timestamp):
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


        self.query = """SELECT
                     id,
                     time,
                     message,
                     type
                     FROM %s
                     """ % LOG_TABLE

        if (searchstring and searchstring != "%") or logentrytype \
                or timemode:
            self.query += " WHERE"

        # Contains all parameters we want to escape
        self.parameters = ()

        # Check what we are searching for. It's either a username, realm,
        # or an IP address/hostname. If searching for all users, skip this
        # where clause all together.
        if searchstring and searchstring != "%":
            self.query += " LOWER(%s) LIKE %%s" % (searchtype)
            self.parameters += (searchstring.lower(),)

        if logentrytype:
            if searchstring and searchstring != "%":
                self.query += " AND "
            self.query += " LOWER(type) LIKE %%s" % ()
            self.parameters += (logentrytype.lower(),)
            #pass


        # Searching for entries in a specified time interval.
        if timemode:
            # If we have already specified some criteria, we need to AND
            # it with this time interval search
            if self.query.find("WHERE", 0, -5) != -1:
                self.query += " AND "

            if timemode == "hours":
                # Search for entries active from x*24 hours ago, until now.
                searchtime = float(hours)*3600
                searchstart = time.strftime(
                        DATEFORMAT_SEARCH, time.localtime(
                            time.time()-searchtime))

                self.query += " (time >= timestamp '%s') " % (searchstart)

            if timemode == "timestamp":
                if not timestampslack:
                    timestampslack = 0

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

                self.query += """ (
                        -- Finding sessions that ended within our interval
                        time BETWEEN timestamp '%(searchstart)s'
                            AND timestamp '%(searchstop)s'
                        ) """ \
                    % {"searchstart": searchstart, "searchstop": searchstop}

        self.query += (" ORDER BY %(sortfield)s %(sortorder)s" %
                       {"sortfield": sortfield, "sortorder": sortorder})
        #raise Exception, self.sqlQuery

    def get_table(self):
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

        self.query = """SELECT
                        *
                        FROM %s
                        WHERE id = %%s
                     """ % (LOG_TABLE)
        self.parameters = (self.logid,)


    def get_table(self):
        self.execute()
        search_result = self.result[0]
        return search_result




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
        return ("Wrong format in timestamp. Please enter a "
                "timestamp in the format: YYYY-MM-DD hh:mm")

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

class IPRangeSyntaxWarning(UserInputSyntaxWarning):
    def __str__(self):
        return "IP-range should be in CIDR format xxx.xxx.xxx.xxx/xx"
