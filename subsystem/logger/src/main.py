#
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

from nav import db
import psycopg
connection = db.getConnection('webfront','manage')
database = connection.cursor()

def handler(req):

    #fieldstorage variables
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)


database.execute("select netaddr from prefix inner join vlan using (vlanid) where nettype='scope'")


database.execute("select id, name, category from origin order by id")
origin = database.fetchall()
#category = []
#for r in database.fetchall():
#    origin[r[0]] = r[1]

database.execute("select id, facility, mnemonic, keyword, description from type order by id")
type = database.fetchall()
#for r in database.fetchall():
#    type[r[0]] = r[1]+"("+r[3]+")"+r[2]

database.execute("select id, priority, keyword, description from priority order by id")
priority = database.fetchall()
#for r in database.fetchall():
#    priority[r[0]] = r[1]+" - "+r[2]

constraints = []
if req.form.has_key("from"):
    constraints.append("time >= %s" % req.form.from)
if req.form.has_key("to"):
    constraints.append("time <= %s" % req.form.to)
if priorityid:
    constraints.append("priority = %s" % priorityid)
if category:
    constraints.append("category = %s" % category)

where = " and ".join(constraints)


## vis alt

if not error:


    if originid and typeid or originid and log or typeid and log:
        database.execute("select time,originid,facility,type.priorityid,mnemonic,message from message join type on type.id=typeid where %s order by time desc", %s)
        noerrtable = database.fetchall()

        if len(noerrtable):
            ### view table
            pass

        else:
            ### nothin
            pass



    elif originid or typeid or priorityid:
        ## statistikk

        database.execute("select originid, count(*) as count from message_view where %s group by originid order by count desc", where)
        origins = database.fetchall()

        database.execute("select count(*) from message_view where %s", where)
        messages = database.fetchall()

        database.execute("select typeid, count(*) as count from message_view where %s group by typeid order by count desc", where)
        types = database.fetchall()

        if len(origins):
            ## print origins
            pass
        if len(types):
            ## print types
            pass


    else:
        ## frontpage / priorities
    pass
    
else:

    ## errors

    database.execute("select message from errorerror order by id")
    errors = database.fetchall()
