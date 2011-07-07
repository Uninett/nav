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

_CHECKER_DIR = os.path.dirname(nav.statemon.checker.__file__)
_CHECKER_PATTERN = "Checker.py"
_DESCR_PATTERN = 'Checker.descr'
_DEFAULT_ARGS = ['port', 'timeout']
_ASSIGNMENT_PATTERN = re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)", re.M)

def get_checkers():
    """Returns a list of available servicemon checkers"""
    files = os.listdir(_CHECKER_DIR)
    result = []
    for file in files:
        if (len(file) > len(_CHECKER_PATTERN) and
            file[len(file)-len(_CHECKER_PATTERN):]==_CHECKER_PATTERN):
            result.append(file[:-len(_CHECKER_PATTERN)].lower())
    return result

def get_description(checker_name):
    """Returns a description of a service checker"""
    descr = {}
    try:
        filename = os.path.join(_CHECKER_DIR,
                                "%s%s" % (checker_name.capitalize(),
                                          _DESCR_PATTERN))
        file = open(filename)
    except:
        return
    for (key, value) in _ASSIGNMENT_PATTERN.findall(file.read()):
        if key == "description":
            descr[key] = value
        else:
            descr[key] = value.split(' ')
    return descr
