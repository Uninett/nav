# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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
"""ipdevpoll configuration management"""

import os
import logging
import ConfigParser

import nav.buildconf

logger = logging.getLogger(__name__)

class IpdevpollConfig(ConfigParser.ConfigParser):
    def __init__(self):
        ConfigParser.ConfigParser.__init__(self)
        # TODO: initialize with default settings
        # TODO: perform sanity check on config settings
        self.read_all()

    def read_all(self):
        """Read all known ipdevpoll.conf instances."""
        configfile = 'ipdevpoll.conf'
        filenames = [os.path.join(nav.buildconf.sysconfdir, configfile),
                     os.path.join('.', configfile)]
        files_read = self.read(filenames)

        if files_read:
            logger.debug("Read config files %r", files_read)
        else:
            logger.warning("Found no config files")
        return files_read


ipdevpoll_conf = IpdevpollConfig()
