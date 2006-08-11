#! /usr/bin/env python
# -*- coding: ISO8859-1 -*-
#
# Copyright 2006 UNINETT AS
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
# Author: Stein Magnus Jodal <stein.magnus@jodal.no>
#

"""
mod_python handler for Maintenance2 subsystem.
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id:$"

from mod_python import apache

import nav.db
from nav.web.URI import URI
from nav.web.templates.Maintenance2Template import Maintenance2Template

dbconn = nav.db.getConnection('webfront', 'manage')
db = dbconn.cursor()

def handler(req):
    """Handler for the Maintenance 2 subsystem."""

    args = URI(req.unparsed_uri)

    # Setup template
    page = Maintenance2Template()
    req.content_type = 'text/html'
    req.send_http_header()

   
    req.write(page.respond())
    return apache.OK

