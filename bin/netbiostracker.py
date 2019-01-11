#!/usr/bin/env python
#
# Copyright (C) 2012 Uninett AS
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
"""Starter script for the netbios tracker"""

import logging
import time
from os.path import join

from nav.bootstrap import bootstrap_django
bootstrap_django(__file__)

from nav.netbiostracker import tracker
from nav.netbiostracker.config import NetbiosTrackerConfig
from nav.buildconf import localstatedir
from nav.logs import init_generic_logging


_logger = logging.getLogger('nav.netbiostracker')
LOGFILE = 'netbiostracker.log'


def main():
    """Main controller"""
    init_generic_logging(logfile=LOGFILE, stderr=False)
    config = NetbiosTrackerConfig()

    start = time.time()
    _logger.info('=== Starting netbiostracker ===')

    addresses = tracker.get_addresses_to_scan(config.get_exceptions())
    scanresult = tracker.scan(addresses)
    parsed_results = tracker.parse(scanresult, config.get_encoding())
    tracker.update_database(parsed_results)

    _logger.info('Scanned %d addresses, got %d results in %.2f seconds',
                 len(addresses), len(parsed_results), time.time() - start)
    _logger.info('Netbiostracker done')


if __name__ == '__main__':
    main()
