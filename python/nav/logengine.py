#
# Copyright (C) 2007, 2009-2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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

# The structure of this code was a mess translated more or less
# directly from perl code. Some refactoring attempts have been made
# to make it more maintainable.  Feel free to refactor it further,
# where it makes sense.

# BUGS: This program has one glaring problem: All the log lines are
# read into memory, and the logfile is subsequently truncated.  If
# the program crashes before the lines are inserted into the
# database, all the read log lines are lost.

# TODO: Possible future enhancement is the ability to tail a log file
# continually, instead of reading and truncating as a cron job.

import re
import fcntl
import sys
import errno
import atexit
import logging
from configparser import ConfigParser
import datetime
import optparse

import nav
import nav.logs
from nav import db
from nav import daemon
from nav.config import find_config_file


PID_FILE = 'logengine.pid'
_logger = logging.getLogger("nav.logengine")


def get_exception_dicts(config):
    options = config.options("priorityexceptions")

    exceptionorigin = {}
    exceptiontype = {}
    exceptiontypeorigin = {}
    exceptions = {}
    for option in options:
        newpriority = config.get("priorityexceptions", option)
        opt = re.split("@", option)
        if len(opt) == 1:
            exceptions[opt[0]] = newpriority
        if len(opt) == 2:
            any_re = re.compile("any", re.I)
            if not opt[0] or any_re.search(opt[0]):
                exceptionorigin[opt[1]] = newpriority
            if not opt[1] or any_re.search(opt[1]):
                exceptiontype[opt[0]] = newpriority
            # both fields
            if opt[0] and opt[1]:
                if opt[0] not in exceptiontypeorigin:
                    exceptiontypeorigin[opt[0]] = {}
                exceptiontypeorigin[opt[0]][opt[1]] = newpriority

        # only one of the fields
        for exception, priority in exceptions.items():
            typematch = re.search(r"^\w+\-\d+\-\S+$", exception)
            if typematch:
                exceptiontype[exception] = priority
            else:
                exceptionorigin[exception] = priority

    return exceptionorigin, exceptiontype, exceptiontypeorigin


# Timestamp patterns for syslog server timestamps
# RFC 3339 format (used by rsyslog on Debian Bookworm+ with RFC 5424)
_RFC3339_TS = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})"
# Traditional BSD syslog format (spaces escaped for re.VERBOSE compatibility)
_BSD_TS = r"[A-Z][a-z]{2}\ [ \d]\d\ \d{2}:\d{2}:\d{2}"
_SERVER_TS = rf"(?:{_RFC3339_TS}|{_BSD_TS})"

# Cisco/source timestamp: [*]Mon D[D] [YYYY] HH:MM:SS[.fff] [TZ]
_SOURCE_TS = (
    r"\*?[A-Z][a-z]{2}\s+\d{1,2}(?:\s+\d{4})?\s+"
    r"\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\s+[A-Z]{2,5})?"
)

# Matches log lines where the origin included its own timestamp
_typical_match_re = re.compile(
    rf"""
    ^
    {_SERVER_TS}                                     # server timestamp (not captured)
    \s+
    (?P<origin>\S+)                                  # origin
    .+?                                              # garbage (non-greedy)
    (?P<timestamp>{_SOURCE_TS})                      # source timestamp
    \s* : \s*
    %(?P<type>[^:]+):                                # message type
    \s*(?P<description>.*)                           # description
    $
    """,
    re.VERBOSE,
)

# Matches log lines where there is no timestamp from the origin
_not_so_typical_match_re = re.compile(
    rf"""
    ^
    (?P<timestamp>{_SERVER_TS})                      # server timestamp (captured)
    \s+
    (?P<origin>\S+)                                  # origin
    .*                                               # everything until %
    %(?P<type>[a-zA-Z0-9\-_]+):                      # message type
    \s*(?P<description>.*)                           # description
    $
    """,
    re.VERBOSE,
)

_type_match_re = re.compile(r"\w+-\d+-?\S*:")

# Patterns for parse_timestamp()
_tz_suffix_re = re.compile(r'\s+[A-Z]{2,5}$')
_space_padded_day_re = re.compile(r'^([A-Z][a-z]{2})\s+(\d)\s')


def create_message(line, database=None):
    match = _typical_match_re.search(line) or _not_so_typical_match_re.search(line)

    if match:
        try:
            timestamp = parse_timestamp(match.group('timestamp'))
            return Message(
                timestamp,
                match.group('origin'),
                match.group('type'),
                match.group('description'),
            )
        except ValueError:
            _logger.debug("syslog line parse error: %s", line, exc_info=True)

    # if this message shows sign of cisco format, put it in the error log
    typematch = _type_match_re.search(line)
    if typematch and database:
        database.execute("INSERT INTO errorerror (message) VALUES (%s)", (line,))


class Message(object):
    prioritymatch_re = re.compile(r"^(.*)-(\d*)-(.*)$")
    categorymatch_re = re.compile(r"\W(gw|sw|gsw|fw|ts)\W")

    def __init__(self, time, origin, msgtype, description):
        self.time = time
        self.origin = origin
        self.category = self.find_category(origin)
        self.type = msgtype
        self.description = description
        (self.facility, self.priorityid, self.mnemonic) = self.find_priority(msgtype)
        if not self.facility:
            raise ValueError("cannot parse message type: %s" % msgtype)

    def find_priority(self, msgtype):
        prioritymatch = self.prioritymatch_re.search(msgtype)
        if prioritymatch:
            return (
                prioritymatch.group(1),
                int(prioritymatch.group(2)),
                prioritymatch.group(3),
            )
        else:
            return None, None, None

    def find_category(self, origin):
        categorymatch = self.categorymatch_re.search(origin)
        if categorymatch:
            return categorymatch.group(1)
        else:
            return "rest"


def find_year(mnd):
    now = datetime.datetime.now()
    if mnd == 12 and now.month == 1:
        return now.year - 1
    else:
        return now.year


def find_month(textual):
    months = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    try:
        return months.index(textual.lower()) + 1
    except ValueError:
        pass


def parse_timestamp(timestamp_str: str) -> datetime.datetime:
    """Parse a timestamp string, trying RFC 3339 first, then traditional formats.

    :param timestamp_str: A timestamp string in either RFC 3339 format
                          (e.g. "2026-01-05T13:54:43.262668+01:00") or traditional
                          Cisco/BSD syslog format (e.g. "Oct 28 13:15:05.310 CEST")
    :returns: A datetime.datetime object (without timezone info)
    :raises ValueError: If the timestamp cannot be parsed
    """
    # Try RFC 3339 / ISO 8601 first
    try:
        dt = datetime.datetime.fromisoformat(timestamp_str)
        # Convert to local time before stripping timezone info (since NAV legacy code
        # unfortunately still uses timezone-naive timestamps)
        if dt.tzinfo is not None:
            dt = dt.astimezone().replace(tzinfo=None)
        return dt
    except ValueError:
        pass

    # Try traditional syslog/Cisco formats
    ts = timestamp_str.lstrip('*')  # Some Cisco timestamps have leading *

    # Strip timezone abbreviation at end (strptime %Z is unreliable)
    ts = _tz_suffix_re.sub('', ts)

    # Normalize space-padded single-digit days (e.g., "Jan  5" -> "Jan 05")
    ts = _space_padded_day_re.sub(r'\1 0\2 ', ts)

    for fmt in [
        "%b %d %H:%M:%S.%f",  # Oct 28 13:15:05.310
        "%b %d %H:%M:%S",  # Oct 28 13:15:05
        "%b %d %Y %H:%M:%S.%f",  # Oct 28 2010 12:08:49.123
        "%b %d %Y %H:%M:%S",  # Oct 28 2010 12:08:49
    ]:
        try:
            dt = datetime.datetime.strptime(ts, fmt)
            if dt.year == 1900:  # strptime default when no year in format
                dt = dt.replace(year=find_year(dt.month))
            return dt
        except ValueError:
            continue

    raise ValueError(f"Cannot parse timestamp: {timestamp_str}")


def delete_old_messages(config):
    """Delete old messages from db, according to config settings."""
    _logger.debug("Deleting old messages from db")

    conn = db.getConnection('logger', 'logger')
    cursor = conn.cursor()

    for priority in range(0, 8):
        if config.get("deletepriority", str(priority)):
            days = config.getint("deletepriority", str(priority))
            cursor.execute(
                "DELETE FROM log_message WHERE newpriority=%s "
                "AND time < now() - interval %s",
                (priority, '%d days' % days),
            )

    conn.commit()


def verify_singleton(quiet=False):
    """Verify that we are the single running logengine process.

    If a logengine process is already running, we exit this process.

    """
    # Create a pidfile and delete it automagically when the process exits.
    # Although we're not a daemon, we do want to prevent multiple simultaineous
    # logengine processes.

    try:
        daemon.justme(PID_FILE)
    except daemon.AlreadyRunningError as err:
        if quiet:
            sys.exit(0)
        else:
            print("logengine is already running (%d)" % err.pid, file=sys.stderr)
            sys.exit(1)

    daemon.writepidfile(PID_FILE)
    atexit.register(daemon.daemonexit, PID_FILE)


def get_categories(cursor):
    categories = {}
    cursor.execute("select category from category")
    for (category,) in cursor.fetchall():
        if category not in categories:
            categories[category] = category
    return categories


def get_origins(cursor):
    origins = {}
    cursor.execute("select origin, name from origin")
    for origin, name in cursor.fetchall():
        if name not in origins:
            origins[name] = int(origin)
    return origins


def get_types(cursor):
    types = {}
    cursor.execute("select type, facility, mnemonic, priority from log_message_type")
    for type_, facility, mnemonic, _priority in cursor.fetchall():
        if facility not in types:
            types[facility] = {}
        if mnemonic not in types[facility]:
            types[facility][mnemonic] = int(type_)
    return types


def read_log_lines(config):
    """Read and yield message lines from the watched cisco log file.

    Once the log file has been read, it is truncated. The watched file
    is configured using the syslog option in the paths section of
    logger.conf.

    """
    filename = config.get("paths", "syslog")
    if config.has_option("paths", "charset"):
        charset = config.get("paths", "charset")
    else:
        charset = "ISO-8859-1"

    logfile = None
    # open log
    try:
        logfile = open(filename, "r+", encoding=charset)
    except IOError as err:
        # If logfile can't be found, we ignore it.  We won't needlessly
        # spam the NAV admin every minute with a file not found error!
        if err.errno != errno.ENOENT:
            _logger.exception("Couldn't open logfile %s", filename)

    # if the file exists
    if logfile:
        # lock logfile
        fcntl.flock(logfile, fcntl.LOCK_EX)

        # read log
        fcon = logfile.readlines()

        # truncate logfile
        logfile.truncate(0)

        # unlock logfile
        fcntl.flock(logfile, fcntl.LOCK_UN)
        # close log
        logfile.close()

        for line in fcon:
            yield line


def parse_and_insert(
    line,
    database,
    categories,
    origins,
    types,
    exceptionorigin,
    exceptiontype,
    exceptiontypeorigin,
):
    """Parse a line of cisco log text and insert into db."""

    try:
        message = create_message(line, database)
    except Exception:  # noqa: BLE001
        _logger.exception("Unhandled exception during message parse: %s", line)
        return False

    if message:
        try:
            insert_message(
                message,
                database,
                categories,
                origins,
                types,
                exceptionorigin,
                exceptiontype,
                exceptiontypeorigin,
            )
        except Exception:  # noqa: BLE001
            _logger.exception("Unhandled exception during message insert: %s", line)
            raise


def insert_message(
    message,
    database,
    categories,
    origins,
    types,
    exceptionorigin,
    exceptiontype,
    exceptiontypeorigin,
):
    # check origin (host)
    if message.origin not in origins:
        if message.category not in categories:
            add_category(message.category, categories, database)
        add_origin(message.origin, message.category, origins, database)
    originid = origins[message.origin]

    # check type
    if message.facility not in types or message.mnemonic not in types[message.facility]:
        add_type(
            message.facility, message.mnemonic, message.priorityid, types, database
        )
    typeid = types[message.facility][message.mnemonic]

    # overload priority if exceptions are set
    m_type = message.type.lower()
    origin = message.origin.lower()
    if m_type in exceptiontypeorigin and origin in exceptiontypeorigin[m_type]:
        try:
            message.priorityid = int(exceptiontypeorigin[m_type][origin])
        except ValueError:
            pass

    elif origin in exceptionorigin:
        try:
            message.priorityid = int(exceptionorigin[origin])
        except ValueError:
            pass

    elif m_type in exceptiontype:
        try:
            message.priorityid = int(exceptiontype[m_type])
        except ValueError:
            pass

    # insert message into database
    database.execute(
        "INSERT INTO log_message (time, origin, "
        "newpriority, type, message) "
        "VALUES (%s, %s, %s, %s, %s)",
        (str(message.time), originid, message.priorityid, typeid, message.description),
    )


def add_category(category, categories, database):
    database.execute("INSERT INTO category (category) VALUES (%s)", (category,))
    categories[category] = category


def add_origin(origin, category, origins, database):
    database.execute("SELECT nextval('origin_origin_seq')")
    originid = database.fetchone()[0]
    assert isinstance(originid, int)
    database.execute(
        "INSERT INTO origin (origin, name, category) VALUES (%s, %s, %s)",
        (originid, origin, category),
    )
    origins[origin] = originid
    return originid


def add_type(facility, mnemonic, priorityid, types, database):
    database.execute("SELECT nextval('log_message_type_type_seq')")
    typeid = int(database.fetchone()[0])
    assert isinstance(typeid, int)

    database.execute(
        "INSERT INTO log_message_type (type, facility, "
        "mnemonic, priority) "
        "VALUES (%s, %s, %s, %s)",
        (typeid, facility, mnemonic, priorityid),
    )
    if facility not in types:
        types[facility] = {}
    types[facility][mnemonic] = typeid


def logengine(config, options):
    verify_singleton(options.quiet)

    connection = db.getConnection('logger', 'logger')
    database = connection.cursor()

    # initial setup of dictionaries

    categories = get_categories(database)
    origins = get_origins(database)
    types = get_types(database)

    # parse priorityexceptions
    (exceptionorigin, exceptiontype, exceptiontypeorigin) = get_exception_dicts(config)

    # add new records
    _logger.debug("Reading new log entries")
    my_parse_and_insert = swallow_all_but_db_exceptions(parse_and_insert)
    for line in read_log_lines(config):
        my_parse_and_insert(
            line,
            database,
            categories,
            origins,
            types,
            exceptionorigin,
            exceptiontype,
            exceptiontypeorigin,
        )

    # Make sure it all sticks
    connection.commit()


def swallow_all_but_db_exceptions(func):
    def _swallow(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except db.driver.Error:
            raise
        except Exception:  # noqa: BLE001
            _logger.exception("Unhandled exception occurred, ignoring.")

    return _swallow


def parse_options():
    """Parse and return options supplied on command line."""
    parser = optparse.OptionParser()
    parser.add_option(
        "-d",
        "--delete",
        action="store_true",
        dest="delete",
        help="delete old messages from database and exit",
    )
    parser.add_option(
        "-q",
        "--quiet",
        action="store_true",
        dest="quiet",
        help="quietly exit without returning an error code if "
        "logengine is already running",
    )

    return parser.parse_args()


def main():
    # Figure out what to do
    (options, _args) = parse_options()

    # Process setup

    config = ConfigParser()
    config.read(find_config_file('logger.conf'))

    nav.logs.init_stderr_logging()

    if options.delete:
        # get rid of old records
        delete_old_messages(config)
        sys.exit(0)
    else:
        logengine(config, options)


if __name__ == '__main__':
    main()
