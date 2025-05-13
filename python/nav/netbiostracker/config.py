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
"""Configparser for Netbiostracker"""

import logging
from configparser import NoSectionError, NoOptionError
from IPy import IP
from nav.config import NAVConfigParser

_logger = logging.getLogger('netbiostrackerconfig')


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
            return create_list(exception_list)

    def get_encoding(self):
        """Get the encoding option"""
        return self.get('main', 'encoding')


def create_list(exceptions):
    """Create a list of single ip-adresses from a list of IP instances"""
    addresses = []
    for element in [x.strip() for x in exceptions.splitlines() if x]:
        try:
            address = IP(element)
        except ValueError as error:
            _logger.error('Skipping exception %s: %s', element, error)
            continue
        else:
            addresses.append(address)

    return list(set(addresses))
