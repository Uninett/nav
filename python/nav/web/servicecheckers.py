#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2011 UNINETT AS
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

from __future__ import with_statement
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
    try:
        files = os.listdir(_CHECKER_DIR)
    except OSError:
        return []

    return [f[:-len(_CHECKER_PATTERN)].lower() for f in files
            if len(f) > len(_CHECKER_PATTERN)
            and f.endswith(_CHECKER_PATTERN)]

def get_description(checker_name):
    """Returns a description of a service checker"""
    filename = os.path.join(_CHECKER_DIR,
                            "%s%s" % (checker_name.capitalize(),
                                      _DESCR_PATTERN))
    try:
        with file(filename, 'rb') as descr_file:
            assignments = _ASSIGNMENT_PATTERN.findall(descr_file.read())
            return dict(
                (key, value if key == "description" else value.split(' '))
                for (key, value) in assignments)
    except IOError:
        return
