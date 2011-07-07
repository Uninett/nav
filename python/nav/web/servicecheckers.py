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
"""Utility functions to find available servicemon checker plugins"""

import os
import re
import nav.statemon.checker

_checkerDir = os.path.dirname(nav.statemon.checker.__file__)
_checkerPattern = "Checker.py"
_descrPattern = 'Checker.descr'
_defaultArgs = ['port', 'timeout']
_regexp = re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)", re.M)

def getCheckers():
    """
    Returns a list of available checkers.
    """
    files = os.listdir(_checkerDir)
    result = []
    for file in files:
        if (len(file) > len(_checkerPattern) and
            file[len(file)-len(_checkerPattern):]==_checkerPattern):
            result.append(file[:-len(_checkerPattern)].lower())
    return result

def getDescription(checkerName):
    """
    Returns a description of the service checker
    """
    descr = {}
    try:
        filename = os.path.join(_checkerDir,
                                "%s%s" % (checkerName.capitalize(),
                                          _descrPattern))
        file = open(filename)
    except:
        return
    for (key, value) in _regexp.findall(file.read()):
        if key == "description":
            descr[key] = value
        else:
            descr[key] = value.split(' ')
    return descr
