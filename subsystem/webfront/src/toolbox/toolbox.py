# -*- coding: ISO8859-1 -*-
#
# $Id$
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
# Authors: Magnar Sveen <magnars@idi.ntnu.no>
#
"""
This module represents the toolbox of the NAV web interface.  It
follows the mod_python.publisher paradigm.
"""
from mod_python import apache
import nav
from nav import web

def handler(req):
    from nav.web.templates.ToolboxTemplate import ToolboxTemplate
    page = ToolboxTemplate()

    from nav.web import toolbox
    page.tools = toolbox.filterToolList(toolbox.getToolList(), req.session['user'])
    page.path = [("Home", "/"), ("Toolbox", False)]
    req.content_type = "text/html"
    req.write(page.respond())
    return apache.OK
