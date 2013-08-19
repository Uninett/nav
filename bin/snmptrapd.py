#!/usr/bin/env python
#
# Copyright 2007 (C) Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV daemon to receive and act upon SNMP traps."""

import os
import re
import socket
import sys
from optparse import OptionParser
import ConfigParser
import logging
import signal

# Import NAV libraries
from nav import daemon
import nav.buildconf
from nav.snmptrapd.plugin import load_handler_modules, ModuleLoadError
from nav.util import is_valid_ip, address_to_string
from nav.db import getConnection
import nav.logs

from nav.snmptrapd import agent

# Paths
configfile = nav.buildconf.sysconfdir + "/snmptrapd.conf"
traplogfile = nav.buildconf.localstatedir + "/log/snmptraps.log"
logfile = nav.buildconf.localstatedir + "/log/snmptrapd.log"


DEFAULT_PORT = 162
DEFAULT_ADDRESSES = (
    ('0.0.0.0', DEFAULT_PORT),
)
ADDRESS_PATTERNS = (
    re.compile(r"(?P<addr>[0-9\.]+) (:(?P<port>[0-9]+))?$", re.VERBOSE),
)
if socket.has_ipv6 and agent.BACKEND == 'pynetsnmp':
    DEFAULT_ADDRESSES += (('::', DEFAULT_PORT),)
    ADDRESS_PATTERNS += (
        re.compile(r"(?P<addr>[0-9a-fA-F:]+)$"),
        re.compile(r"\[(?P<addr>[^\]]+)\] (:(?P<port>[0-9]+))?$", re.VERBOSE),
    )


def main():

    # Verify that subsystem exists, if not insert it into database
    verifySubsystem()

    # Initialize and read startupconfig
    global config
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    # Create parser and define options
    global opts
    opts, addresses = parse_args()

    # When binding to a port < 1024 we need to be root
    minport = min(port for addr, port in addresses)
    if minport < 1024:
        if os.geteuid() != 0:
            print("Must be root to bind to ports < 1024, exiting")
            sys.exit(-1)

    # Check if already running
    pidfile = nav.buildconf.localstatedir + "/run/snmptrapd.pid"
    try:
        daemon.justme(pidfile)
    except daemon.DaemonError, why:
        print why
        sys.exit(-1)

    # Create SNMP agent object
    server = agent.TrapListener(*addresses)
    server.open()

    # We have bound to a port and can safely drop privileges
    runninguser = config.get('snmptrapd','user')
    try:
        if os.geteuid() == 0:
            daemon.switchuser(runninguser)
    except daemon.DaemonError, why:
        print why
        server.close()
        sys.exit(-1)


    # logger and traplogger logs to two different files. We want a
    # complete log of received traps in one place, and an activity log
    # somewhere else.  Note: When not running in daemonmode the
    # loggers both log to stdout.
    global logger, traplogger, handlermodules

    # Create logger based on if we are to daemonize or just run in
    # shell
    if opts.daemon:

        # Fetch loglevel from snmptrapd.conf
        loglevel = config.get('snmptrapd', 'loglevel')
        if not loglevel.isdigit():
            loglevel = logging.getLevelName(loglevel)

        try:
            loglevel = int(loglevel)
        except ValueError:
            #default to loglevel INFO
            loglevel = 20

        # Initialize deamonlogger
        if not loginitfile(logfile, traplogfile, loglevel):
            sys.exit(1)

        traplogger = logging.getLogger('nav.snmptrapd.traplog')
        logger = logging.getLogger('nav.snmptrapd')

    else:

        # Log to console
        handler = logging.StreamHandler()

        logger = logging.getLogger('')
        logger.setLevel(logging.DEBUG)
        traplogger = logging.getLogger('')
        traplogger.setLevel(logging.DEBUG)

        logger.addHandler(handler)
        traplogger.addHandler(handler)

    logger.debug("using %r as SNMP backend", agent.BACKEND)

    # Load handlermodules
    try:
        logger.debug('Trying to load handlermodules')
        handlermodules = load_handler_modules(config.get('snmptrapd','handlermodules').split(','))
    except ModuleLoadError, why:
        logger.error("Could not load handlermodules %s" %why)
        sys.exit(1)

    addresses_text = ", ".join(address_to_string(*addr) for addr in addresses)
    if opts.daemon:
        # Daemonize and listen for traps
        try:
            logger.debug("Going into daemon mode...")
            daemon.daemonize(pidfile,
                             stderr=nav.logs.get_logfile_from_logger())
        except daemon.DaemonError, why:
            logger.error("Could not daemonize: %s", why)
            server.close()
            sys.exit(1)

        # Daemonized; reopen log files
        nav.logs.reopen_log_files()
        logger.debug('Daemonization complete; reopened log files.')

        # Reopen lost db connection
        # This is a workaround for a double free bug in psycopg 2.0.7
        # which is why we don't need to keep the return value
        getConnection('default')

        # Reopen log files on SIGHUP
        logger.debug('Adding signal handler for reopening log files on SIGHUP.')
        signal.signal(signal.SIGHUP, signal_handler)
        # Exit on SIGTERM
        signal.signal(signal.SIGTERM, signal_handler)

        logger.info("Snmptrapd started, listening on %s", addresses_text)
        try:
            server.listen(opts.community, trapHandler)
        except SystemExit:
            raise
        except Exception, why:
            logger.critical("Fatal exception ocurred", exc_info=True)

    else:
        # Start listening and exit cleanly if interrupted.
        try:
            logger.info ("Listening on %s", addresses_text)
            server.listen(opts.community, trapHandler)
        except KeyboardInterrupt, why:
            logger.error("Received keyboardinterrupt, exiting.")
            server.close()


def parse_args():
    usage = "usage: %prog [options] [address1 [address2 ...]]"
    parser = OptionParser(
        usage,
        epilog="One or more address specifications can be given to tell the "
               "trap daemon which interface/port combinations it should "
               "listen to. The default is 0.0.0.0:162, which means the daemon "
               "will accept traps on any IPv4 interface, UDP port 162."
    )
    parser.add_option("-d", "--daemon", action="store_true", dest="daemon",
                      help="Run as daemon")
    parser.add_option("-c", "--community", dest="community", default="public",
                      help="Which SNMP community incoming traps must use. "
                           "The default is 'public'")

    (opts, args) = parser.parse_args()
    try:
        addresses = parse_address_list(args) or DEFAULT_ADDRESSES
    except ValueError as error:
        parser.error(error)
    return opts, addresses


def parse_address_list(args):
    return [parse_address(arg.strip()) for arg in args]


def parse_address(address):
    match = (pattern.match(address) for pattern in ADDRESS_PATTERNS)
    match = reduce(lambda x, y: x or y, match)
    if match:
        match = match.groupdict()
        addr = match['addr']
        port = int(match.get('port', None) or DEFAULT_PORT)
        if is_valid_ip(addr):
            return addr, port

    raise ValueError("%s is not a valid address" % address)


def loginitfile(logfile, traplogfile, loglevel):
    """Initalize the logging handler for logfile."""

    try:
        filehandler = logging.FileHandler(logfile, 'a')
        fileformat = '[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s'
        fileformatter = logging.Formatter(fileformat)
        filehandler.setFormatter(fileformatter)
        logger = logging.getLogger()
        logger.addHandler(filehandler)
        logger.setLevel(loglevel)
        #logger.setLevel(loglevel)

        filehandler = logging.FileHandler(traplogfile, 'a')
        filehandler.setFormatter(fileformatter)
        traplogger = logging.getLogger("nav.snmptrapd.traplog")
        traplogger.propagate = 0
        traplogger.addHandler(filehandler)

        return True
    except IOError, error:
        print >> sys.stderr, \
         "Failed creating file loghandler. Daemon mode disabled. (%s)" \
         % error
        return False





def trapHandler(trap):
    """Handle a trap"""

    traplogger.info(trap.trapText())
    connection = getConnection('default')

    for mod in handlermodules:
        logger.debug("Giving trap to %s" %str(mod))
        try:
            accepted = mod.handleTrap(trap, config=config)
            logger.debug ("Module %s %s trap", mod.__name__,
                          accepted and 'accepted' or 'ignored',)
        except Exception, why:
            logger.exception("Error when handling trap with %s: %s"
                             %(mod.__name__, why))
        # Assuming that the handler used the same connection as this
        # function, we rollback any uncommitted changes.  This is to
        # avoid idling in transactions.
        connection.rollback()


def verifySubsystem ():
    """Verify that subsystem exists, if not insert it into database"""
    db = getConnection('default')
    c = db.cursor()

    sql = """INSERT INTO subsystem (SELECT 'snmptrapd', '' WHERE
    NOT EXISTS (SELECT * FROM subsystem WHERE name = 'snmptrapd'))"""
    c.execute(sql)
    db.commit()


def signal_handler(signum, _):
    """Signal handler to close and reopen log file(s) on HUP and exit on TERM."""
    if signum == signal.SIGHUP:
        logger.info("SIGHUP received; reopening log files.")
        nav.logs.reopen_log_files()
        daemon.redirect_std_fds(stderr=nav.logs.get_logfile_from_logger())
        logger.info("Log files reopened.")
    elif signum == signal.SIGTERM:
        logger.warn('SIGTERM received: Shutting down.')
        sys.exit(0)

if __name__ == '__main__':
    main()

