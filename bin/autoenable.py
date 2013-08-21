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

"""
Autoenable removes detention for computers that are done with detention.

Usage:
sudo -u $NAV_USER ./autoenable.py

autoenable is meant to be run as a cronjob. It checks the configured
arnold-database for any detained ports and opens them if they have a
autoenable-time set and that time has passed.

"""

import getpass
import logging
import sys
from datetime import datetime

import nav.buildconf
from nav.arnold import (open_port, init_logging, GeneralException)
from nav.models.arnold import Identity

LOGGER = logging.getLogger('autoenable')


def main():
    """Main controller"""
    init_logging(nav.buildconf.localstatedir + "/log/arnold/autoenable.log")
    LOGGER.info("Starting autoenable")

    candidates = Identity.objects.filter(
        autoenable__lte=datetime.now(), status__in=['disabled', 'quarantined'])

    if len(candidates) <= 0:
        LOGGER.info("No ports ready for opening.")
        sys.exit(0)

    # For each port that is blocked, try to enable the port.
    for candidate in candidates:
        try:
            open_port(candidate, getpass.getuser(),
                      eventcomment="Opened automatically by autoenable")
            interface = candidate.interface
            netbox = interface.netbox
            LOGGER.info("Opening %s %s:%s for %s" % (
                netbox.sysname, interface.module,
                interface.baseport, candidate.mac))
        except GeneralException, why:
            LOGGER.error(why)
            continue


if __name__ == '__main__':
    main()
