#
# Copyright (C) 2012 UNINETT AS
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
"""Configparser for Netbiostracker"""
from ConfigParser import NoSectionError, NoOptionError
from nav.config import NAVConfigParser


class NetbiosTrackerConfig(NAVConfigParser):
    """Configparser for Netbiostracker"""
    DEFAULT_CONFIG_FILES = ('netbiostracker.conf',)
    DEFAULT_CONFIG = """
[main]
encoding = cp850
"""

    def get_exceptions(self):
        """Get list of ip-addresses not to scan"""
        try:
            exception_list = self.get('main', 'exceptions')
        except (NoSectionError, NoOptionError):
            return []
        else:
            return [x.strip() for x in exception_list.splitlines() if x]

    def get_encoding(self):
        """Get the encoding option"""
        return self.get('main', 'encoding')
