#
# Copyright (C) 2011-2015, 2017, 2019 UNINETT
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
"""Tools to handle PortAdmin configuration database/file"""

from os.path import join

from nav.config import NAVConfigParser
from nav.portadmin.vlan import FantasyVlan


class PortAdminConfig(NAVConfigParser):
    """ "PortAdmin config parser"""

    DEFAULT_CONFIG_FILES = (join("portadmin", "portadmin.conf"),)
    DEFAULT_CONFIG = """
[general]
cisco_voice_vlans = false
cisco_voice_cdp = false
restart_interface = on
commit = on
timeout = 3
retries = 3
trunk_edit = true
link_edit = true

[authorization]
vlan_auth = off

[defaultvlan]
[ifaliasformat]

[dot1x]
enabled = false
"""

    def is_vlan_authorization_enabled(self):
        """Check config to see if authorization is to be done"""
        return self.getboolean("authorization", "vlan_auth")

    def is_commit_enabled(self):
        """Checks if configuration commit is turned on or off. Default is on"""
        return self.getboolean("general", "commit")

    def is_restart_interface_enabled(self):
        """Checks if restart interface is turned on or off. Default is on"""
        return self.getboolean("general", "restart_interface")

    def get_dot1x_external_url(self):
        """Returns url for external config of dot1x for a interface"""
        return self.get("dot1x", "port_url_template", fallback=None)

    def get_ifaliasformat(self):
        """Get format for ifalias defined in config file"""
        return self.get("ifaliasformat", "format", fallback=None)

    def find_default_vlan(self, include_netident=False):
        """Check config to see if a default vlan is set

        :rtype: FantasyVlan
        """
        defaultvlan = self.getint("defaultvlan", "vlan", fallback=None)
        netident = self.get("defaultvlan", "netident", fallback="")

        if defaultvlan:
            if include_netident:
                return FantasyVlan(defaultvlan, netident)
            else:
                return FantasyVlan(defaultvlan)

    def fetch_voice_vlans(self):
        """Fetch the voice vlans (if any) from the config file"""
        voice_vlans = self.get("general", "voice_vlans", fallback="")
        try:
            return [int(v) for v in voice_vlans.split(",")]
        except ValueError:
            return []

    def get_trunk_edit(self):
        """Gets config option for trunk edit

        Default is to allow trunk edit
        """
        return self.getboolean("general", "trunk_edit", fallback=True)

    def get_link_edit(self):
        """Gets config option for link edit"""
        return self.getboolean("general", "link_edit", fallback=True)

    def is_dot1x_enabled(self):
        """Checks if dot1x config option is true"""
        return self.getboolean("dot1x", "enabled", fallback=False)

    def is_cisco_voice_enabled(self):
        """Checks if the Cisco config option is enabled"""
        return self.getboolean("general", "cisco_voice_vlan", fallback=False)

    def is_cisco_voice_cdp_enabled(self):
        """Checks if the CDP config option is enabled"""
        return self.getboolean("general", "cisco_voice_cdp", fallback=False)


CONFIG = PortAdminConfig()
