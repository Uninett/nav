#
# Copyright (C) 2008, 2009, 2013, 2017, 2018 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Utility functions for NAV configuration file discovery and parsing."""

import errno
import grp
import io
import logging

import os
import sys
import pwd
import stat
import configparser
from pathlib import Path

from nav.errors import GeneralException
from nav.util import resource_files, resource_bytes
from . import buildconf

_logger = logging.getLogger(__name__)

# Potential locations to find configuration files
CONFIG_LOCATIONS = [
    os.path.expanduser('~/.local/etc/nav'),
    os.path.expanduser('~/.local/etc'),
    os.path.expanduser('~/.config/nav'),
    '/etc/nav',
    os.path.join(buildconf.datadir, 'conf'),
]
# If running inside a virtualenv, add that virtualenv to the search path as well:
_base_prefix = (
    # Detect the base prefix in a manner compatible with both old and new virtualenv
    getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix
)
_venv = sys.prefix if sys.prefix != _base_prefix else None
if _venv:
    CONFIG_LOCATIONS = [
        os.path.join(_venv, 'etc'),
        os.path.join(_venv, 'etc/nav'),
        os.path.join(_venv, buildconf.datadir, 'conf'),
    ] + CONFIG_LOCATIONS


def list_config_files_from_dir(dirname):
    return [
        os.path.join(dirname, f)
        for f in sorted(os.listdir(dirname))
        if os.path.isfile(os.path.join(dirname, f))
        and f.endswith(".conf")
        and not f.startswith(".")
    ]


def find_config_dir():
    nav_conf = find_config_file('nav.conf')
    if nav_conf:
        return os.path.dirname(nav_conf)


def read_flat_config(config_file, delimiter='='):
    """Reads a key=value type config file into a dictionary.

    :param config_file: the configuration file to read; either a file name
                        or an open file object. If the filename is not an
                        absolute path, NAV's configuration directory is used
                        as the base path.
    :param delimiter: the character used to assign values in the config file.
    :returns: dictionary of the key/value pairs that were read.
    """

    if isinstance(config_file, str):
        config_file = open_configfile(config_file)

    with config_file:
        configuration = {}
        for line in config_file.readlines():
            line = line.strip()
            # Unless the line is a comment, we parse it
            if line and line[0] != '#':
                # Split the key/value pair (max 1 split)
                try:
                    (key, value) = line.split(delimiter, 1)
                    value = value.split('#', 1)[0]  # Remove end-of-line comments
                    configuration[key.strip()] = value.strip()
                except ValueError:
                    sys.stderr.write("Config file %s has errors.\n" % config_file.name)

        return configuration


def getconfig(configfile, defaults=None):
    """Reads an INI-style configuration file into a two-level dictionary.

    :param configfile: the configuration file to read, either a name or an
                       open file object.
    :param defaults: A dict that is passed on to the underlying ConfigParser.
    :returns: Returns a dict, with sections names as keys and a dict for each
              section as values.

    """
    if isinstance(configfile, str):
        configfile = open_configfile(configfile)

    with configfile:
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

    DEFAULT_CONFIG = ""
    DEFAULT_CONFIG_FILES = ()

    def __init__(self, default_config=None, default_config_files=None):
        if default_config is not None:
            self.DEFAULT_CONFIG = default_config
        if default_config_files is not None:
            self.DEFAULT_CONFIG_FILES = default_config_files

        configparser.ConfigParser.__init__(self)
        # TODO: perform sanity check on config settings
        faked_default_file = io.StringIO(self.DEFAULT_CONFIG)
        self.read_file(faked_default_file)
        self.read_all()

    def read_all(self):
        """Reads all config files in DEFAULT_CONFIG_FILES"""
        filenames = [
            f
            for f in (find_config_file(name) for name in self.DEFAULT_CONFIG_FILES)
            if f
        ]
        filenames.extend(os.path.join('.', name) for name in self.DEFAULT_CONFIG_FILES)
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
        self.parser = NAVConfigParser(self.DEFAULT_CONFIG, self.DEFAULT_CONFIG_FILES)
        self.section = section

    def get(self, *args):
        return self.parser.get(self.section, *args)

    def getboolean(self, *args):
        return self.parser.getboolean(self.section, *args)


def find_config_file(filename):
    """Searches for filename in any of the known config file locations

    :returns: The first instance of filename found in the CONFIG_LOCATIONS
              list, or None if the configfile was not found.
    """
    if filename.startswith(os.sep):
        return filename  # IDGAF, you gave me a fully qualified path
    candidates = (os.path.join(directory, filename) for directory in CONFIG_LOCATIONS)
    for name in candidates:
        if os.path.exists(name):
            return name


def open_configfile(filename):
    """Opens and returns a file handle for a given config file.

    The config file will be found using find_config_file()
    """
    name = find_config_file(filename)
    if name:
        return io.open(name, encoding='utf-8')
    else:
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), filename)


def install_example_config_files(target_directory, overwrite=False, callback=None):
    """Installs a copy of NAV's example configuration files in
    target_directory

    :param target_directory: A valid filesystem path to which we have write
                             access.
    :param overwrite: Existing files are overwritten if this is true.
    :param callback: A function that is called with the full path name of each
                     successfully written file.
    """
    for resource in _config_resource_walk():
        path = _install_single_config_resource_(resource, target_directory, overwrite)
        if callback and path:
            callback(path)


def _config_resource_walk(source=''):
    """Returns a generator that walks the entire tree of example config files
    from available nav package resources. All paths returned will be relative to
    the etc top directory.
    """
    source = Path(source)
    current_path = Path('etc') / source
    for path in resource_files('nav').joinpath(current_path).iterdir():
        name = path.name
        full_name = current_path / name
        relative_name = str(source / name)
        if resource_files('nav').joinpath(full_name).is_dir():
            for path in _config_resource_walk(source=relative_name):
                yield str(path)
        else:
            yield relative_name


def _install_single_config_resource_(source, target, overwrite=False):
    """Installs a single config file resource from the nav packages, rooted at
    the directory named in target.
    """
    resource_path = os.path.join('etc', source)
    dirname = os.path.dirname(source)
    target_directory = os.path.join(target, dirname)
    target_file = os.path.join(target, source)
    if not os.path.exists(target_directory):
        os.makedirs(target_directory, mode=0o755)

    if not overwrite and os.path.exists(target_file):
        return False

    content = resource_bytes('nav', resource_path)
    with open(target_file, 'wb') as handle:
        handle.write(content)
        return target_file


def verify_nav_config(config):
    """Verifies the validity of the most critical options of nav.conf

    :param config: A NAV config dictionary, typically the result of
                   read_flat_config('nav.conf')
    :returns: None, but will raise a ConfigurationError if verification failed.

    """
    if not config:
        return

    # First, verify presence of absolutely required options
    for option in ('NAV_USER', 'LOG_DIR', 'PID_DIR'):
        if option not in config:
            raise ConfigurationError(
                'Configuration option {} is missing!'.format(option)
            )

    # Verify that user exists
    username = config['NAV_USER']
    try:
        pwd.getpwnam(username)
    except KeyError:
        raise ConfigurationError('No such user: {}'.format(username))

    # Verify that directories exist and are writable
    for option, moniker in (('LOG_DIR', 'log'), ('PID_DIR', 'pid file')):
        dir_name = config[option]
        if not os.path.isdir(dir_name):
            raise ConfigurationError(
                'The {} directory {} does not exist or is not a directory'.format(
                    moniker, dir_name
                )
            )
        if not _is_directory_writable_by_user(dir_name, username):
            raise ConfigurationError(
                'The {} directory {} is not writeable for the {} user'.format(
                    moniker, dir_name, username
                )
            )


def _is_directory_writable_by_user(directory, username):
    dir_stat = os.stat(directory)

    user = pwd.getpwnam(username)
    uid, gid = user.pw_uid, user.pw_gid
    dir_mode = dir_stat[stat.ST_MODE]
    dir_uid = dir_stat[stat.ST_UID]
    dir_gid = dir_stat[stat.ST_GID]
    dir_group = grp.getgrgid(dir_gid)

    writeable_owner = uid == dir_uid and stat.S_IRWXU & dir_mode == stat.S_IRWXU
    is_in_group = gid == dir_gid or username in dir_group.gr_mem
    writeable_group = is_in_group and stat.S_IRWXG & dir_mode == stat.S_IRWXG
    writeable_world = stat.S_IRWXO & dir_mode == stat.S_IRWXO

    return writeable_owner or writeable_group or writeable_world


class ConfigurationError(GeneralException):
    """Configuration error"""

    pass


try:
    NAV_CONFIG = read_flat_config('nav.conf')
except OSError:
    NAV_CONFIG = {}
