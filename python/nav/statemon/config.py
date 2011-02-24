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
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#
"""
Abstraction for the various config files used
by servicemon and pinger.
Implements the singleton pattern ensuring only one
instance created.
"""

import os
import sys
import re
from debug import debug

try:
    # this module exists in a properly installed enviroment
    import nav.path
    CONFIGFILEPATH = [nav.path.sysconfdir]
except ImportError:
    # fallback to current dir++
    CONFIGFILEPATH = ['/usr/local/nav/local/etc/conf/', '.']

class Conf(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        self._configfile = None
        for path in CONFIGFILEPATH:
            file = os.path.join(os.path.abspath(path), self._file)
            try:
                self._configfile = open(file, "r")
                break
            except IOError:
                pass

        if self._configfile is None:
            #debug("Failed to open %s" % self._file)
            sys.exit(0)
        self._regexp = re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)", re.M)
        self.parsefile()
        self._configfile.close()

    def parsefile(self):
        for (key, value) in self._regexp.findall(self._configfile.read()):
            if self.validoptions:
                if key.strip() in self.validoptions:
                    self[key.strip()]=value.strip()
            else:
                self[key.strip()]=value.strip()

def dbconf(*args, **kwargs):
    if _dbconf._instance is None:
        _dbconf._instance = _dbconf(*args, **kwargs)
    return _dbconf._instance

class _dbconf(Conf):
    _instance = None
    def __init__(self, *args, **kwargs):
        self._file = kwargs.get('configfile','db.conf')
        # Valid configoptions must be specified in this list
        self.validoptions = []
        Conf.__init__(self, *args, **kwargs)

class _serviceconf(Conf):
    _instance = None
    def __init__(self, *args, **kwargs):
        self._file = kwargs.get('configfile', 'servicemon.conf')
        self.validoptions = []
        Conf.__init__(self, *args, **kwargs)


def serviceconf(*args, **kwargs):
    if _serviceconf._instance is None:
        _serviceconf._instance = _serviceconf(*args, **kwargs)
    return _serviceconf._instance

class _pingconf(Conf):
    _instance = None
    def __init__(self, *args, **kwargs):
        self._file = kwargs.get('configfile','pping.conf')
        self.validoptions = []
        Conf.__init__(self, *args, **kwargs)


def pingconf(*args, **kwargs):
    if _pingconf._instance is None:
        _pingconf._instance = _pingconf(*args, **kwargs)
    return _pingconf._instance



