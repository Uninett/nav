#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
from nav.statemon.abstractchecker import AbstractChecker
import nav.statemon.checker

_CHECKER_DIR = os.path.dirname(nav.statemon.checker.__file__)
_CHECKER_PATTERN = "Checker.py"
_DEFAULT_ARGS = ['port', 'timeout']
_ASSIGNMENT_PATTERN = re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)", re.M)


def get_checkers():
    """Returns a list of available servicemon checkers"""
    return [f[:-len(_CHECKER_PATTERN)].lower() for f in get_checker_modules()]


def get_descriptions(checker_names):
    """Returns metadata about the checkers"""
    checker_modules = get_checker_modules_as_dict()
    return {c: get_description(c, checker_modules) for c in checker_names}


def get_description(checker_name, checkers=None):
    """Returns a description of a service checker"""
    if checkers is None:
        checkers = get_checker_modules_as_dict()
    if checker_name not in checkers:
        return
    checker = checkers[checker_name]

    result = {
        'description': checker.DESCRIPTION,
        'args': checker.ARGS,
        'optargs': checker.OPTARGS,
    }
    return result


def get_checker_modules_as_dict():
    """Load all checker classes and construct a dictionary of the result"""
    return {c.get_type(): c for c in load_checker_classes()}


def load_checker_classes():
    """Imports service checker modules, returning checker classes in a list.

    :returns: A list of AbstractChecker subclasses.

    """
    module_names = ("nav.statemon.checker.%s" % os.path.splitext(f)[0]
                    for f in get_checker_modules())
    modules = (m for m in (_import_or_none(n) for n in module_names) if m)
    checkers = set()
    for mod in modules:
        for value in vars(mod).values():
            try:
                if (issubclass(value, AbstractChecker)
                    and value is not AbstractChecker):
                    checkers.add(value)
            except TypeError:
                pass

    return checkers


def _import_or_none(module_name):
    try:
        return __import__(module_name, fromlist=['*'])
    except ImportError:
        return


def get_checker_modules():
    """Returns a list of available servicemon checker modules"""
    try:
        files = os.listdir(_CHECKER_DIR)
    except OSError:
        return []

    return [f for f in files
            if len(f) > len(_CHECKER_PATTERN) and f.endswith(_CHECKER_PATTERN)]
