import re
import time
import uuid
from collections import namedtuple
from socket import gethostbyname_ex, gaierror

from django.db import connection, transaction
from twisted.names.dns import Message, Query

from nav.asyncdns import reverse_lookup
from .radius_config import (
    DATEFORMAT_SEARCH,
    LOG_SEARCHRESULTFIELDS,
    ACCT_DETAILSFIELDS,
    LOG_DETAILFIELDS,
    ACCT_TABLE,
    LOG_TABLE,
)

from . import radiuslib


def get_named_cursor():
    """
    This function returns a named cursor, which speeds up queries
    returning large result sets immensely by caching them on the
    server side.

    This is not yet supported by Django itself.
    """
    # This is required to populate the connection object properly
    if connection.connection is None:
        connection.cursor()

    # Prefixing the name to ensure that it starts with a letter.
    # Needed for psycopg2.2 compatibility
    name = 'nav{0}'.format(str(uuid.uuid4()).replace('-', ''))

    cursor = connection.connection.cursor(name=name)
    return cursor


class SQLQuery(object):
    """
    Superclass for other query classes.
    """

    query = None
    parameters = None
    result = None
    result_tuple = None

    def execute(self):
        cursor = get_named_cursor()
        with transaction.atomic():
            cursor.execute(self.query, self.parameters)
            self.result = [self.result_tuple._make(self._format(row)) for row in cursor]

    def _format(self, row):
        """
        Subclasses should override this method
        if the data need to be formatted for display
        purposes.
        """
        return row


class LogDetailQuery(SQLQuery):
    """
    Get all details about specified log entry
    """

    def __init__(self, logid, fields=LOG_DETAILFIELDS):
        """
        Construct SQL query

        Keyword arguments:
        logid   - ID of the log entry we want to get details on.
        """

        self.result_tuple = namedtuple('LogDetailQueryResult', fields)

        self.logid = logid

        self.query = """SELECT
                        %s
                        FROM %s
                        WHERE id = %%s
                     """ % (
            ','.join(fields),
            LOG_TABLE,
        )
        self.parameters = (self.logid,)

    def _format(self, row):
        try:
            message = row[LOG_DETAILFIELDS.index('message')]
            return map(
                lambda x: (
                    x if x != message else x.replace('[', '[<b>').replace(']', '</b>]')
                ),
                row,
            )
        except ValueError:
            return row


class LogSearchQuery(SQLQuery):
    """
    Get search result
    """

    def __init__(
        self,
        searchstring,
        searchtype,
        logentrytype,
        timemode,
        timestamp,
        timestampslack,
        hours,
        sortfield,
        sortorder,
        fields=LOG_SEARCHRESULTFIELDS,
    ):
        """
        Construct search query from user input
        """

        if 'id' not in fields:
            fields_extended = ['id']
            fields_extended.extend(list(fields))
            fields = fields_extended

        self.result_tuple = namedtuple('LogSearchQueryResult', fields)

        # Make "*" wildcard character
        if searchstring:
            searchstring = searchstring.lower().replace("*", "%")

        self.query = """SELECT
                     %s
                     FROM %s
                     """ % (
            ','.join(fields),
            LOG_TABLE,
        )

        if (searchstring and searchstring != "%") or logentrytype or timemode:
            self.query += " WHERE"

        # Contains all parameters we want to escape
        self.parameters = ()

        # Check what we are searching for. It's either a username, realm,
        # or an IP address/hostname. If searching for all users, skip this
        # where clause all together.
        if searchstring and searchstring != "%":
            self.query += " LOWER(%s) LIKE %%s" % searchtype
            self.parameters += (searchstring.lower(),)

        if logentrytype:
            if searchstring and searchstring != "%":
                self.query += " AND "
            self.query += " LOWER(type) LIKE %%s" % ()
            self.parameters += (logentrytype.lower(),)

        # Searching for entries in a specified time interval.
        if timemode:
            # If we have already specified some criteria, we need to AND
            # it with this time interval search
            if self.query.find("WHERE", 0, -5) != -1:
                self.query += " AND "

            if timemode == "hours":
                # Search for entries active from x*24 hours ago, until now.
                searchtime = float(hours) * 3600
                searchstart = time.strftime(
                    DATEFORMAT_SEARCH, time.localtime(time.time() - searchtime)
                )

                self.query += " (time >= timestamp '%s') " % searchstart

            if timemode == "timestamp":
                if not timestampslack:
                    timestampslack = 0

                # Search for entries between (given timestamp - slack)
                # and (given timestamp + slack)
                unixtimestamp = time.mktime(time.strptime(timestamp, DATEFORMAT_SEARCH))
                searchstart = time.strftime(
                    DATEFORMAT_SEARCH,
                    time.localtime(unixtimestamp - (int(timestampslack) * 60)),
                )
                searchstop = time.strftime(
                    DATEFORMAT_SEARCH,
                    time.localtime(unixtimestamp + (int(timestampslack) * 60)),
                )

                self.query += """ (
                        -- Finding sessions that ended within our interval
                        time BETWEEN timestamp '%(searchstart)s'
                            AND timestamp '%(searchstop)s'
                        ) """ % {
                    "searchstart": searchstart,
                    "searchstop": searchstop,
                }

        self.query += " ORDER BY %(sortfield)s %(sortorder)s" % {
            "sortfield": sortfield,
            "sortorder": sortorder,
        }

    def _format(self, row):
        try:
            message = row[LOG_SEARCHRESULTFIELDS.index('message')]
            return map(
                lambda x: (
                    x if x != message else x.replace('[', '[<b>').replace(']', '</b>]')
                ),
                row,
            )
        except ValueError:
            return row


class AcctSearchQuery(SQLQuery):
    """
    Get search result
    """

    result_tuple = namedtuple(
        'AccountSearchQueryResult',
        (
            'radacctid',
            'acctuniqueid',
            'username',
            'realm',
            'framedipaddress',
            'nasipaddress',
            'nasporttype',
            'acctstarttime',
            'acctstoptime',
            'acctsessiontime',
            'acctoutputoctets',
            'acctinputoctets',
        ),
    )

    def __init__(
        self,
        searchstring,
        searchtype,
        nasporttype,
        timemode,
        timestamp,
        timestampslack,
        days,
        userdns,
        nasdns,
        sortfield,
        sortorder,
    ):
        """
        Construct search query from user input
        """

        # Make "*" wildcard character
        if searchstring:
            searchstring = searchstring.lower().replace("*", "%")

        self.userdns = userdns
        self.nasdns = nasdns
        self.ips_to_lookup = set()

        self.query = (
            """(SELECT
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
                        """
            % ACCT_TABLE
        )

        if (searchstring and searchstring != "%") or nasporttype or timemode:
            self.query += " WHERE"

        # Contains all parameters we want to escape
        self.parameters = ()

        # Check what we are searching for. It's either a username, realm,
        # or an IP address/hostname. If searching for all users, skip this
        # where clause all together.
        if (searchtype == "username" or searchtype == "realm") and searchstring != "%":
            self.query += " LOWER(%s) LIKE %%s" % searchtype
            self.parameters += (searchstring,)

        # Address
        if searchtype == "framedipaddress" or searchtype == "nasipaddress":
            # Split search string into hostname and, if entered, cisco nas
            # port.
            match = re.search(
                r"^(?P<host>[[a-zA-Z0-9\.\-]+)[\:\/]{0,1}" r"(?P<swport>[\S]+){0,1}$",
                searchstring,
            )
            # Get all ip addresses, if a hostname is entered
            try:
                addresses = gethostbyname_ex(match.group("host"))[2]
            except (AttributeError, gaierror):
                # AttributeError triggered when regexp found no match, and
                # thus is None
                addresses = ["255.255.255.255"]

            self.query += " ("
            for address in addresses:
                self.query += "%s = INET(%%s)" % searchtype
                self.parameters += (address,)
                if address != addresses[-1]:
                    self.query += " OR "
            self.query += ")"

            # Search for Cisco NAS port, if it has been entered
            if match.group("swport"):
                self.query += " AND LOWER(cisconasport) = %s"
                self.parameters += tuple(match.group("swport").lower().split())

        if searchtype == "iprange":
            if searchstring.find('%'):
                if re.search('/32', searchstring):
                    self.query += " (%s = INET(%%s) OR %s = INET(%%s))" % (
                        'framedipaddress',
                        'nasipaddress',
                    )
                    self.parameters += (searchstring[:-3], searchstring[:-3])
                else:
                    self.query += " (%s << INET(%%s) OR %s = INET(%%s))" % (
                        'framedipaddress',
                        'nasipaddress',
                    )
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
                searchtime = float(days) * 86400
                searchstart = time.strftime(
                    DATEFORMAT_SEARCH, time.localtime(time.time() - searchtime)
                )
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
                unixtimestamp = time.mktime(time.strptime(timestamp, DATEFORMAT_SEARCH))
                searchstart = time.strftime(
                    DATEFORMAT_SEARCH,
                    time.localtime(unixtimestamp - (int(timestampslack) * 60)),
                )
                searchstop = time.strftime(
                    DATEFORMAT_SEARCH,
                    time.localtime(unixtimestamp + (int(timestampslack) * 60)),
                )

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
            """ % {
                    "searchstart": searchstart,
                    "searchstop": searchstop,
                }

        self.query += ")"  # End select
        self.query += " ORDER BY %(sortfield)s %(sortorder)s" % {
            "sortfield": sortfield,
            "sortorder": sortorder,
        }

    def execute(self):
        super(AcctSearchQuery, self).execute()
        if self.ips_to_lookup:
            lookup_result = reverse_lookup(self.ips_to_lookup)

            self.result = [
                self._replace_ip_with_hostname(result, lookup_result)
                for result in self.result
            ]

    def make_stats(self):
        sessionstats = set()
        total_time, total_sent, total_received = 0, 0, 0

        for row in self.result:
            if row.acctuniqueid not in sessionstats and row.acctsessiontime:
                sessionstats.add(row.acctuniqueid)

                total_time += row.acctsessiontime
                total_sent += row.acctinputoctets
                total_received += row.acctoutputoctets

        return total_time, total_sent, total_received

    def _format(self, row):
        if self.userdns and row[4]:
            self.ips_to_lookup.add(row[4])
        if self.nasdns and row[5]:
            self.ips_to_lookup.add(row[5])

        acctstarttime = radiuslib.remove_fractions(row[7])

        acctstoptime = radiuslib.calculate_stop_time(row[7], row[8], row[9])

        return (
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            acctstarttime,
            acctstoptime,
            row[9],
            row[10],
            row[11],
        )

    def _replace_ip_with_hostname(self, result, lookup_result):
        useraddr = (
            lookup_result.get(result.framedipaddress, [''])[0]
            if self.userdns
            else result.framedipaddress
        )
        nasaddr = (
            lookup_result.get(result.nasipaddress, [''])[0]
            if self.nasdns
            else result.nasipaddress
        )

        # TODO: Maybe we can show the user something more informative
        if isinstance(useraddr, Message) or isinstance(useraddr, Query):
            useraddr = ''
        if isinstance(nasaddr, Message) or isinstance(useraddr, Query):
            nasaddr = ''

        return result._replace(framedipaddress=useraddr, nasipaddress=nasaddr)


class AcctDetailQuery(SQLQuery):
    """
    Get all details about a specified session
    """

    _host_cache = radiuslib.HostCache()

    def __init__(self, rad_acct_id, fields=ACCT_DETAILSFIELDS):
        """
        Construct SQL query

        """

        self.result_tuple = namedtuple('AccountDetailQueryResult', ACCT_DETAILSFIELDS)

        self.rad_acct_id = rad_acct_id

        self.query = """
            SELECT %s FROM %s
            WHERE radacctid = %%s""" % (
            ','.join(fields),
            ACCT_TABLE,
        )

        self.parameters = (self.rad_acct_id,)

    def _format(self, row):
        fields = dict(zip(ACCT_DETAILSFIELDS, row))

        if 'nasipaddress' in fields:
            field = fields['nasipaddress']
            fields['nasipaddress'] = '%s (%s)' % (
                field,
                self._host_cache.lookup_ip_address(field),
            )
        if 'framedipaddress' in fields:
            field = fields['framedipaddress']
            fields['framedipaddress'] = '%s (%s)' % (
                field,
                self._host_cache.lookup_ip_address(field),
            )
        if 'acctstoptime' in fields:
            start = fields['acctstarttime']
            stop = fields['acctstoptime']
            session = fields['acctsessiontime']
            fields['acctstoptime'] = radiuslib.calculate_stop_time(start, stop, session)
        if 'acctsessiontime' in fields:
            fields['acctsessiontime'] = radiuslib.humanize_time(
                fields['acctsessiontime']
            )
        if 'acctoutputoctets' in fields:
            fields['acctoutputoctets'] = radiuslib.humanize_bytes(
                fields['acctoutputoctets']
            )
        if 'acctinputoctets' in fields:
            fields['acctinputoctets'] = radiuslib.humanize_bytes(
                fields['acctinputoctets']
            )

        # dict does not preserve order so we cant use dict.values()
        return tuple([fields[field] for field in ACCT_DETAILSFIELDS])


class AcctChartsQuery(SQLQuery):
    """
    Get top bandwidth hogs for specified period,

    Can generate SQL queries for top uploaders, top downloaders, and top
    overall bandwidth (ab)users
    """

    result_tuple = namedtuple(
        'AccountChartsQueryResult',
        (
            'username',
            'realm',
            'sortfield',
            'acctsessiontime',
            'fieldisnull',
        ),
    )

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
            self.table_title = 'Uploaders'
        if chart == "recv":
            field = "acctoutputoctets"
            self.table_title = 'Downloaders'
        if chart == "sentrecv":
            field = "acctoutputoctets+acctinputoctets"
            self.table_title = 'Bandwidth Hogs (Upload+Downloads)'
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
                    """ % (
                field,
                field,
                ACCT_TABLE,
                days,
                topx,
            )

            self.parameters = ()
