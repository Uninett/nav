# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
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
