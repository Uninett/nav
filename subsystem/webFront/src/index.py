####################
#
# $Id$
# This file is part of the NAV project.
# This Python module represents the page index and related
# functionality of the NAV web interface.
#
# Copyright (c) 2003 by NTNU, ITEA nettgruppen
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#
####################
"""
Represents the page index of the NAV web interface.

The module follows the mod_python.publisher paradigm.
"""

#from mod_python import apache
#from nav import blapp
import os
import nav


def index(req):
    
    return """
    <a href="/index.py/toolbox">Toolbox is here, %s</a>
""" %  req.session.id

def toolbox(req):
    from nav.web.templates.ToolboxTemplate import ToolboxTemplate
    page = ToolboxTemplate()

    from nav.web import toolbox
    page.tools = toolbox.getToolList()

    return page
