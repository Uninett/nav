# -*- coding: ISO8859-1 -*-
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
"""
"""

import os
import re
try:
    import nav.path
    _checkerDir = os.path.join(nav.path.pythonlibdir, "nav/statemon/checker")
except:
    # not properly installed
    _checkerDir = "/usr/local/nav/navme/subsystem/statemon/lib/checker"
_checkerPattern = "Checker.py"
_descrPattern = 'Checker.descr'
_defaultArgs = ['port', 'timeout']
_regexp=re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)",re.M)

def getCheckers():
    """
    Returns a list of available checkers.
    """
    files = os.listdir(_checkerDir)
    result = []
    for file in files:
        if len(file) > len(_checkerPattern) and file[len(file)-len(_checkerPattern):]==_checkerPattern:
            result.append(file[:-len(_checkerPattern)].lower())
    return result

def getDescription(checkerName):
    """
    Returns a description of the service checker
    """
    descr = {}
    try:
        filename = os.path.join(_checkerDir, "%s%s" % (checkerName.capitalize(), _descrPattern))
        file = open(filename)
    except:
        #print "could not open file ", filename
        return
    for (key, value) in _regexp.findall(file.read()):
        if key == "description":
            descr[key] = value
        else:
            descr[key] = value.split(' ')
    return descr
    
