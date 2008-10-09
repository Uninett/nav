# -*- coding: ISO8859-1 -*-
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
# $Id$
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#
"""
This module contains functionality related to the web toolbox.
"""
from nav import config
import os, os.path
import nav.auth, nav.web, nav.path

def _compareTools(x, y):
    """
    Internal function to compare two tools for sorting purposes
    """
    # Do a standard comparison of priority values (to accomplish an
    # ascendingg sort, we negate the priorities)
    ret = cmp(-x.priority, -y.priority)
    # If priorities were equal, sort by name instead
    if not ret:
        ret = cmp(x.name.upper(), y.name.upper())
    return ret
    
def getToolList():
    """ Searches the configured list of paths for *.tool files and
    returns a list of Tool objects representing these files"""
    paths = {}
    if nav.web.webfrontConfig.has_option('toolbox', 'path'):
        paths = nav.web.webfrontConfig.get('toolbox', 'path').split(os.pathsep)
    else:
        return None

    list = []
    for path in paths:
        if os.access(path, os.F_OK):
            filelist = os.listdir(path)
            for filename in filelist:
                if filename[-5:] == '.tool':
                    fullpath = os.path.join(path, filename)
                    list.append(Tool().load(fullpath))

    # Sort the tool list according to the _cmpTool function
    list.sort(_compareTools)
    return list

def filterToolList(toolList, user):
    """Returns a filtered version of toolList, according to the uri
    privileges of the user."""
    newToolList = []
    for tool in toolList:
        if nav.auth.hasPrivilege(user, 'web_access', tool.uri):
            newToolList.append(tool)
    return newToolList

class Tool:
    def __init__(self):
        self.name = ''
        self.uri = ''
        self.description = ''
        self.icon = ''

    def load(self, filename):
        if filename[0] != os.sep:
            filename = os.path.join(os.getcwd(), filename)
        dict = config.readConfig(filename)
        self.name        = dict['name']
        self.uri         = dict['uri']
        self.description = dict['description']
        self.icon        = dict['icon']
        if dict.has_key('priority'):
            self.priority = int(dict['priority'])
        else:
            self.priority = 0
        
        return self

    def __str__(self):
        return "%s (%s)" % (self.name, self.uri)
