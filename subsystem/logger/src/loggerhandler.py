# -*- coding: ISO8859-1 -*-
# $Id: report.py 2674 2004-04-28 13:03:41Z mortenv $
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
# Authors: Sigurd Gartmann <sigurd-nav@brogar.org>
#
from mod_python import apache,util

import os
import nav
from nav import db
import psycopg
import re
from mx import DateTime
from ConfigParser import ConfigParser
from nav.web.templates.LoggerTemplate import LoggerTemplate

DATEFORMAT = "%Y-%m-%d %H:%M:%S"
DOMAIN_SUFFICES = [s.strip() for s in nav.config.readConfig("nav.conf")["DOMAIN_SUFFIX"].split(",")]


def handler(req):
    connection = db.getConnection('webfront','logger')
    database = connection.cursor()

    #fieldstorage variables
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)

    if req.form.has_key("tfrom") and req.form["tfrom"]:
        tfrom = DateTime.strptime(req.form["tfrom"], DATEFORMAT)
    else:
        tfrom = DateTime.now() - DateTime.oneDay

    if req.form.has_key("tto") and req.form["tto"]:
        tto = DateTime.strptime(req.form["tto"], DATEFORMAT)
    else:
        tto = DateTime.now()

    database.execute("select origin, name from origin order by origin")
    origins = []
    originid2origin = {}
    origin2originid = {}
    origins.append((0,"(All)"))
    for r in database.fetchall():
        shortorigin = r[1]
        origin2originid[shortorigin] = r[0]
        for d in DOMAIN_SUFFICES:
            shortorigin = re.sub(d,"",r[1])
        origins.append((r[0], shortorigin))
        originid2origin[r[0]] = shortorigin
        
        # should maybe make this dependant on wether it already exists
        origin2originid[shortorigin] = r[0]
        
    database.execute("select category from category order by category")
    categories = database.fetchall()
    categories.insert(0,("(All)",))

    database.execute("select priority, facility, mnemonic, type from log_message_type order by priority, facility, mnemonic")
    types = []
    typeid2type = {}
    type2typeid = {}
    types.append((0,"(All)","",""))
    for r in database.fetchall():
        types.append((r[3], "%s-%d-%s" % (r[1], r[0], r[2])))
        type2typeid["%s-%d-%s" % (r[1], r[0], r[2])] = r[3]
        typeid2type[r[3]] = "%s-%d-%s" % (r[1], r[0], r[2])

    database.execute("select priority, keyword, description from priority order by priority")
    priorities = []
    priorities.append(("-", "(All)", ""))
    for r in database.fetchall():
        priorities.append((r[0], "%s - %s" % (r[0], r[1]), r[2]))
        
    origin = None
    originid = None
    type = None
    typeid = None
    priority = None
    category = None

    links = []
    constraints = []
    constraints.append("time >= '%s'" % tfrom.strftime(DATEFORMAT))
    constraints.append("time <= '%s'" % tto.strftime(DATEFORMAT))
    links.append("tfrom=%s" % tfrom.strftime(DATEFORMAT))
    links.append("tto=%s" %tto.strftime(DATEFORMAT))
    if req.form.has_key("priority") and not req.form["priority"] == "-":
        priority = req.form["priority"]
        constraints.append("newpriority = %s" % priority)
        links.append("priority=%s" % priority)
    if req.form.has_key("type") and req.form["type"] and type2typeid.has_key(req.form["type"]):
        type = req.form["type"]
        typeid = type2typeid[type]
        constraints.append("type = %d" % typeid)
        links.append("type=%s" % type)
    if req.form.has_key("origin") and req.form["origin"] and origin2originid.has_key(req.form["origin"]):
        origin = req.form["origin"]
        originid = origin2originid[origin]
        constraints.append("origin = %d" % originid)
        links.append("origin=%s" % originid2origin[originid])
    if req.form.has_key("category") and req.form["category"] > '0':
        category = req.form["category"]
        constraints.append("category = '%s'" % category)
        links.append("category=%s" % category)

    where = " and ".join(constraints)
    link = "&amp;".join(links)

    page = LoggerTemplate()
    page.path = [("Home","/"),("Syslog Analyzer",None)]
    page.priority = priority
    page.origin = origin
    page.originid = originid
    page.category = category
    page.type = type
    page.typeid = type
    page.tto = tto.strftime(DATEFORMAT)
    page.tfrom = tfrom.strftime(DATEFORMAT)

    page.priorities = priorities
    page.types = types
    page.categories = categories
    page.origins = origins
    page.origindict = originid2origin
    page.typedict = typeid2type

    page.link = link
    
    ## vis alt
    if req.form.has_key("error"):
        error = 1
    else:
        error = 0
    if req.form.has_key("exception"):
        exception = 1
    else:
        exception = 0
    if req.form.has_key("log"):
        log = 1
    else:
        log = 0
        
    if not error and not exception:

        if origin and type or origin and log or type and log:
            ## log

            #where = re.sub("priority","newpriority",where)
            database.execute("select time, origin, newpriority, priority, facility, mnemonic, message from log_message inner join log_message_type USING (type) inner join origin USING (origin) where %s order by time desc" % where)
            #raise repr("select time, name, newpriority, facility, mnemonic, message from message inner join type USING (type) inner join origin USING (origin) where %s order by time desc" % where)
            log = []
            for l in database.fetchall():
                log.append(LogMessage(l[0], originid2origin[l[1]], l[2], l[3], l[4], l[5], l[6]))
            page.log = log
            page.mode = "log"
            page.total = database.rowcount

        elif origin or type or priority and not priority == "-":
            ## statistikk

            page.mode = "statistics"
            database.execute("select origin, count(*) as count from message_view where %s group by origin order by count desc" % where)
            page.originlist = database.fetchall()

            database.execute("select type, count(*) as count from message_view where %s group by type order by count desc" % where)
            page.typelist = database.fetchall()

            database.execute("select count(*) from message_view where %s" % where)
            page.total = database.fetchone()[0]

        else:
            ## frontpage / priorities

            database.execute("select newpriority, count(*) as count from message_view WHERE %s group by newpriority order by newpriority" % where)
            page.priorityresult = {}
            for p in database.fetchall():
                page.priorityresult[p[0]] = p[1]
                
            page.mode = "priority"

    else:

        if exception:
        ## list priority exceptions
        
            config = ConfigParser()
            config.read(os.path.join(nav.path.sysconfdir,'logger.conf'))
            options = config.options("priorityexceptions")
            exceptions = []
            for option in options:
                newpriority = config.get("priorityexceptions", option)
                exceptions.append((option, newpriority))
            page.exceptions = exceptions
            page.mode = "exception"
                
        else:
        ## errors
        
            database.execute("select message from errorerror order by id desc")
            page.errors = database.fetchall()
            page.mode = "error"
            page.total = database.rowcount
        
    req.content_type = "text/html"
    req.write(page.respond())

    return apache.OK

class LogMessage:

    def __init__(self, time, originname, newpriority, priority, facility, mnemonic, message):
        self.time = time.strftime(DATEFORMAT)
        self.origin = originname
        if isinstance(newpriority,int):
            self.type = "%s-%d(%d)-%s" % (facility, newpriority, priority, mnemonic)
        else:
            self.type = "%s-%d-%s" % (facility, priority, mnemonic)
        self.message = message
        
