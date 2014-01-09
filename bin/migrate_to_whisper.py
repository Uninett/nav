#!/usr/bin/env python
#
# Copyright (C) 2014 UNINETT AS
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
"""Migrate all rrd-files to whisper files

Use schemas deducted from the rrd-files

"""
from optparse import OptionParser
from os.path import join
from datetime import datetime
import logging
import sys

from nav.graphite_migrate import (InterfaceMigrator, SystemMigrator,
                                  PpingMigrator, SensorMigrator,
                                  ActiveIpMigrator, ServicePingMigrator)
from nav.logs import init_stderr_logging
from nav.path import localstatedir

_logger = logging.getLogger('nav.graphite.migrate')


def main():
    """Controller"""

    options, args = parse_options()
    init_stderr_logging()

    start_time = datetime.now()
    _logger.info('Starting migrate at %s', start_time)

    InterfaceMigrator(args[0]).migrate()
    SystemMigrator(args[0]).migrate()
    PpingMigrator(args[0]).migrate()
    ServicePingMigrator(args[0]).migrate()
    SensorMigrator(args[0]).migrate()
    ActiveIpMigrator(args[0]).migrate()

    _logger.info('Migration done in %s', datetime.now() - start_time)


def parse_options():
    """Parse command line arguments and options"""
    usage = "usage: %prog path_to_whisper_storage"
    parser = OptionParser(usage=usage)
    options, args = parser.parse_args()
    if not args:
        print parser.get_usage()
        sys.exit()
    return options, args


if __name__ == '__main__':
    main()
