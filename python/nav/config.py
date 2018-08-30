#
# Copyright (C) 2008, 2009, 2013, 2017, 2018 Uninett AS
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
"""Utility functions for NAV configuration file discovery and parsing."""
from __future__ import absolute_import

import errno
import io
import logging

import os
import sys
import configparser

from django.utils import six

from nav.errors import GeneralException
from . import buildconf

_logger = logging.getLogger(__name__)

# Potential locations to find configuration files
CONFIG_LOCATIONS = [
    os.path.expanduser('~/.local/etc/nav'),
    os.path.expanduser('~/.local/etc'),
    os.path.expanduser('~/.config/nav'),
    '/etc/nav',
    buildconf.sysconfdir,
]


def read_flat_config(config_file, delimiter='='):
    """Reads a key=value type config file into a dictionary.

    :param config_file: the configuration file to read; either a file name
                        or an open file object. If the filename is not an
                        absolute path, NAV's configuration directory is used
                        as the base path.
    :param delimiter: the character used to assign values in the config file.
    :returns: dictionary of the key/value pairs that were read.
    """

    if isinstance(config_file, six.string_types):
        config_file = open_configfile(config_file)

    configuration = {}
    for line in config_file.readlines():
        line = line.strip()
        # Unless the line is a comment, we parse it
        if len(line) and line[0] != '#':
            # Split the key/value pair (max 1 split)
            try:
                (key, value) = line.split(delimiter, 1)
                value = value.split('#', 1)[0] # Remove end-of-line comments
                configuration[key.strip()] = value.strip()
            except ValueError:
                sys.stderr.write("Config file %s has errors.\n" %
                                 config_file.name)

    return configuration


def getconfig(configfile, defaults=None):
    """Reads an INI-style configuration file into a two-level dictionary.

    :param configfile: the configuration file to read, either a name or an
                       open file object.
    :param defaults: A dict that is passed on to the underlying ConfigParser.
    :returns: Returns a dict, with sections names as keys and a dict for each
              section as values.

    """
    if isinstance(configfile, six.string_types):
        configfile = open_configfile(configfile)

    config = configparser.RawConfigParser(defaults)
    config.read_file(configfile)

    sections = config.sections()
    configdict = {}

    for section in sections:
        configsection = config.items(section)
        configdict[section] = dict(configsection)

    return configdict


class NAVConfigParser(configparser.ConfigParser):
    """A ConfigParser for NAV config files with some NAV-related
    simplifications.

    A NAV subsystem utilizing an INI-type config file can subclass this
    class and define only the DEFAULT_CONFIG and the DEFAULT_CONFIG_FILES
    class variables to be mostly self-contained.

    Any file listed in the class variable DEFAULT_CONFIG_FILES will be
    attempted read from any of NAV's accepted configuration directories and
    from the current working directory upon instantation of the parser
    subclass.

    """
    DEFAULT_CONFIG = u""
    DEFAULT_CONFIG_FILES = ()

    def __init__(self, default_config=None, default_config_files=None):
        if default_config is not None:
            self.DEFAULT_CONFIG = default_config
        if default_config_files is not None:
            self.DEFAULT_CONFIG_FILES = default_config_files

        configparser.ConfigParser.__init__(self)
        # TODO: perform sanity check on config settings
        faked_default_file = io.StringIO(self.DEFAULT_CONFIG)
        self.readfp(faked_default_file)
        self.read_all()

    def read_all(self):
        """Reads all config files in DEFAULT_CONFIG_FILES"""
        filenames = [f for f in (find_configfile(name)
                                 for name in self.DEFAULT_CONFIG_FILES)
                     if f]
        filenames.extend(os.path.join('.', name)
                         for name in self.DEFAULT_CONFIG_FILES)
        files_read = self.read(filenames)

        if files_read:
            _logger.debug("Read config files %r", files_read)
        else:
            _logger.debug("Found none of %r", filenames)
        return files_read


class NavConfigParserDefaultSection(object):
    """A ConfigParser for NAV config files with some NAV-related
    simplifications and use a default section.

    See NavConfigParser for more details.
    """
    DEFAULT_CONFIG_FILES = ()
    DEFAULT_CONFIG = ""

    def __init__(self, section):
        self.parser = NAVConfigParser(self.DEFAULT_CONFIG,
                                      self.DEFAULT_CONFIG_FILES)
        self.section = section

    def get(self, *args):
        return self.parser.get(self.section, *args)

    def getboolean(self, *args):
        return self.parser.getboolean(self.section, *args)


def find_configfile(filename):
    """Searches for filename in any of the known config file locations

    :returns: The first instance of filename found in the CONFIG_LOCATIONS
              list, or None if the configfile was not found.
    """
    if filename.startswith(os.sep):
        return filename  # IDGAF, you gave me a fully qualified path
    candidates = (os.path.join(directory, filename)
                  for directory in CONFIG_LOCATIONS)
    for name in candidates:
        if os.path.exists(name):
            return name


def open_configfile(filename):
    """Opens and returns a file handle for a given config file.

    The config file will be found using find_configfile()
    """
    name = find_configfile(filename)
    if name:
        return io.open(name, encoding='utf-8')
    else:
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), filename)


class ConfigurationError(GeneralException):
    """Configuration error"""
    pass


try:
    NAV_CONFIG = read_flat_config('nav.conf')
except OSError:
    NAV_CONFIG = {}
