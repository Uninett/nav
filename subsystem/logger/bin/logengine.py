#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# $Id: main.py 2774 2004-06-04 18:50:41Z gartmann $
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
#


## The structure in this file is not good, but understandable. It is easy
## to see that this file is converted from procedure oriented perl code.

import re
import os
import nav
from mx import DateTime
from nav import db
from ConfigParser import ConfigParser

config = ConfigParser()
config.read(os.path.join(nav.path.sysconfdir,'logger.conf'))
logfile = config.get("paths","syslog")

connection = db.getConnection('logger','logger')
database = connection.cursor()


def createMessage(line):

    typicalmatch = re.search("^(\w+)\s+(\d+)\s+(\d+)\:(\d+):\d+\W+(\S+\.\w+)\W+(?:(\d{4})|.*)\s+\W*(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+).*%(.*?):\s*(.*)$",line)

    if typicalmatch:
        servmonth = find_month(typicalmatch.group(1))
        servyear = find_year(servmonth)
        servday = int(typicalmatch.group(2))
        servhour = int(typicalmatch.group(3))
        servmin = int(typicalmatch.group(4))
        origin = typicalmatch.group(5)
        month = find_month(typicalmatch.group(7))
        year = find_year(month)
        day = int(typicalmatch.group(8))
        hour = int(typicalmatch.group(9))
        min = int(typicalmatch.group(10))
        type = typicalmatch.group(12)
        description = typicalmatch.group(13)

        # does no control of clocks, using servtime
        servtime = DateTime.DateTime(servyear,servmonth,servday,servhour,servmin)
        oritime = DateTime.DateTime(year,month,day,hour,min)

        #stoler på at denne tiden er rett
        servtime = oritime

        
        #print oritime+DateTime.DateTimeDelta(5)

    else:
        notsotypicalmatch = re.search("(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\W+(\S+\.\w+).*\W(\w+\ ??\w*-(\d)-?\w*):\s*(.*)$", line)
        if notsotypicalmatch:
            month = find_month(notsotypicalmatch.group(1))
            year = find_year(month)
            day = int(notsotypicalmatch.group(2))
            hour = int(notsotypicalmatch.group(3))
            min = int(notsotypicalmatch.group(4))
            origin = notsotypicalmatch.group(6)
            type = notsotypicalmatch.group(7)
            priority = int(notsotypicalmatch.group(8))
            message = notsotypicalmatch.group(9)

            servtime = DateTime.DateTime(year,month,day,hour,min)
            
            raise "this is a defined message, but it has no handler"
        
        else:
            raise "this is an undefined message"+line

    #ny prioritet hvis exceptions
    #ikke impl

    return Message(servtime, origin, type, description)

    
class Message:

    def __init__(self, time, origin, type, description):
        self.time = time
        self.origin = origin
        self.category = self.find_category(origin)
        self.type = type
        self.description = description
        (self.facility, self.priorityid, self.mnemonic) = self.find_priority(type)

    def find_priority(self, type):
        prioritymatch = re.search("^(.*)-(\d*)-(.*)$",type)
        if prioritymatch:
            return (prioritymatch.group(1), int(prioritymatch.group(2)), prioritymatch.group(3))
        else:
            return (None, None, None)

    def find_category(self, origin):
                
        categorymatch = re.search("\W(gw|sw|gsw|fw|ts)\W",origin)
        if categorymatch:
            return categorymatch.group(1)
        else:
            return "rest"

#not in use
def find_priority(description):

    prioritymatch = re.search(".*-(\d)-??.*",description)
    if prioritymatch:
        return int(prioritymatch.group(1))

def find_year(mnd):

    now = DateTime.now().tuple()
    if mnd==12 and now[1]==1:
        return now[0]-1
    else:
        return now[0]
    
def find_month(textual):
    textual = textual.lower()

    if textual == "jan":
        return 1
    if textual == "feb":
        return 2
    if textual == "mar":
        return 3
    if textual == "apr":
        return 4
    if textual == "may":
        return 5
    if textual == "jun":
        return 6
    if textual == "jul":
        return 7
    if textual == "aug":
        return 8
    if textual == "sep":
        return 9
    if textual == "oct":
        return 10
    if textual == "nov":
        return 11
    if textual == "dec":
        return 12


if __name__ == '__main__':

    ## initial setup of dictionaries

    categories = {}
    database.execute("select category from category")
    for r in database.fetchall():
        if not categories.has_key(r):
            categories[r] = r
    
    origins = {}
    database.execute("select origin, name from origin")
    for r in database.fetchall():
        if not origins.has_key(r[1]):
            origins[r[1]] = int(r[0])

    types = {}
    database.execute("select type, facility, mnemonic, priority from type")
    for r in database.fetchall():
        if not types.has_key(r[1]): 
            types[r[1]] = {}
        if not types[r[1]].has_key(r[2]):
            types[r[1]][r[2]] = int(r[0])

    ## delete old records
    ## the limits for what is old is specified in the logger.conf
    ## configuration file
    for priority in range(0,8):
        if config.get("deletepriority",str(priority)):
            database.execute("delete from message where newpriority=%d and time<'%s'",(priority, DateTime.now()+DateTime.RelativeDateTime(days=-int(config.get("deletepriority",str(priority))))))

    connection.commit() #get rid of old records before filling up with new (old jungle slogan)


    ## add new records
    ## the new records are read from the cisco syslog file specified 
    ## by the syslog path in the logger.conf configuration file
    f = file(logfile).readlines()

    for line in f:
        message = createMessage(line)

        if origins.has_key(message.origin):
            originid = origins[message.origin]

        else:
            if not categories.has_key(message.category):
                database.execute("insert into category (category) values ('%s')" % message.category)
                categories[message.category] = message.category

            database.execute("select nextval('origin_origin_seq')")
            originid = database.fetchone()[0]
            database.execute("insert into origin (origin, name, category) values (%d, %s, %s)", (originid, message.origin, message.category))
            origins[message.origin] = originid

        if types.has_key(message.facility) and types[message.facility].has_key(message.mnemonic):
            typeid = types[message.facility][message.mnemonic]

        else:
            database.execute("select nextval('type_type_seq')")
            typeid = int(database.fetchone()[0])

            database.execute("insert into type (type, facility, mnemonic, priority) values (%d, %s, %s, %d)", (typeid, message.facility, message.mnemonic, message.priorityid))
            if not types.has_key(message.facility):
                types[message.facility] = {}
            types[message.facility][message.mnemonic] = typeid

        database.execute("insert into message (time, origin, newpriority, type, message) values ('%s', %d, %d, %d, '%s')"% (message.time, originid, message.priorityid, typeid, message.description))

    connection.commit()


