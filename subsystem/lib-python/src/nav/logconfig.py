# -*- coding: utf-8 -*-
#
# Copyright 2006 UNINETT AS
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
"""Logging configuration related functions for the Python parts of NAV."""

__author__ = "Morten Vold <morten.vold@uninett.no>"

import os.path
import logging
import ConfigParser
import nav.path

def setLogLevels():
    """Read the logging config file and set up log levels for the different
    loggers."""
    logConfFile = os.path.join(nav.path.sysconfdir, 'logging.conf')
    config = ConfigParser.ConfigParser()
    config.read(logConfFile)
    
    for loggerName in config.options('levels'):
        level = config.get('levels', loggerName)
        # Allow the config file to specify the root logger as 'root'
        if loggerName.lower() == 'root':
            loggerName = ''
        logger = logging.getLogger(loggerName)

        # Allow log levels to be specified as either names or values.
        # Translate any non-integer levels to integer first.
        if not level.isdigit():
            level = logging.getLevelName(level)
        try:
            level = int(level)
        except ValueError:
            # Default to INFO
            level = logging.INFO
        logger.setLevel(level)
