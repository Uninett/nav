# -*- coding: utf-8 -*-
#
# Copyright (C) 2006, 2007, 2009, 2011, 2012, 2014, 2017 Uninett AS
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
"""NAV related logging functionality."""

import sys
import os
import logging
import logging.config
from itertools import chain
from typing import Optional
import yaml

import configparser
from nav.config import find_config_file, NAV_CONFIG

DEFAULT_LOG_FORMATTER = logging.Formatter(
    '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
LOGGING_CONF_VAR = 'NAV_LOGGING_CONF'
LOGGING_CONF_FILE_DEFAULT = find_config_file('logging.conf') or ''
LOGGING_YAML_VAR = 'NAV_LOGGING_YAML'
LOGGING_YAML_FILE_DEFAULT = find_config_file('logging.yml') or ''

_logger = logging.getLogger(__name__)


def set_log_config():
    """Set log levels and custom log files"""
    set_log_levels()
    _set_custom_log_file()
    _read_dictconfig_from_yaml_file()


def set_log_levels():
    """
    Read the logging config file and set up log levels for the different
    loggers.
    """
    config = _get_logging_conf()
    if 'levels' not in config.sections():
        return

    for logger_name in config.options('levels'):
        level = config.get('levels', logger_name)
        # Allow the config file to specify the root logger as 'root'
        if logger_name.lower() == 'root':
            logger_name = ''
        _logger = logging.getLogger(logger_name)
        _logger.setLevel(_translate_log_level(level))


def _translate_log_level(level):
    """Allow log levels to be specified as either names or values.

    Translate any non-integer levels to integer first.
    """
    if not level.isdigit():
        level = logging.getLevelName(level)
    try:
        level = int(level)
    except ValueError:
        # Default to INFO
        level = logging.INFO

    return level


def _set_custom_log_file():
    """Read logging config and add additional file handlers to specified logs"""

    config = _get_logging_conf()
    section = 'files'

    if section not in config.sections():
        return

    for logger_name in config.options(section):
        filename = config.get(section, logger_name)
        # Allow the config file to specify the root logger as 'root'
        if logger_name.lower() == 'root':
            logger_name = ''
        _logger = logging.getLogger(logger_name)

        filehandler = logging.FileHandler(_get_logfile_path(filename), encoding='utf-8')
        filehandler.setFormatter(DEFAULT_LOG_FORMATTER)
        _logger.addHandler(filehandler)


def _read_dictconfig_from_yaml_file():
    """Reads legacy logging dictconfig from alternative yaml-based config file, if
    possible.

    This allows for much more flexible logging configuration than NAV's standard logging
    parameters.
    """
    config = _get_logging_yaml()
    if config:
        logging.config.dictConfig(config)


def _get_logging_conf():
    """
    Returns a ConfigParser with the logging configuration to use.

    Unless a specific config file is specified NAV_LOGGING_CONF environment
    variable, the default is to read from the file specified by
    LOGGING_CONF_FILE_DEFAULT .

    """
    filename = os.environ.get(LOGGING_CONF_VAR, LOGGING_CONF_FILE_DEFAULT)
    config = configparser.ConfigParser()
    read = config.read(filename)
    if filename not in read and LOGGING_CONF_VAR in os.environ:
        _logger.error(
            "cannot read logging config from %s, trying default %s",
            filename,
            LOGGING_CONF_FILE_DEFAULT,
        )
        config.read(LOGGING_CONF_FILE_DEFAULT)
    return config


def _get_logging_yaml() -> Optional[dict]:
    """Returns a logging config dict from logging.yaml, if readable"""
    filename = os.environ.get(LOGGING_YAML_VAR, LOGGING_YAML_FILE_DEFAULT)
    try:
        with open(filename, "rb") as yamlconf:
            config = yaml.safe_load(yamlconf)
            _logger.debug("Loaded logging config from %r", filename)
    except OSError as error:
        _logger.debug("Could not load yaml logging config: %r", error)
        return None
    return config


def reset_log_levels(level=logging.WARNING):
    """Resets the log level of all loggers.

    The root logger's level is set to `level`, while other existing loggers in
    the hierarchy are reset to NOTSET.

    """
    root = logging.getLogger('')
    root.setLevel(level)
    all_loggers = root.manager.loggerDict.values()
    for logger in all_loggers:
        if hasattr(logger, 'setLevel'):
            logger.setLevel(logging.NOTSET)


def reopen_log_files():
    """
    Function to iterate over all FileHandlers in the logger hierarchy, close
    their streams and reopen them.
    """
    # Get the manager of the root logger
    root = logging.getLogger()
    manager = root.manager
    mylog = logging.getLogger('nav.logs')
    for logger in chain([root], manager.loggerDict.values()):
        try:
            for hdl in logger.handlers:
                if isinstance(hdl, logging.FileHandler):
                    mylog.debug("Reopening " + hdl.baseFilename)
                    hdl.flush()
                    hdl.acquire()
                    hdl.stream.close()
                    hdl.stream = open(hdl.baseFilename, hdl.mode)
                    hdl.release()
                    mylog.debug("Reopened " + hdl.baseFilename)
        except AttributeError:
            continue


def get_logfile_from_logger(logger=logging.root):
    """Return the file object of the first FileHandler of a given logger.

    This can be used as shorthand for redirecting the low-level stderr
    file descriptor to a log file after daemonization.

    Example usage:
        nav.daemon.daemonize('/var/run/nav/mydaemon.pid',
                             stderr=get_logfile_from_logger())

    Arguments:
        ``logger'' the logger object whose first FileHandler's file will be
                   returned.  If omitted, the root logger is searched for a
                   FileHandler.

    Returns:
        A file object, or None if no FileHandlers were found.

    """
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return handler.stream


def init_stderr_logging(formatter=None, rootlogger=''):
    """Initializes logging to stderr.

    Log levels are read from logging.conf, the root logger's format is set to
    NAV's default format, and its handler is set to a StreamHandler writing
    to sys.stderr.

    """
    init_generic_logging(formatter=formatter, read_config=True, rootlogger=rootlogger)


def init_generic_logging(
    logfile=None,
    stderr=True,
    stdout=False,
    formatter=None,
    read_config=False,
    rootlogger='',
    stderr_level=None,
):
    """Setup logging

    Attempts to cover all the possible existing ways of setting up logging"""

    if 'TIME_ZONE' in NAV_CONFIG:
        os.environ['TZ'] = NAV_CONFIG['TIME_ZONE']

    root = logging.getLogger(rootlogger)

    if stderr or (stdout and sys.stdout.isatty()):
        tty = sys.stderr if stderr else sys.stdout
        tty_handler = logging.StreamHandler(tty)
        formatter = formatter or DEFAULT_LOG_FORMATTER
        tty_handler.setFormatter(formatter)
        if stderr and stderr_level:
            tty_handler.setLevel(stderr_level)
        root.addHandler(tty_handler)

    if logfile:
        try:
            filehandler = logging.FileHandler(
                _get_logfile_path(logfile), encoding='utf-8'
            )
        except IOError:
            pass
        else:
            formatter = formatter or DEFAULT_LOG_FORMATTER
            filehandler.setFormatter(formatter)
            root.addHandler(filehandler)

    if read_config:
        set_log_config()
    else:
        set_log_levels()


def _get_logfile_path(logfile):
    """Returns the fully qualified path to logfile.

    If logfile is an absolute path, it is returned unchanged, otherwise,
    the LOG_DIR path configured in nav.conf will be prepended.
    """
    if not logfile.startswith(os.sep):
        logfile = os.path.join(NAV_CONFIG['LOG_DIR'], logfile)
    return logfile
