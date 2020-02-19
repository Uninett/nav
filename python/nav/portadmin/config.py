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
import configparser
from os.path import join

from nav.config import find_configfile
from nav.portadmin.vlan import FantasyVlan

CONFIGFILE = find_configfile(join("portadmin", "portadmin.conf")) or ''


def is_vlan_authorization_enabled():
    """Check config to see if authorization is to be done"""
    # TODO: It is very inefficient to reread config for every option
    config = read_config()
    if config.has_option("authorization", "vlan_auth"):
        return config.getboolean("authorization", "vlan_auth")

    return False


def is_write_mem_enabled():
    """Checks if write mem is turned on or off. Default is on"""
    # TODO: It is very inefficient to reread config for every option
    config = read_config()
    if config.has_option("general", "write_mem"):
        return config.getboolean("general", "write_mem")

    return True


def is_restart_interface_enabled():
    """Checks if restart interface is turned on or off. Default is on"""
    # TODO: It is very inefficient to reread config for every option
    config = read_config()
    if config.has_option("general", "restart_interface"):
        return config.getboolean("general", "restart_interface")

    return True


def dot1x_external_url():
    """Returns url for external config of dot1x for a interface"""
    config = read_config()
    section = 'dot1x'
    option = 'port_url_template'
    return config[section].get(option, None)


def get_ifaliasformat(config=None):
    """Get format for ifalias defined in config file"""
    if config is None:
        config = read_config()
    section = "ifaliasformat"
    option = "format"
    if config.has_section(section) and config.has_option(section, option):
        return config.get(section, option)


def find_default_vlan(include_netident=False):
    """Check config to see if a default vlan is set

    :rtype: FantasyVlan
    """
    defaultvlan = ""
    netident = ""

    # TODO: It is very inefficient to reread config for every option
    config = read_config()
    if config.has_section("defaultvlan"):
        if config.has_option("defaultvlan", "vlan"):
            defaultvlan = config.getint("defaultvlan", "vlan")
        if config.has_option("defaultvlan", "netident"):
            netident = config.get("defaultvlan", "netident")

    if defaultvlan:
        if include_netident:
            return FantasyVlan(defaultvlan, netident)
        else:
            return FantasyVlan(defaultvlan)


def fetch_voice_vlans(config=None):
    """Fetch the voice vlans (if any) from the config file"""
    if config is None:
        config = read_config()
    if config.has_section("general"):
        if config.has_option("general", "voice_vlans"):
            try:
                return [int(v) for v in
                        config.get("general", "voice_vlans").split(',')]
            except ValueError:
                pass
    return []


def read_config():
    """Read the config"""
    config = configparser.ConfigParser()
    config.read(CONFIGFILE)

    return config
