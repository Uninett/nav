# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Uninett AS
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
import os
import importlib
import logging


_logger = logging.getLogger(__name__)
HANDLER_PATTERN = "Checker.py"
CHECKER_DIR = os.path.join(os.path.dirname(__file__), "checker")

checkers = {}
dirty = []  # store failed imports here


def register(key, module):
    if key not in checkers:
        _logger.debug("Registering checker %s from module %s", key, module)
        checkers[key] = module


def get(checker):
    """Gets a specific checker class from its short handler name"""
    if checker in dirty:
        return
    if checker not in checkers:
        parsedir()
        # apparently, the following is required for proper plugin imports on Python 3
        importlib.import_module("nav.statemon.checker")
    module_name = class_name = checkers.get(checker.lower(), '')
    if not module_name:
        return
    try:
        module = importlib.import_module('.' + module_name, 'nav.statemon.checker')
    except Exception as ex:  # noqa: BLE001
        _logger.error("Failed to import %s, %s", module_name, ex)
        dirty.append(checker)
        return
    return getattr(module, class_name)


def parsedir():
    """Finds potential checker modules in the CHECKER_DIR"""
    fnames = os.listdir(CHECKER_DIR)
    for fname in fnames:
        if fname.endswith(HANDLER_PATTERN):
            key = fname.removesuffix(HANDLER_PATTERN).lower()
            handler = fname[:-3]
            register(key, handler)
