#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- notest -*-
#
# Copyright (C) 2018 Uninett AS
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
"""Radius error log parser.

This program was written to run on a radius server, not on the NAV
server.  It has been written to not require any NAV libraries.

It will require psycopg, a PostgreSQL driver for Python.
"""

import psycopg2
import sys
import os

import re
from time import mktime, strptime
import datetime

# Configuration settings.
# Update these for your setup.
dbhost = ""  # Hostname where the nav-database runs
dbport = 5432  # Port the PostgreSQL database listens to
dbname = "nav"  # Name of the NAV database
dbuser = "nav"  # Username for the nav-database, usually 'nav'
dbpasswd = ""  # Password for nav-user
db_radiuslog_table = "radiuslog"

radius_logfile = ""  # Location of the freeradius-logfile to parse
my_logfile = "./radiusparser.log"  # Location of this program's debug log file


def main(args=None):
    # If script is already running, abort
    if pid_running():
        sys.exit(1)
    else:
        print("Running instance of script not found. Starting...")

    if args is None:
        args = sys.argv[1:]

    try:
        db_params = (dbhost, dbport, dbname, dbuser, dbpasswd)
        connection = psycopg2.connect(
            "host=%s port=%s dbname=%s user=%s password=%s" % db_params
        )
    except psycopg2.OperationalError as e:
        print(
            "An error occured while connecting to the database:\n\n'%s'" % (str(e)[:-1])
        )
        sys.exit(1)

    connection.set_isolation_level(0)
    database = connection.cursor()

    # Start "tail -f" on radius_logfile
    t = Tail(radius_logfile, only_new=True)
    t.nextline()

    # DEBUG-related
    type = 0
    message = 0
    status = 0
    user = 0
    client = 0
    port = 0

    try:
        # Open DEBUG Logfile.
        f = open(my_logfile, 'w+')
        f.write("\n\n\n\n****************** Script restarted *****************\n")

        for line in t:
            # Check if the line is parseable
            try:
                row = Row(parse_line(line))
            except AttributeError:
                print("AttributeError: " + line)

            # We want to look for octals in the messages
            p = re.compile(r'(\\\d\d\d)')

            # Then parse the octals, this is a workaround since
            # Freeradius encodes non-ascii characters with UTF8
            # in octals and we need to let python evaluate them
            # before they are chucked into the DB
            if p.search(row.message):
                row.message = parse_octals(row.message)
                row.client = parse_octals(row.client)
                row.user = parse_octals(row.user)

            # Logging to find out what the maximum length of the db fields
            # need to be

            if len(row.type) > type:
                type = len(row.type)
                f.write("type:    %s\n" % str(type))

            if len(row.message) > message:
                message = len(row.message)
                f.write("message: %s\n" % str(message))

            if len(row.status) > status:
                status = len(row.status)
                f.write("status:  %s\n" % str(status))

            if len(row.user) > user:
                user = len(row.user)
                f.write("user:    %s\n" % str(user))

            if len(row.client) > client:
                client = len(row.client)
                f.write("client:  %s\n" % str(client))

            if len(row.port) > port:
                port = len(row.port)
                f.write("port:    %s\n" % str(port))

            f.flush()

            # Don't insert successful logins in the database
            if row.message != "rlm_eap_mschapv2: Issuing Challenge":
                if row.status != "Login OK":
                    sqlQuery = (
                        "INSERT INTO %s (time, type, message, status, username, "
                        "client, port) VALUES (timestamp '%%s', %%s, %%s, %%s, %%s, "
                        "%%s, %%s)" % (db_radiuslog_table)
                    )
                    sqlParameters = (
                        row.time,
                        row.type,
                        row.message,
                        row.status,
                        row.user,
                        row.client,
                        row.port,
                    )
                    try:
                        database.execute(sqlQuery, sqlParameters)
                    except psycopg2.ProgrammingError as e:
                        # Write error to log
                        f.write("Query failed:\n")
                        f.write(str(e) + "\n\n\n")
                        f.flush()

    except KeyboardInterrupt:
        print("Interrupted by user...")

    database.close()
    sys.exit()


# Parses octals from the freeradius-server
def parse_octals(line):
    def suboct(match):
        return eval("'" + match.group(1) + "'")
        # Consider: eval(func,{"__builtins__":None},{})
        # Maybe Not necessary here

    ret = re.sub(r'(\\\d\d\d)', suboct, line)

    return ret


def pid_running(pidfile="/tmp/radiusparser_po.pid"):
    """
    Check if another instance of the script is running.
    """

    try:
        # Read pid from pidfile
        pf = open(pidfile, 'r')
        pid = int(pf.read().strip())
        pf.close()
    except (IOError, ValueError):
        # If reading the pidfile failed
        pid = None

    try:
        # Check if PID exists. If os.kill() throws exeption, it doesn't.
        # If everything is OK, we let the previous instance run, and exit this
        # one.
        os.kill(pid, 0)
        return True

    except (OSError, TypeError):
        # Create/update PID-file
        pf = open(pidfile, 'w')
        pf.write(str(os.getpid()))

        return False


##############################################################################
# The Tail Class is written by Jon More, and is Copyright (C) 2005 by The
# Trustees of the University of Pennsylvania
##############################################################################
__license__ = 'Python Software Foundation License'  # Grabbed from code.activestate.com


from os import stat
from os.path import abspath
from stat import ST_SIZE
from time import sleep, time


class Tail(object):
    """The Tail monitor object."""

    def __init__(
        self, path, only_new=False, min_sleep=1, sleep_interval=1, max_sleep=60
    ):
        """Initialize a tail monitor.
        path: filename to open
        only_new: By default, the tail monitor will start reading from
          the beginning of the file when first opened. Set only_new to
          True to have it skip to the end when it first opens, so that
          you only get the new additions that arrive after you start
          monitoring.
        min_sleep: Shortest interval in seconds to sleep when waiting
          for more input to arrive. Defaults to 1.0 second.
        sleep_interval: The tail monitor will dynamically recompute an
          appropriate sleep interval based on a sliding window of data
          arrival rate. You can set sleep_interval here to seed it
          initially if the default of 1.0 second doesn't work for you
          and you don't want to wait for it to converge.
        max_sleep: Maximum interval in seconds to sleep when waiting
          for more input to arrive. Also, if this many seconds have
          elapsed without getting any new data, the tail monitor will
          check to see if the log got truncated (rotated) and will
          quietly reopen itself if this was the case. Defaults to 60.0
          seconds.
        """

        # remember path to file in case I need to reopen
        self.path = abspath(path)
        self.f = open(self.path, "r")
        self.min_sleep = min_sleep * 1.0
        self.sleep_interval = sleep_interval * 1.0
        self.max_sleep = max_sleep * 1.0
        if only_new:
            # seek to current end of file
            file_len = stat(path)[ST_SIZE]
            self.f.seek(file_len)
        self.pos = self.f.tell()  # where am I in the file?
        self.last_read = time()  # when did I last get some data?
        self.queue = []  # queue of lines that are ready
        self.window = []  # sliding window for dynamically
        # adjusting the sleep_interval

    def _recompute_rate(self, n, start, stop):
        """Internal function for recomputing the sleep interval. I get
        called with a number of lines that appeared between the start and
        stop times; this will get added to a sliding window, and I will
        recompute the average interarrival rate over the last window.
        """
        self.window.append((n, start, stop))
        purge_idx = -1  # index of the highest old record
        tot_n = 0  # total arrivals in the window
        tot_start = stop  # earliest time in the window
        tot_stop = start  # latest time in the window
        for i, record in enumerate(self.window):
            (i_n, i_start, i_stop) = record
            if i_stop < start - self.max_sleep:
                # window size is based on self.max_sleep; this record has
                # fallen out of the window
                purge_idx = i
            else:
                tot_n += i_n
                if i_start < tot_start:
                    tot_start = i_start
                if i_stop > tot_stop:
                    tot_stop = i_stop
        if purge_idx >= 0:
            # clean the old records out of the window (slide the window)
            self.window = self.window[purge_idx + 1 :]
        if tot_n > 0:
            # recompute; stay within bounds
            self.sleep_interval = (tot_stop - tot_start) / tot_n
            if self.sleep_interval > self.max_sleep:
                self.sleep_interval = self.max_sleep
            if self.sleep_interval < self.min_sleep:
                self.sleep_interval = self.min_sleep

    def _fill_cache(self):
        """Internal method for grabbing as much data out of the file as is
        available and caching it for future calls to nextline(). Returns
        the number of lines just read.
        """
        old_len = len(self.queue)
        line = self.f.readline()
        while line != "":
            self.queue.append(line)
            line = self.f.readline()
        # how many did we just get?
        num_read = len(self.queue) - old_len
        if num_read > 0:
            self.pos = self.f.tell()
            now = time()
            self._recompute_rate(num_read, self.last_read, now)
            self.last_read = now
        return num_read

    def _dequeue(self):
        """Internal method; returns the first available line out of the
        cache, if any."""
        if len(self.queue) > 0:
            line = self.queue[0]
            self.queue = self.queue[1:]
            return line
        else:
            return None

    def _reset(self):
        """Internal method; reopen the internal file handle (probably
        because the log file got rotated/truncated)."""
        self.f.close()
        self.f = open(self.path, "r")
        self.pos = self.f.tell()
        self.last_read = time()

    def nextline(self):
        """Return the next line from the file. Blocks if there are no lines
        immediately available."""

        # see if we have any lines cached from the last file read
        line = self._dequeue()
        if line:
            return line

        # ok, we are out of cache; let's get some lines from the file
        if self._fill_cache() > 0:
            # got some
            return self._dequeue()

        # hmm, still no input available
        while True:
            sleep(self.sleep_interval)
            if self._fill_cache() > 0:
                return self._dequeue()
            now = time()
            if now - self.last_read > self.max_sleep:
                # maybe the log got rotated out from under us?
                if stat(self.path)[ST_SIZE] < self.pos:
                    # file got truncated and/or re-created
                    self._reset()
                    if self._fill_cache() > 0:
                        return self._dequeue()

    def close(self):
        """Close the tail monitor, discarding any remaining input."""
        self.f.close()
        self.f = None
        self.queue = []
        self.window = []

    def __iter__(self):
        """Iterator interface, so you can do:

        for line in filetail.Tail('log.txt'):
            # do stuff
            pass
        """
        return self

    def next(self):
        """Kick the iterator interface. Used under the covers to support:

        for line in filetail.Tail('log.txt'):
            # do stuff
            pass
        """
        return self.nextline()


###############################################################################

auth_pattern = re.compile(
    r'^(?P<time>.*) : (?P<type>Auth): (?P<message>(?P<status>.*?): \[(?P<user>.*?)\] '
    r'\(from client (?P<client>[^ ]+) port (?P<port>[^ ]+)( cli (?P<cli>[^ ]+)|)\))\s*$'
)
other_pattern = re.compile(r'^(?P<time>.*) : (?P<type>[^:]+): (?P<message>.*?)\s*$')
ignore_rlmsql = re.compile('Error: rlm_sql')

unknown = []


def parse_line(line):
    """
    Parse a line in the radius error log
    """

    # Try to parse this as an authentication line
    # (the common case by far)
    m = auth_pattern.search(line)
    if m:
        return m
    else:
        # We want to ignore some freeradius sql-errors as well
        m = ignore_rlmsql.search(line)
        if m:
            # unknown.append(line)
            return None
        # I guess it's some other type of line,
        # try to parse that.
        m = other_pattern.search(line)
        if m:
            # Do nothing for now, but this should also
            # go in the database somewhere.
            return m
        else:
            # No, this is something else entirely,
            # let's just skip it for now.
            # unknown.append(line)
            return None


class Row:
    def __init__(self, m):
        self.m = m
        self.time = datetime.datetime.fromtimestamp(mktime(strptime(m.group('time'))))

    def __getattr__(self, attr):
        try:
            return self.m.group(attr)
        except IndexError:
            return ''

    def __repr__(self):
        return repr(self.m.groupdict())

    def __str__(self):
        return str(self.m.groupdict())


def iter_lines(file):
    for line in file:
        m = parse_line(line)
        if m:
            yield Row(m)


###########
# Start   #
###########

if __name__ == '__main__':
    main()
