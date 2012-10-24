#!/usr/bin/env python
#
# Copyright 2008 (C) Norwegian University of Science and Technology
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
# import regular libraries
"""
autoenable is meant to be run as a cronjob. It checks the configured
arnold-database for any detained ports and opens them if they have a
autoenable-time set and that time has passed.
"""

import sys
import logging
import ConfigParser
import getpass
from datetime import datetime

import nav.arnold
import nav.db
import nav.buildconf
from nav.models.arnold import Identity


def main():
    """Main controller"""
    logger = get_logger(read_config())
    logger.info("Starting autoenable")

    candidates = Identity.objects.filter(autoenable__lte=datetime.now())

    if len(candidates) <= 0:
        logger.info("No ports ready for opening.")
        sys.exit(0)

    # For each port that is blocked, try to enable the port.
    for candidate in candidates:
        try:
            nav.arnold.open_port(candidate, getpass.getuser(),
                                 eventcomment="Opened automatically by "
                                              "autoenable")
            interface = candidate.interface
            netbox = interface.netbox
            logger.info("Opening %s %s:%s for %s" % (
                netbox.sysname, interface.module,
                interface.baseport, candidate.mac))
        except (nav.arnold.NoDatabaseInformationError,
                nav.arnold.ChangePortStatusError,
                nav.arnold.DbError), why:
            logger.error(why)
            continue


def read_config():
    """Read and return config"""
    configfile = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
    config = ConfigParser.ConfigParser()
    config.read(configfile)


def get_logger(config):
    """Set logger attributes, return logger"""
    loglevel = config.get('loglevel','autoenable')
    if not loglevel.isdigit():
        loglevel = logging.getLevelName(loglevel)

    try:
        loglevel = int(loglevel)
    except ValueError:
        loglevel = 20 # default to INFO

        # Create logger, start logging
    logfile = nav.buildconf.localstatedir + "/log/arnold/autoenable.log"
    filehandler = logging.FileHandler(logfile)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] '\
                                  '[%(name)s] L%(lineno)d %(message)s')
    filehandler.setFormatter(formatter)
    logger = logging.getLogger('autoenable')
    logger.addHandler(filehandler)
    logger.setLevel(loglevel)

    return logger


if __name__ == '__main__':
    main()
