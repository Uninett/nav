#!/usr/bin/env python
#
# Copyright (C) 2006, 2008, 2011 Uninett AS
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

"""
This program dispatches maintenance events according to the maintenance
schedule in NAVdb.
"""

import time
import logging

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.logs import init_generic_logging
from nav.maintengine import check_devices_on_maintenance

LOG_FILE = 'maintengine.log'
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s"


def main():
    """Good old main..."""
    before = time.time()
    fmt = logging.Formatter(LOG_FORMAT)
    init_generic_logging(
        logfile=LOG_FILE, stderr=False, formatter=fmt, read_config=True
    )
    _logger = logging.getLogger('')

    _logger.debug('-' * 60)  # Visual separation line
    try:
        check_devices_on_maintenance()
    except Exception:  # noqa: BLE001
        _logger.exception("An unhandled exception occurred:")
    _logger.debug('Finished in %.3fs' % (time.time() - before))
    _logger.debug('-' * 60)  # Visual separation line


if __name__ == '__main__':
    main()
