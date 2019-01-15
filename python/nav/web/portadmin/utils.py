#
# Copyright (C) 2011-2015 Uninett AS
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
"""Util functions for the PortAdmin"""
import re
import configparser
import logging

import django.template

from django.template.loaders.filesystem import Loader

from nav.config import find_configfile
from nav.django.utils import is_admin
from nav.portadmin.snmputils import SNMPFactory, FantasyVlan
from nav.enterprise.ids import VENDOR_ID_CISCOSYSTEMS
from operator import attrgetter
from os.path import join

CONFIGFILE = find_configfile(join("portadmin", "portadmin.conf")) or ''

_logger = logging.getLogger("nav.web.portadmin")


def get_and_populate_livedata(netbox, interfaces):
    """Fetch live data from netbox"""
    handler = SNMPFactory.get_instance(netbox)
    live_ifaliases = create_dict_from_tuplelist(handler.get_all_if_alias())
    live_vlans = create_dict_from_tuplelist(handler.get_all_vlans())
    live_operstatus = dict(handler.get_netbox_oper_status())
    live_adminstatus = dict(handler.get_netbox_admin_status())
    update_interfaces_with_snmpdata(interfaces, live_ifaliases, live_vlans,
                                    live_operstatus, live_adminstatus)

    return handler


def create_dict_from_tuplelist(tuplelist):
    """
    The input is a list from a snmp bulkwalk or walk.
    Extract ifindex from oid and use that as key in the dict.
    """
    pattern = re.compile(r"(\d+)$")
    result = []
    # Extract ifindex from oid
    for key, value in tuplelist:
        match_object = pattern.search(key)
        if match_object:
            ifindex = int(match_object.groups()[0])
            result.append((ifindex, value))

    # Create dict from modified list
    return dict(result)


def update_interfaces_with_snmpdata(interfaces, ifalias, vlans, operstatus,
                                    adminstatus):
    """
    Update the interfaces with data gathered via snmp.
    """
    for interface in interfaces:
        if interface.ifindex in ifalias:
            interface.ifalias = ifalias[interface.ifindex]
        if interface.ifindex in vlans:
            interface.vlan = vlans[interface.ifindex]
        if interface.ifindex in operstatus:
            interface.ifoperstatus = operstatus[interface.ifindex]
        if interface.ifindex in adminstatus:
            interface.ifadminstatus = adminstatus[interface.ifindex]


def find_and_populate_allowed_vlans(account, netbox, interfaces, factory):
    """Find allowed vlans and indicate which interface can be edited"""
    allowed_vlans = find_allowed_vlans_for_user_on_netbox(account, netbox,
                                                          factory)
    set_editable_on_interfaces(netbox, interfaces, allowed_vlans)
    return allowed_vlans


def find_allowed_vlans_for_user_on_netbox(account, netbox, factory=None):
    """Find allowed vlans for this user on this netbox

    ::returns list of Fantasyvlans

    """
    netbox_vlans = find_vlans_on_netbox(netbox, factory=factory)

    if is_vlan_authorization_enabled():
        if is_admin(account):
            allowed_vlans = netbox_vlans
        else:
            all_allowed_vlans = find_allowed_vlans_for_user(account)
            allowed_vlans = intersect(all_allowed_vlans, netbox_vlans)
    else:
        allowed_vlans = netbox_vlans

    return sorted(allowed_vlans, key=attrgetter('vlan'))


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


def find_vlans_on_netbox(netbox, factory=None):
    """Find all the vlans on this netbox

    fac: already instantiated factory instance. Use this if possible
    to enable use of cached values

    :returns: list of FantasyVlans
    :rtype: list
    """
    if not factory:
        factory = SNMPFactory.get_instance(netbox)
    return factory.get_netbox_vlans()


def find_allowed_vlans_for_user(account):
    """Find the allowed vlans for this user based on organization"""
    allowed_vlans = []
    for org in account.organizations.all():
        allowed_vlans.extend(find_vlans_in_org(org))

    defaultvlan = find_default_vlan()
    if defaultvlan and defaultvlan not in allowed_vlans:
        allowed_vlans.append(defaultvlan)

    return allowed_vlans


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


def set_editable_on_interfaces(netbox, interfaces, vlans):
    """
    Set a flag on the interface to indicate if user is allowed to edit it.
    """
    vlan_numbers = [vlan.vlan for vlan in vlans]

    for interface in interfaces:
        iseditable = (interface.vlan in vlan_numbers and netbox.read_write)
        if iseditable:
            interface.iseditable = True
        else:
            interface.iseditable = False


def intersect(list_a, list_b):
    """Find intersection between two lists"""
    return list(set(list_a) & set(list_b))


def find_vlans_in_org(org):
    """Find all vlans in an organization and child organizations

    :returns: list of FantasyVlans
    :rtype: list
    """
    vlans = list(org.vlan_set.all())
    for child_org in org.organization_set.all():
        vlans.extend(find_vlans_in_org(child_org))
    return [FantasyVlan(x.vlan, x.net_ident) for x in list(set(vlans)) if
            x.vlan]


def check_format_on_ifalias(ifalias):
    """Verify that format on ifalias is correct if it is defined in config"""
    section = "ifaliasformat"
    option = "format"
    config = read_config()
    if not ifalias:
        return True
    elif config.has_section(section) and config.has_option(section, option):
        ifalias_format = re.compile(config.get(section, option))
        if ifalias_format.match(ifalias):
            return True
        else:
            _logger.error('Wrong format on ifalias: %s', ifalias)
            return False
    else:
        return True


def get_ifaliasformat(config=None):
    """Get format for ifalias defined in config file"""
    if config is None:
        config = read_config()
    section = "ifaliasformat"
    option = "format"
    if config.has_section(section) and config.has_option(section, option):
        return config.get(section, option)


def get_aliastemplate():
    """Fetch template for displaying ifalias format as help to user"""
    templatepath = find_configfile("portadmin")
    templatename = "aliasformat.html"
    loader = Loader()
    rawdata, _ = loader.load_template_source(templatename, [templatepath])
    tmpl = django.template.Template(rawdata)
    return tmpl


def save_to_database(interfaces):
    """Save changes for all interfaces to database"""
    for interface in interfaces:
        interface.save()


def filter_vlans(target_vlans, old_vlans, allowed_vlans):
    """Return a list of vlans that matches following criteria

    - All target vlans should be set if the vlan is in allowed_vlans
    - Remove the old_vlans if they are in allowed_vlans
    """
    return list((set(target_vlans) & set(allowed_vlans)) |
                (set(old_vlans) - set(allowed_vlans)))


def should_check_access_rights(account):
    """Return boolean indicating that this user is restricted"""
    return (is_vlan_authorization_enabled() and
            not is_admin(account))


def mark_detained_interfaces(interfaces):
    """Mark interfaces detained in Arnold
    :type interfaces: list[nav.models.manage.Interface]
    """
    for interface in interfaces:
        # If interface is administratively down, check if Arnold is the source
        if interface.ifadminstatus == 2 and interface.identity_set.filter(
                status='disabled').count() > 0:
            interface.detained = True
        if interface.identity_set.filter(status='quarantined').count() > 0:
            interface.detained = True


def add_dot1x_info(interfaces, handler):
    """Add information about dot1x state for interfaces"""

    # Skip if port access control is not enabled (and thus not dot1x)
    if not handler.is_port_access_control_enabled():
        return

    dot1x_states = handler.get_dot1x_enabled_interfaces()
    if not dot1x_states:
        # Empty result
        return

    for interface in interfaces:
        interface.dot1xenabled = dot1x_states.get(interface.ifindex)


def is_cisco(netbox):
    """Returns true if netbox is of vendor cisco
    :type netbox: manage.Netbox
    """
    return netbox.type.get_enterprise_id() == VENDOR_ID_CISCOSYSTEMS


def get_trunk_edit(config):
    """Gets config option for trunk edit

    Default is to allow trunk edit
    """
    section = 'general'
    option = 'trunk_edit'
    if config.has_section(section) and config.has_option(section, option):
        return config.getboolean(section, option)
    return True
