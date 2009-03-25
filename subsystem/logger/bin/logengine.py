#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2007, 2009 UNINETT AS
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
"""logengine.py inserts Cisco syslog messages into the NAV database.

This program takes no arguments; its operation is configured in the
file logger.conf.

Syslog messages will be read from the configured file, parsed and
inserted into structured NAV database tables.  Messages that cannot be
parsed as Cisco syslog messages are ignored.

The syslog file is truncated upon the exit of this program.  If you
wish to keep a copy of the syslog messages on file, you should
configure your syslog daemon to log the messages to two separate
files, one of which this program will have exclusive access to.

"""

## The structure in this file is not good, but understandable. It is easy
## to see that this file is converted from procedure oriented perl code.
## go down to the main part first if you want to know what this is all
## about.

import re
import fcntl
import sys
import os
import os.path
import atexit
import logging
from ConfigParser import ConfigParser

from mx import DateTime

import nav
import nav.logs
from nav import db
from nav import daemon
from nav.buildconf import localstatedir


config = ConfigParser()
config.read(os.path.join(nav.path.sysconfdir,'logger.conf'))
logfile = config.get("paths","syslog")
if config.has_option("paths", "charset"):
    logfile_charset = config.get("paths", "charset")
else:
    logfile_charset = "ISO-8859-1"

logging.basicConfig()
logger = logging.getLogger('logengine')
connection = db.getConnection('logger','logger')
database = connection.cursor()

def get_exception_dicts(config):

    options = config.options("priorityexceptions")

    exceptionorigin = {}
    exceptiontype = {}
    exceptiontypeorigin = {}
    exceptions = {}
    for option in options:
        newpriority = config.get("priorityexceptions", option)
        op = re.split("@",option)
        if len(op) == 1:
            exceptions[op[0]] = newpriority
        if len(op) == 2:
            any = re.compile("any",re.I)
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

    return (exceptionorigin,exceptiontype,exceptiontypeorigin)

# Examples of typical log lines that must be matched by the following
# regexp:

# Feb  8 12:58:40 158.38.0.51 316371: Feb  8 12:58:39.873 MET: %SEC-6-IPACCESSLOGDP: list 112 permitted icmp 158.38.60.10 -> 158.38.12.5 (0/0), 1 packet
# Mar 20 10:27:26 sw_1 607977: Mar 20 2009 10:20:06: %SEC-6-IPACCESSLOGP: list fraVLAN800 denied tcp x.x.x.x(1380) -> y.y.y.y(80), 2 packets
# Mar 25 10:54:25 somedevice 72: AP:000b.adc0.ffee: *Mar 25 10:15:51.666: %LINK-3-UPDOWN: Interface Dot11Radio0, changed state to up

typicalmatchRe = re.compile(
    """
    ^
    (?P<servmonth>\w+) \s+ (?P<servday>\d+) \s+        # server month and date
    (?P<servhour>\d+) \: (?P<servmin>\d+) : \d+ \W+    # server hour/min/second
    (?P<origin>\S+)                                    # origin
    \W+ (?:(\d{4}) | .*?) \s+ \W*                      # year/msg counter/garbage
    (?P<month>\w+) \s+ (?P<day>\d+) \s+                # origin month and date
    ((?P<year>\d{4}) \s+ )?                            # origin year, if present
    (?P<hour>\d+) : (?P<min>\d+) : (?P<second>\d+)     # origin hour/minute/second
    .* %                                               # eat chars until % appears
    (?P<type>.*?) :                                    # message type
    \s* (?P<description>.*)                            # message (without leading spaces)
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
        msgtype = match.group('type')
        description = match.group('description')

        timestamp = DateTime.DateTime(year,month,day,hour,minute)

        return Message(timestamp, origin, msgtype, description)

    else:
        # if this message shows sign of cisco format, put it in the error log
        typematch = typematchRe.search(line)
        if typematch:
            database.execute("INSERT INTO errorerror (message) "
                             "VALUES (%s)", (line,))
            connection.commit()

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
        (self.facility, self.priorityid, self.mnemonic) = self.find_priority(type)

    def find_priority(self, type):
        prioritymatch = self.prioritymatchRe.search(type)
        if prioritymatch:
            return (prioritymatch.group(1), int(prioritymatch.group(2)), prioritymatch.group(3))
        else:
            return (None, None, None)

    def find_category(self, origin):
                
        categorymatch = self.categorymatchRe.search(origin)
        if categorymatch:
            return categorymatch.group(1)
        else:
            return "rest"

def find_year(mnd):

    now = DateTime.now().tuple()
    if mnd==12 and now[1]==1:
        return now[0]-1
    else:
        return now[0]
    
def find_month(textual):
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
              "oct", "nov", "dec"]
    try:
        return months.index(textual.lower())+1
    except ValueError, e:
        pass



if __name__ == '__main__':
    nav.logs.setLogLevels()
    # Create a pidfile and delete it automagically when the process exits.
    # Although we're not a daemon, we do want to prevent multiple simultaineous
    # logengine processes.
    pidfile = os.path.join(localstatedir, 'run', 'logengine.pid')

    try:
        daemon.justme(pidfile)
    except daemon.AlreadyRunningError, e:
        print >> sys.stderr, "logengine is already running (%d)" % e.pid
        sys.exit(1)
        
    daemon.writepidfile(pidfile)
    atexit.register(daemon.daemonexit, pidfile)

    ## initial setup of dictionaries

    categories = {}
    database.execute("select category from category")
    for r in database.fetchall():
        if not categories.has_key(r[0]):
            categories[r[0]] = r[0]
    
    origins = {}
    database.execute("select origin, name from origin")
    for r in database.fetchall():
        if not origins.has_key(r[1]):
            origins[r[1]] = int(r[0])

    types = {}
    database.execute("select type, facility, mnemonic, priority from log_message_type")
    for r in database.fetchall():
        if not types.has_key(r[1]): 
            types[r[1]] = {}
        if not types[r[1]].has_key(r[2]):
            types[r[1]][r[2]] = int(r[0])

    ## parse priorityexceptions
    (exceptionorigin,
     exceptiontype,
     exceptiontypeorigin) =  get_exception_dicts(config)

    ## delete old records
    ## the limits for what is old is specified in the logger.conf
    ## configuration file
    for priority in range(0,8):
        if config.get("deletepriority",str(priority)):
            days = config.getint("deletepriority", str(priority))
            database.execute("DELETE FROM log_message WHERE newpriority=%s "
                             "AND time < now() - interval %s",
                             (priority, '%d days' % days))

    #get rid of old records before filling up with new (old jungle proverb)
    connection.commit()


    ## add new records
    ## the new records are read from the cisco syslog file specified 
    ## by the syslog path in the logger.conf configuration file

    f = None
    ## open log
    try:
        f = open(logfile, "r+")
    except IOError, e:
        # If errno==2 (file not found), we ignore it.  We won't needlessly
        # spam the NAV admin every minute with a file not found error!
        if e.errno != 2:
            print >> sys.stderr, "Couldn't open logfile %s: %s" % (logfile, e)

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
            line = line.decode(logfile_charset).encode("UTF-8")
            try:
                message = createMessage(line)
            except Exception, e:
                logger.exception("Unhandled exception during message parse: %s",
                                 line)
                continue
            if message:

                ## check origin (host)
                if origins.has_key(message.origin):
                    originid = origins[message.origin]

                else:
                    ## update category database table
                    if not categories.has_key(message.category):
                        database.execute("INSERT INTO category (category) "
                                         "VALUES (%s)", (message.category,))
                        categories[message.category] = message.category

                    ## update origin database table
                    database.execute("SELECT nextval('origin_origin_seq')")
                    originid = database.fetchone()[0]
                    database.execute("INSERT INTO origin (origin, name, "
                                     "category) VALUES (%d, %s, %s)",
                                     (originid, message.origin,
                                      message.category))
                    origins[message.origin] = originid

                ## check type
                if types.has_key(message.facility) and types[message.facility].has_key(message.mnemonic):
                    typeid = types[message.facility][message.mnemonic]

                else:
                    ## update type database table
                    database.execute("SELECT nextval('log_message_type_type_seq')")
                    typeid = int(database.fetchone()[0])

                    database.execute("INSERT INTO log_message_type (type, facility, "
                                     "mnemonic, priority) "
                                     "VALUES (%d, %s, %s, %d)",
                                     (typeid, message.facility,
                                      message.mnemonic, message.priorityid))
                    if not types.has_key(message.facility):
                        types[message.facility] = {}
                    types[message.facility][message.mnemonic] = typeid

                ## overload priority if exceptions are set
                if exceptiontypeorigin.has_key(message.type.lower()) and exceptiontypeorigin[message.type.lower()].has_key(message.origin.lower()):
                    try:
                        message.priorityid = int(exceptiontypeorigin[message.type.lower()][message.origin.lower()])
                    except:
                        pass

                elif exceptionorigin.has_key(message.origin.lower()):
                    try:
                        message.priorityid = int(exceptionorigin[message.origin.lower()])
                    except:
                        pass

                elif exceptiontype.has_key(message.type.lower()):
                    try:
                        message.priorityid = int(exceptiontype[message.type.lower()])
                    except:
                        pass

                ## insert message into database
                database.execute("INSERT INTO log_message (time, origin, "
                                 "newpriority, type, message) "
                                 "VALUES (%s, %s, %s, %s, %s)",
                                 (str(message.time), originid,
                                  message.priorityid, typeid,
                                  message.description))

        connection.commit()


