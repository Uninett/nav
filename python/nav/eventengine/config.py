#
# Copyright (C) 2012 Uninett AS
# Copyright (C) 2022 Sikt
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
"""eventengine config"""

from configparser import NoSectionError, NoOptionError

from nav.config import NAVConfigParser
from nav.util import parse_interval


class EventEngineConfig(NAVConfigParser):
    DEFAULT_CONFIG_FILES = ('eventengine.conf',)
    DEFAULT_CONFIG = """
[timeouts]
boxDown.warning = 1m
boxDown.alert = 4m

moduleDown.warning = 1m
moduleDown.alert = 4m

linkDown.alert = 4m

snmpAgentDown.alert = 4m

bgpDown.alert = 1m
"""

    def get_timeout_for(self, option):
        """Gets an integer timeout value from option in the timeouts section.

        :param option: An option name in the timeouts section, or an integer.
        :return: An integer number of seconds parsed from option. If the
                 option is not present, None is returned.  If option itself is
                 an int, option is returned unchanged.

        """
        if isinstance(option, int):
            return option
        try:
            return parse_interval(self.get('timeouts', option))
        except (NoSectionError, NoOptionError):
            pass

    def get_timeouts_for(self, *options):
        """Gets timeouts using get_timeout_for for multiple options"""
        return [self.get_timeout_for(opt) for opt in options]


EVENTENGINE_CONF = EventEngineConfig()
