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
# $Id$
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#
import os, os.path, nav.path
import sys
import ConfigParser

def readConfig(filename, splitChar='='):
    """Reads a key=value type config file. If the specified path does
    not begin at the root, the file is search for in the default NAV
    configuration directory.  Returns a dictionary of the key/value
    pairs that were read."""

    if filename[0] != os.sep:
        filename = os.path.join(nav.path.sysconfdir, filename)

    configuration = {}
    file = open(filename, 'r')
    for line in file.readlines():
        line = line.strip()
        # Unless the line is a comment, we parse it
        if len(line) and line[0] != '#':
            # Split the key/value pair (max 1 split)
            try:
                (key, value) = line.split(splitChar, 1)
                value = value.split('#', 1)[0] # Remove end-of-line comments
                configuration[key.strip()] = value.strip()
            except ValueError:
                sys.stderr.write("Config file %s has errors.\n" % filename)

    file.close()
    return configuration

def getconfig(configfile, defaults=None, configfolder=None):
    """
    Read whole config from file.

    Arguments:
        ``configfile'' the configfile to open
        ``defaults'' are passed on to configparser before reading config.

    Returns:
        Returns a dict, with sections names as keys and a dict for each
        section as values.
    """

    if configfolder:
        file = os.path.join(configfolder, configfile)

    config = ConfigParser.RawConfigParser(defaults)
    config.read(configfile)

    sections = config.sections()
    configdict = {}

    for section in sections:
        configsection = config.items(section)
        sectiondict = {}
        for opt, val in configsection:
            sectiondict[opt] = val
        configdict[section] = sectiondict

    return configdict

