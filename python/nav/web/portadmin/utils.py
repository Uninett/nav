#
# Copyright 2010 (C) Norwegian University of Science and Technology
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
"""Util functions for the PortAdmin"""
import re
import ConfigParser
import django.template

from django.template.loaders.filesystem import Loader
from nav.models.profiles import AccountGroup
from nav.path import sysconfdir
from nav.portadmin.snmputils import SNMPFactory, FantasyVlan
from nav.models.arnold import Identity
from operator import attrgetter
from os.path import join

CONFIGFILE = join(sysconfdir, "portadmin", "portadmin.conf")

import logging
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
        if ifalias.has_key(interface.ifindex):
            interface.ifalias = ifalias[interface.ifindex]
        if vlans.has_key(interface.ifindex):
            interface.vlan = vlans[interface.ifindex]
        if operstatus.has_key(interface.ifindex):
            interface.ifoperstatus = operstatus[interface.ifindex]
        if adminstatus.has_key(interface.ifindex):
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
        if is_administrator(account):
            allowed_vlans = netbox_vlans
        else:
            all_allowed_vlans = find_allowed_vlans_for_user(account)
            allowed_vlans = intersect(all_allowed_vlans, netbox_vlans)
    else:
        allowed_vlans = netbox_vlans

    defaultvlan = find_default_vlan()
    if defaultvlan and defaultvlan not in allowed_vlans:
        allowed_vlans.append(defaultvlan)

    return sorted(allowed_vlans, key=attrgetter('vlan'))


def is_vlan_authorization_enabled():
    """Check config to see if authorization is to be done"""
    config = read_config()
    if config.has_option("authorization", "vlan_auth"):
        return config.getboolean("authorization", "vlan_auth")

    return False


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
    return allowed_vlans


def find_default_vlan(include_netident=False):
    """Check config to see if a default vlan is set

    :rtype: FantasyVlan
    """
    defaultvlan = ""
    netident = ""

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


def fetch_voice_vlans():
    """Fetch the voice vlans (if any) from the config file"""
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
    config = ConfigParser.ConfigParser()
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


def is_administrator(account):
    """Check if this account is an administrator account"""
    groups = account.get_groups()
    if AccountGroup.ADMIN_GROUP in groups:
        return True
    return False


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


def get_ifaliasformat():
    """Get format for ifalias defined in config file"""
    section = "ifaliasformat"
    option = "format"
    config = read_config()
    if config.has_section(section) and config.has_option(section, option):
        return config.get(section, option)


def get_aliastemplate():
    """Fetch template for displaying ifalias format as help to user"""
    templatepath = join(sysconfdir, "portadmin")
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

    - the vlans was on the trunk before
    - or is set by user and in allowed_vlans

    """
    return (list((set(target_vlans) | set(old_vlans)) &
                 (set(old_vlans) | set(allowed_vlans))))


def should_check_access_rights(account):
    """Return boolean indicating that this user is restricted"""
    return (is_vlan_authorization_enabled() and
            not is_administrator(account))


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
