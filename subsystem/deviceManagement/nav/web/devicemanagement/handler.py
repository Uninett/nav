# -*- coding: UTF-8 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
#
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no
#
"""
mod_python handler for Device Management
"""

### Imports

try:
    from mod_python import util, apache
except:
    pass # To allow use of pychecker

# Devicemanagement imports
from nav.web.devicemanagement.constants import *
from nav.web.devicemanagement.common import *

# Pages
from nav.web.devicemanagement.history import *
from nav.web.devicemanagement.order import *
from nav.web.devicemanagement.register import *
from nav.web.devicemanagement.rma import *
from nav.web.devicemanagement.error import *
from nav.web.devicemanagement.delete import *

### Handler

def handler(req):
    keep_blank_values = True
    req.form = util.FieldStorage(req,keep_blank_values)
    path = req.uri.split(BASEPATH)[1]
    path = path.split('/')

    if path[0] == 'error':
        output = error(req)
    elif path[0] == 'order':
        output = order(req,path)
    elif path[0] == 'delete':
        output = delete(req,path)
    elif path[0] == 'rma':
        output = rma(req,path)
    elif path[0] == 'register':
        output = register(req,path)
    else:
        # Default
        output = history(req)

    if output:
        req.content_type = "text/html"
        req.write(output)
        return apache.OK
    else:
        return apache.HTTP_NOT_FOUND
