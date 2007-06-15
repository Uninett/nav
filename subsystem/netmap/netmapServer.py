# -*- coding: UTF-8 -*-
#
# Copyright 2007 UNINETT AS
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
# Authors: Kristian Klette <klette@samfundet.no>

# A small web-service to output structured output of netpoints and the links between them.
import sys
import psycopg
import nav.db

from common import *
from dataCollector import *
from output import *

# Try-catch hack so we can use console as well..
console = False
try:
    from mod_python import apache, util
except:
    console = True
    pass

def handler(req):
    connection = nav.db.getConnection()
    db = connection.cursor()

    netboxes = getData(db)

    req.content_type="text/txt"

    req.write( returnSimpleXML(netboxes) );

    return apache.OK
