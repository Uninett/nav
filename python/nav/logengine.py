#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2007, 2009-2011 UNINETT AS
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
"""logengine.py inserts Cisco syslog messages into the NAV database.

Most of the operation of this program is configured in logger.conf.

Syslog messages will be read from the configured file, parsed and
inserted into structured NAV database tables.  Messages that cannot be
parsed as Cisco syslog messages are ignored.

The syslog file is truncated upon the exit of this program.  If you
wish to keep a copy of the syslog messages on file, you should
configure your syslog daemon to log the messages to two separate
files, one of which this program will have exclusive access to.

"""

## The structure of this code was a mess translated more or less
## directly from perl code. Some refactoring attempts have been made
## to make it more maintainable.  Feel free to refactor it further,
## where it makes sense.

## BUGS: This program has one glaring problem: All the log lines are
## read into memory, and the logfile is subsequently truncated.  If
## the program crashes before the lines are inserted into the
## database, all the read log lines are lost.

## TODO: Possible future enhancement is the ability to tail a log file
## continually, instead of reading and truncating as a cron job.

import re
import fcntl
import sys
import os
import os.path
import errno
import atexit
import logging
from ConfigParser import ConfigParser
import datetime
import optparse

import nav
import nav.logs
from nav import db
from nav import daemon
from nav.buildconf import localstatedir

logger = logging.getLogger('logengine')

def get_exception_dicts(config):

    options = config.options("priorityexceptions")

    exceptionorigin = {}
    exceptiontype = {}
    exceptiontypeorigin = {}
    exceptions = {}
    for option in options:
        newpriority = config.get("priorityexceptions", option)
        op = re.split("@", option)
        if len(op) == 1:
            exceptions[op[0]] = newpriority
        if len(op) == 2:
            any = re.compile("any", re.I)
            if not op[0] or any.search(op[0]):
                exceptionorigin[op[1]] = newpriority
            if not op[1] or any.search(op[1]):
                exceptiontype[op[0]] = newpriority
            #both fields
            if op[0] and op[1]:
                if not exceptiontypeorigin.has_key(op[0]):
                    exceptiontypeorigin[op[0]] = {}
                exceptiontypeorigin[op[0]][op[1]] = newpriority

        #only one of the fields
        for exception, priority in exceptions.items():
            typematch = re.search("^\w+\-\d+\-\S+$", exception)
            if typematch:
                exceptiontype[exception] = priority
            else:
                exceptionorigin[exception] = priority

    return (exceptionorigin, exceptiontype, exceptiontypeorigin)

# Examples of typical log lines that must be matched by the following
# regexp:

# Feb  8 12:58:40 158.38.0.51 316371: Feb  8 12:58:39.873 MET: %SEC-6-IPACCESSLOGDP: list 112 permitted icmp 158.38.60.10 -> 158.38.12.5 (0/0), 1 packet
# Mar 20 10:27:26 sw_1 607977: Mar 20 2009 10:20:06: %SEC-6-IPACCESSLOGP: list fraVLAN800 denied tcp x.x.x.x(1380) -> y.y.y.y(80), 2 packets
# Mar 25 10:54:25 somedevice 72: AP:000b.adc0.ffee: *Mar 25 10:15:51.666: %LINK-3-UPDOWN: Interface Dot11Radio0, changed state to up

typicalmatchRe = re.compile(
    """
    ^
    (?P<servmonth>\w+) \s+ (?P<servday>\d+) \s+      # server month and date
    (?P<servhour>\d+) \: (?P<servmin>\d+) : \d+ \W+  # server hour/min/second
    (?P<origin>\S+)                                  # origin
    \W+ (?:(\d{4}) | .*?) \s+ \W*                    # year/msg counter/garbage
    (?P<month>\w+) \s+ (?P<day>\d+) \s+              # origin month and date
    ((?P<year>\d{4}) \s+ )?                          # origin year, if present
    (?P<hour>\d+) : (?P<min>\d+) : (?P<second>\d+)   # origin hour/minute/second
    .* %                                             # eat chars until % appears
    (?P<type>[^:]+) :                                # message type
    \s* (?P<description>.*)                          # message (lstripped)
    $
    """, re.VERBOSE)

# WTF is a "not so typical match"?
notsotypicalmatchRe = re.compile(
    """
    (?P<month>\w+) \s+ (?P<day>\d+) \s+
    (?P<hour>\d+) : (?P<min>\d+) : (?P<second>\d+) \W+
    (?P<origin>\S+ \. \w+) .* \W
    (?P<type>\w+ \ ?? \w* - (?P<priority>\d) -? \w*) :
    \s* (?P<description>.*)
    $
    """, re.VERBOSE)

typematchRe = re.compile("\w+-\d+-?\S*:")
def createMessage(line):

    typicalmatch = typicalmatchRe.search(line)
    match = typicalmatch or notsotypicalmatchRe.search(line)

    if match:
        origin = match.group('origin')
        month = find_month(match.group('month'))
        if 'year' in match.groupdict() and match.group('year'):
            year = int(match.group('year'))
        else:
            year = find_year(month)
        day = int(match.group('day'))
        hour = int(match.group('hour'))
        minute = int(match.group('min'))
        second = int(match.group('second'))
        msgtype = match.group('type')
        description = match.group('description')

        timestamp = datetime.datetime(year, month, day, hour, minute, second)

        return Message(timestamp, origin, msgtype, description)

    else:
        # if this message shows sign of cisco format, put it in the error log
        typematch = typematchRe.search(line)
        if typematch:
            database.execute("INSERT INTO errorerror (message) "
                             "VALUES (%s)", (line,))

        return



class Message:
    prioritymatchRe = re.compile("^(.*)-(\d*)-(.*)$")
    categorymatchRe = re.compile("\W(gw|sw|gsw|fw|ts)\W")

    def __init__(self, time, origin, type, description):
        self.time = time
        self.origin = origin
        self.category = self.find_category(origin)
        self.type = type
        self.description = db.escape(description)
        self.facility, self.priorityid, self.mnemonic = self.find_priority(type)

    def find_priority(self, type):
        prioritymatch = self.prioritymatchRe.search(type)
        if prioritymatch:
            return (prioritymatch.group(1), int(prioritymatch.group(2)),
                    prioritymatch.group(3))
        else:
            return (None, None, None)

    def find_category(self, origin):
        categorymatch = self.categorymatchRe.search(origin)
        if categorymatch:
            return categorymatch.group(1)
        else:
            return "rest"

def find_year(mnd):
    now = datetime.datetime.now()
    if mnd == 12 and now.month == 1:
        return now.year-1
    else:
        return now.year

def find_month(textual):
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
              "oct", "nov", "dec"]
    try:
        return months.index(textual.lower())+1
    except ValueError, e:
        pass

def delete_old_messages(config):
    """Delete old messages from db, according to config settings."""
    logger.info("Deleting old messages from db")

    connection = db.getConnection('logger','logger')
    cursor = connection.cursor()

    for priority in range(0, 8):
        if config.get("deletepriority", str(priority)):
            days = config.getint("deletepriority", str(priority))
            cursor.execute("DELETE FROM log_message WHERE newpriority=%s "
                           "AND time < now() - interval %s",
                           (priority, '%d days' % days))

    connection.commit()

def verify_singleton(quiet=False):
    """Verify that we are the single running logengine process.

    If a logengine process is already running, we exit this process.

    """
    # Create a pidfile and delete it automagically when the process exits.
    # Although we're not a daemon, we do want to prevent multiple simultaineous
    # logengine processes.
    pidfile = os.path.join(localstatedir, 'run', 'logengine.pid')

    try:
        daemon.justme(pidfile)
    except daemon.AlreadyRunningError, e:
        if quiet:
            sys.exit(0)
        else:
            print >> sys.stderr, "logengine is already running (%d)" % e.pid
            sys.exit(1)

    daemon.writepidfile(pidfile)
    atexit.register(daemon.daemonexit, pidfile)


def get_categories(cursor):
    categories = {}
    cursor.execute("select category from category")
    for r in cursor.fetchall():
        if not categories.has_key(r[0]):
            categories[r[0]] = r[0]
    return categories

def get_origins(cursor):
    origins = {}
    cursor.execute("select origin, name from origin")
    for r in cursor.fetchall():
        if not origins.has_key(r[1]):
            origins[r[1]] = int(r[0])
    return origins

def get_types(cursor):
    types = {}
    cursor.execute(
        "select type, facility, mnemonic, priority from log_message_type")
    for r in cursor.fetchall():
        if not types.has_key(r[1]):
            types[r[1]] = {}
        if not types[r[1]].has_key(r[2]):
            types[r[1]][r[2]] = int(r[0])
    return types

def read_log_lines(config):
    """Read and yield message lines from the watched cisco log file.

    Once the log file has been read, it is truncated. The watched file
    is configured using the syslog option in the paths section of
    logger.conf.

    """
    logfile = config.get("paths","syslog")
    if config.has_option("paths", "charset"):
        charset = config.get("paths", "charset")
    else:
        charset = "ISO-8859-1"

    f = None
    ## open log
    try:
        f = open(logfile, "r+")
    except IOError, e:
        # If logfile can't be found, we ignore it.  We won't needlessly
        # spam the NAV admin every minute with a file not found error!
        if e.errno != errno.ENOENT:
            logger.exception("Couldn't open logfile %s", logfile)

    ## if the file exists
    if f:

        ## lock logfile
        fcntl.flock(f, fcntl.LOCK_EX)

        ## read log
        fcon = f.readlines()

        ## truncate logfile
        f.truncate(0)

        ## unlock logfile
        fcntl.flock(f, fcntl.LOCK_UN)
        ##close log
        f.close()

        for line in fcon:
            # Make sure the data is encoded as UTF-8 before we begin work on it
            line = line.decode(charset).encode("UTF-8")
            yield line
    else:
        raise StopIteration

def parse_and_insert(line, database,
                     categories, origins, types,
                     exceptionorigin, exceptiontype, exceptiontypeorigin):
    """Parse a line of cisco log text and insert into db."""

    try:
        message = createMessage(line)
    except Exception, e:
        logger.exception("Unhandled exception during message parse: %s",
                         line)
        return False

    if message:
        try:
            insert_message(message, database,
                           categories, origins, types,
                           exceptionorigin, exceptiontype, exceptiontypeorigin)
        except Exception:
            logger.exception("Unhandled exception during message insert: %s",
                             line)
            raise

def insert_message(message, database,
                   categories, origins, types,
                   exceptionorigin, exceptiontype, exceptiontypeorigin):
    ## check origin (host)
    if not origins.has_key(message.origin):
        if not categories.has_key(message.category):
            add_category(message.category, categories, database)
        add_origin(message.origin, message.category, origins, database)
    originid = origins[message.origin]

    ## check type
    if (not types.has_key(message.facility) or
        not types[message.facility].has_key(message.mnemonic)):
        add_type(message.facility, message.mnemonic, message.priorityid, types,
                 database)
    typeid = types[message.facility][message.mnemonic]

    ## overload priority if exceptions are set
    m_type = message.type.lower()
    origin = message.origin.lower()
    if (exceptiontypeorigin.has_key(m_type) and
        exceptiontypeorigin[m_type].has_key(origin)):
        try:
            message.priorityid = int(exceptiontypeorigin[m_type][origin])
        except:
            pass

    elif exceptionorigin.has_key(origin):
        try:
            message.priorityid = int(exceptionorigin[origin])
        except:
            pass

    elif exceptiontype.has_key(m_type):
        try:
            message.priorityid = int(exceptiontype[m_type])
        except:
            pass

    ## insert message into database
    database.execute("INSERT INTO log_message (time, origin, "
                     "newpriority, type, message) "
                     "VALUES (%s, %s, %s, %s, %s)",
                     (str(message.time), originid,
                      message.priorityid, typeid,
                      message.description))

def add_category(category, categories, database):
    database.execute("INSERT INTO category (category) "
                     "VALUES (%s)", (category,))
    categories[category] = category


def add_origin(origin, category, origins, database):
    database.execute("SELECT nextval('origin_origin_seq')")
    originid = database.fetchone()[0]
    assert type(originid) in (int, long)
    database.execute("INSERT INTO origin (origin, name, "
                     "category) VALUES (%s, %s, %s)",
                     (originid, origin, category))
    origins[origin] = originid
    return originid

def add_type(facility, mnemonic, priorityid, types, database):
    database.execute("SELECT nextval('log_message_type_type_seq')")
    typeid = int(database.fetchone()[0])
    assert type(typeid) in (long, int)

    database.execute("INSERT INTO log_message_type (type, facility, "
                     "mnemonic, priority) "
                     "VALUES (%s, %s, %s, %s)",
                     (typeid, facility, mnemonic, priorityid))
    if not types.has_key(facility):
        types[facility] = {}
    types[facility][mnemonic] = typeid

def logengine(config, options):
    global connection, database

    verify_singleton(options.quiet)

    connection = db.getConnection('logger','logger')
    database = connection.cursor()

    ## initial setup of dictionaries

    categories = get_categories(database)
    origins = get_origins(database)
    types = get_types(database)

    ## parse priorityexceptions
    (exceptionorigin,
     exceptiontype,
     exceptiontypeorigin) =  get_exception_dicts(config)

    ## add new records
    logger.info("Reading new log entries")
    my_parse_and_insert = swallow_all_but_db_exceptions(parse_and_insert)
    for line in read_log_lines(config):
        my_parse_and_insert(line, database,
                            categories, origins, types,
                            exceptionorigin, exceptiontype,
                            exceptiontypeorigin)

    # Make sure it all sticks
    connection.commit()

def swallow_all_but_db_exceptions(func):
    def _swallow(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except db.driver.Error, err:
            raise
        except Exception:
            logger.exception("Unhandled exception occurred, ignoring.")
    return _swallow

def parse_options():
    """Parse and return options supplied on command line."""
    parser = optparse.OptionParser()
    parser.add_option("-d", "--delete", action="store_true", dest="delete",
                      help="delete old messages from database and exit")
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                      help="quietly exit without returning an error code if "
                      "logengine is already running")

    return parser.parse_args()

def main():
    # Figure out what to do
    (options, args) = parse_options()

    # Process setup

    config = ConfigParser()
    config.read(os.path.join(nav.path.sysconfdir,'logger.conf'))

    logging.basicConfig()
    nav.logs.set_log_levels()

    if options.delete:
        # get rid of old records
        delete_old_messages(config)
        sys.exit(0)
    else:
        logengine(config, options)


if __name__ == '__main__':
    main()
