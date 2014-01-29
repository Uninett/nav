#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2003-2005 Norwegian University of Science and Technology
# Copyright 2006, 2008, 2011 UNINETT AS
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
This program dispatches maintenance events according to the maintenance
schedule in NAVdb.
"""


import os.path
import time
import nav.path
from nav.maintengine import init_logging
from nav.maintengine import check_devices_on_maintenance


def main():
    """Good old main..."""
    before = time.clock()
    log_file = os.path.join(nav.path.localstatedir, 'log', 'maintengine.log')
    fmt = "[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s"
    logger = init_logging(log_file, fmt)
    logger.debug('------------------------------------------------------------')
    try:
        check_devices_on_maintenance()
    except Exception as error:
        logger.exception("An unhandled exception occurred:")
    logger.debug('Finished in %.3fs' % (time.clock() - before))
    logger.debug('------------------------------------------------------------')


if __name__ == '__main__':
    main()
