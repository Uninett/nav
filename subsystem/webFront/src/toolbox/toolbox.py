"""
$Id: $

This file is part of the NAV project.

This module represents the toolbox of the NAV web interface.  It
follows the mod_python.publisher paradigm.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Magnar Sveen <magnars@stud.ntnu.no>

"""
from mod_python import apache
import nav
from nav import web

def handler(req):
    from nav.web.templates.ToolboxTemplate import ToolboxTemplate
    page = ToolboxTemplate()

    from nav.web import toolbox
    page.tools = toolbox.filterToolList(toolbox.getToolList(), req.session['user'])
    page.path = [("Frontpage", "/"), ("Tools", False)]
    req.write(page.respond())
    return apache.OK
