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
"""
Abstraction for the various config files used
by servicemon and pinger.
Implements the singleton pattern ensuring only one
instance created.
"""

import os
from nav.config import read_flat_config, NAV_CONFIG


class Conf(dict):
    def __init__(self, *_args, **_kwargs):
        super(Conf, self).__init__()
        self.update(read_flat_config(self._file))

    @property
    def logfile(self):
        logfile = self.get('logfile')
        if logfile.startswith(os.sep) or not logfile:
            return logfile
        else:
            return os.path.join(NAV_CONFIG['LOG_DIR'], logfile)


def dbconf(*args, **kwargs):
    if _dbconf._instance is None:
        _dbconf._instance = _dbconf(*args, **kwargs)
    return _dbconf._instance


class _dbconf(Conf):
    _instance = None

    def __init__(self, *args, **kwargs):
        self._file = kwargs.get('configfile', 'db.conf')
        super(_dbconf, self).__init__(*args, **kwargs)


class _serviceconf(Conf):
    _instance = None

    def __init__(self, *args, **kwargs):
        self._file = kwargs.get('configfile', 'servicemon.conf')
        super(_serviceconf, self).__init__(*args, **kwargs)


def serviceconf(*args, **kwargs):
    if _serviceconf._instance is None:
        _serviceconf._instance = _serviceconf(*args, **kwargs)
    return _serviceconf._instance


class _pingconf(Conf):
    _instance = None

    def __init__(self, *args, **kwargs):
        self._file = kwargs.get('configfile', 'pping.conf')
        super(_pingconf, self).__init__(*args, **kwargs)


def pingconf(*args, **kwargs):
    if _pingconf._instance is None:
        _pingconf._instance = _pingconf(*args, **kwargs)
    return _pingconf._instance
