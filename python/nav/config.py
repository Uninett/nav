# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2008, 2009 UNINETT AS
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
"""Utility functions for NAV configuration file parsing."""

import os
import sys
import ConfigParser

import buildconf

def readConfig(config_file, splitChar='='):
    """Reads a key=value type config file. 

    If the specified path does not begin at the root, the file is
    searched for in the default NAV configuration directory.  

    Arguments:
        ``config_file'' the configuration file to read;  either a file name
                        or an open file object.
        ``splitChar'' the character used to assign values in the config file.

    Returns:
        A dictionary of the key/value pairs that were read.
    """

    if isinstance(config_file, basestring):
        if config_file[0] != os.sep:
            config_file = os.path.join(buildconf.sysconfdir, config_file)
        config_file = file(config_file, 'r')

    configuration = {}
    for line in config_file.readlines():
        line = line.strip()
        # Unless the line is a comment, we parse it
        if len(line) and line[0] != '#':
            # Split the key/value pair (max 1 split)
            try:
                (key, value) = line.split(splitChar, 1)
                value = value.split('#', 1)[0] # Remove end-of-line comments
                configuration[key.strip()] = value.strip()
            except ValueError:
                sys.stderr.write("Config file %s has errors.\n" % 
                                 config_file.name)

    return configuration

# Really, what value does this function add?  Why not use a
# ConfigParser directly?
def getconfig(configfile, defaults=None, configfolder=None):
    """
    Read whole config from an INI-style configuration file.

    Arguments:
        ``configfile'' the configuration file to read, either a name or an 
                       open file object.
        ``defaults'' are passed on to configparser before reading config.

    Returns:
        Returns a dict, with sections names as keys and a dict for each
        section as values.
    """

    if isinstance(configfile, basestring):
        if configfolder:
            configfile = os.path.join(configfolder, configfile)
        configfile = file(configfile, 'r')

    config = ConfigParser.RawConfigParser(defaults)
    config.readfp(configfile)

    sections = config.sections()
    configdict = {}

    for section in sections:
        configsection = config.items(section)
        sectiondict = {}
        for opt, val in configsection:
            sectiondict[opt] = val
        configdict[section] = sectiondict

    return configdict

