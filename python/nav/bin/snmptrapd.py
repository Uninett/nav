#!/usr/bin/env python
# -*- testargs: -h -*-
#
# Copyright (C) 2010, 2013, 2017, 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV daemon to receive and act upon SNMP traps."""

import logging
import os
import re
import socket
import sys
import argparse
import signal
from functools import reduce

# Import NAV libraries
from nav import daemon
from nav.config import NAV_CONFIG, NAVConfigParser
import nav.buildconf
from nav.snmptrapd.plugin import load_handler_modules, ModuleLoadError
from nav.util import is_valid_ip, address_to_string
from nav.db import getConnection
from nav.bootstrap import bootstrap_django
import nav.logs

from nav.snmptrapd import agent

# Paths
logfile_path = os.path.join(NAV_CONFIG['LOG_DIR'], 'snmptrapd.log')
pidfile = 'snmptrapd.pid'
logging.raiseExceptions = False  # don't raise exceptions for logging issues
_logger = logging.getLogger('nav.snmptrapd')
_traplogger = logging.getLogger('nav.snmptrapd.traplog')
handlermodules = None
config = None

DEFAULT_PORT = 162
DEFAULT_ADDRESSES = (('0.0.0.0', DEFAULT_PORT),)
ADDRESS_PATTERNS = (re.compile(r"(?P<addr>[0-9.]+) (:(?P<port>[0-9]+))?$", re.VERBOSE),)
if socket.has_ipv6 and agent.BACKEND == 'pynetsnmp':
    DEFAULT_ADDRESSES += (('::', DEFAULT_PORT),)
    ADDRESS_PATTERNS += (
        re.compile(r"(?P<addr>[0-9a-fA-F:]+)$"),
        re.compile(r"\[(?P<addr>[^\]]+)\] (:(?P<port>[0-9]+))?$", re.VERBOSE),
    )


def main():
    bootstrap_django('snmptrapd')

    # Verify that subsystem exists, if not insert it into database
    verify_subsystem()

    # Initialize and read startupconfig
    global config
    config = SnmptrapdConfig()

    # Create parser and define options
    opts = parse_args()

    # When binding to a port < 1024 we need to be root
    minport = min(port for addr, port in opts.address)
    if minport < 1024:
        if os.geteuid() != 0:
            sys.exit("Must be root to bind to ports < 1024, exiting")

    # Check if already running
    try:
        daemon.justme(pidfile)
    except daemon.DaemonError as why:
        sys.exit(why)

    # Create SNMP agent object
    server = agent.TrapListener(*opts.address)
    server.open()

    # We have bound to a port and can safely drop privileges
    runninguser = NAV_CONFIG['NAV_USER']
    try:
        if os.geteuid() == 0:
            daemon.switchuser(runninguser)
    except daemon.DaemonError as why:
        server.close()
        sys.exit(why)

    global handlermodules

    nav.logs.init_stderr_logging()

    _logger.debug("using %r as SNMP backend", agent.BACKEND)

    # Load handlermodules
    try:
        _logger.debug('Trying to load handlermodules')
        handlermodules = load_handler_modules(
            config.get('snmptrapd', 'handlermodules').split(',')
        )
    except ModuleLoadError as why:
        _logger.error("Could not load handlermodules %s" % why)
        sys.exit(1)

    addresses_text = ", ".join(address_to_string(*addr) for addr in opts.address)
    if not opts.foreground:
        # Daemonize and listen for traps
        try:
            _logger.debug("Going into daemon mode...")
            logfile = open(logfile_path, 'a')
            daemon.daemonize(pidfile, stderr=logfile, stdout=logfile)
        except daemon.DaemonError as why:
            _logger.error("Could not daemonize: %s", why)
            server.close()
            sys.exit(1)

        # Daemonized
        _logger.info('snmptrapd is now running in daemon mode')

        # Reopen lost db connection
        # This is a workaround for a double free bug in psycopg 2.0.7
        # which is why we don't need to keep the return value
        getConnection('default')

        # Reopen log files on SIGHUP
        _logger.debug('Adding signal handler for reopening log files on SIGHUP.')
        signal.signal(signal.SIGHUP, signal_handler)
        # Exit on SIGTERM
        signal.signal(signal.SIGTERM, signal_handler)

        _logger.info("Snmptrapd started, listening on %s", addresses_text)
        try:
            server.listen(opts.community, trap_handler)
        except SystemExit:
            raise
        except Exception:  # noqa: BLE001
            _logger.critical("Fatal exception ocurred", exc_info=True)

    else:
        daemon.writepidfile(pidfile)
        # Start listening and exit cleanly if interrupted.
        try:
            _logger.info("Listening on %s", addresses_text)
            server.listen(opts.community, trap_handler)
        except KeyboardInterrupt:
            _logger.error("Received keyboard interrupt, exiting.")
            server.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="NAV SNMP Trap daemon",
        epilog="One or more address specifications can be given to tell the "
        "trap daemon which interface/port combinations it should "
        "listen to. The default is 0.0.0.0:162, and, if the system "
        "appears to support IPv6, also [::]:162, which means the daemon "
        "will accept traps on any IPv4/IPv6 interface, UDP port 162.",
    )
    parser.add_argument(
        "-f", "--foreground", action="store_true", help="Run in foreground"
    )
    parser.add_argument(
        "-c",
        "--community",
        default="public",
        help="Which SNMP community incoming traps must use. The default is 'public'",
    )
    parser.add_argument("address", nargs="*", type=Address, default=DEFAULT_ADDRESSES)

    return parser.parse_args()


def Address(address):
    address = address.strip()
    match = (pattern.match(address) for pattern in ADDRESS_PATTERNS)
    match = reduce(lambda x, y: x or y, match)
    if match:
        match = match.groupdict()
        addr = match['addr']
        port = int(match.get('port', None) or DEFAULT_PORT)
        if is_valid_ip(addr):
            return addr, port

    raise ValueError("%s is not a valid address" % address)


def trap_handler(trap):
    """Handles a trap.

    :type trap: SNMPTrap

    """
    _traplogger.debug("%s", trap)
    connection = getConnection('default')
    handled_by = []

    for mod in handlermodules:
        _logger.debug("Offering trap (%s) to %s", id(trap), mod)
        try:
            accepted = mod.handleTrap(trap, config=config)
            if accepted:
                handled_by.append(mod.__name__)
            _logger.debug(
                "Module %s %s trap (%s)",
                mod.__name__,
                'accepted' if accepted else 'ignored',
                id(trap),
            )
        except Exception as why:  # noqa: BLE001
            _logger.exception(
                "Unhandled exception when handling trap (%s) with %s: %s",
                id(trap),
                mod.__name__,
                why,
            )
        # Assuming that the handler used the same connection as this
        # function, we rollback any uncommitted changes.  This is to
        # avoid idling in transactions.
        connection.rollback()

    _log_trap_handle_result(handled_by, trap)


def _log_trap_handle_result(handled_by, trap):
    agent_string = (
        trap.netbox.sysname + ' ({})'.format(trap.agent) if trap.netbox else trap.agent
    )
    if handled_by:
        _logger.info(
            "v%s trap received from %s, handled by %s",
            trap.version,
            agent_string,
            handled_by,
        )
    else:
        _logger.info(
            "v%s trap received from %s, no handlers wanted it: %s",
            trap.version,
            agent_string,
            trap.snmpTrapOID,
        )


def verify_subsystem():
    """Verify that subsystem exists, if not insert it into database"""
    db = getConnection('default')
    c = db.cursor()

    sql = """INSERT INTO subsystem (SELECT 'snmptrapd', '' WHERE
    NOT EXISTS (SELECT * FROM subsystem WHERE name = 'snmptrapd'))"""
    c.execute(sql)
    db.commit()


def signal_handler(signum, _):
    """Signal handler to close and reopen log file(s) on HUP and exit on TERM"""
    if signum == signal.SIGHUP:
        _logger.info("SIGHUP received; reopening log files.")
        nav.logs.reopen_log_files()
        logfile = open(logfile_path, 'a')
        daemon.redirect_std_fds(stdout=logfile, stderr=logfile)
        nav.logs.reset_log_levels()
        nav.logs.set_log_config()
        _logger.info('Log files reopened.')
    elif signum == signal.SIGTERM:
        _logger.warning('SIGTERM received: Shutting down.')
        sys.exit(0)


class SnmptrapdConfig(NAVConfigParser):
    """Configparser for snmptrapd"""

    DEFAULT_CONFIG_FILES = ['snmptrapd.conf']


if __name__ == '__main__':
    main()
