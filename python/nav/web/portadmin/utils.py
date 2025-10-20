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

from typing import Any, Optional, Sequence
import re
import logging
from operator import attrgetter

from django.template import loader

from nav.models import manage, profiles
from nav.models.profiles import Account
from nav.portadmin.config import CONFIG
from nav.portadmin.management import ManagementFactory
from nav.portadmin.handlers import ManagementHandler
from nav.portadmin.vlan import FantasyVlan
from nav.enterprise.ids import VENDOR_ID_CISCOSYSTEMS


_logger = logging.getLogger("nav.web.portadmin")


def get_and_populate_livedata(netbox, interfaces):
    """Fetch live data from netbox"""
    handler = ManagementFactory.get_instance(netbox)
    livedata = handler.get_interfaces(interfaces)
    update_interfaces_with_collected_data(interfaces, livedata)

    return handler


def update_interfaces_with_collected_data(
    interfaces: Sequence[manage.Interface], livedata: Sequence[dict[str, Any]]
):
    """Updates the list of Interface objects with data gathered via
    ManagementHandler.get_interfaces().
    """
    interfaces_by_name = {ifc.ifdescr: ifc for ifc in interfaces}
    interfaces_by_name.update({ifc.ifname: ifc for ifc in interfaces})

    matches = (
        (interfaces_by_name[data["name"]], data)
        for data in livedata
        if data.get("name") in interfaces_by_name
    )
    for interface, data in matches:
        if data.get("description") is not None:
            interface.ifalias = data["description"]
        if data.get("vlan"):
            interface.vlan = data["vlan"]
        if data.get("oper"):
            interface.ifoperstatus = data["oper"]
        if data.get("admin"):
            interface.ifadminstatus = data["admin"]


def find_and_populate_allowed_vlans(
    account: profiles.Account,
    netbox: manage.Netbox,
    interfaces: Sequence[manage.Interface],
    handler: ManagementHandler,
):
    """Finds allowed vlans and indicate which interfaces can be edited"""
    allowed_vlans = find_allowed_vlans_for_user_on_netbox(account, netbox, handler)
    set_editable_flag_on_interfaces(interfaces, allowed_vlans, account)
    return allowed_vlans


def find_allowed_vlans_for_user_on_netbox(
    account: profiles.Account, netbox: manage.Netbox, handler: ManagementHandler = None
) -> list[FantasyVlan]:
    """Finds allowed vlans for this user on this netbox"""
    netbox_vlans = find_vlans_on_netbox(netbox, handler=handler)

    if CONFIG.is_vlan_authorization_enabled():
        if account.is_admin():
            allowed_vlans = netbox_vlans
        else:
            all_allowed_vlans = find_allowed_vlans_for_user(account)
            allowed_vlans = intersect(all_allowed_vlans, netbox_vlans)
    else:
        allowed_vlans = netbox_vlans

    return sorted(allowed_vlans, key=attrgetter('vlan'))


def find_vlans_on_netbox(
    netbox: manage.Netbox, handler: ManagementHandler = None
) -> list[FantasyVlan]:
    """Find all the available vlans on this netbox

    :param netbox: The Netbox whose available VLANs you want to find.
    :param handler: Already instantiated ManagementHandler instance. Use this if
                    possible to enable use of cached values.
    """
    if not handler:
        handler = ManagementFactory.get_instance(netbox)
    return handler.get_netbox_vlans()


def find_allowed_vlans_for_user(account):
    """Find the allowed vlans for this user based on organization"""
    allowed_vlans = []
    for org in account.organizations.all():
        allowed_vlans.extend(find_vlans_in_org(org))

    defaultvlan = CONFIG.find_default_vlan()
    if defaultvlan and defaultvlan not in allowed_vlans:
        allowed_vlans.append(defaultvlan)

    return allowed_vlans


def set_editable_flag_on_interfaces(
    interfaces: Sequence[manage.Interface],
    vlans: Sequence[FantasyVlan],
    user: Optional[Account] = None,
):
    """Sets the pseudo-attribute `iseditable` on each interface in the interfaces
    list, indicating whether the PortAdmin UI should allow edits to it or not.

    An interface will be considered "editable" only if its native vlan matches one of
    the vlan tags from `vlans`. An interface may be considered non-editable if it is
    an uplink, depending on how portadmin is configured.
    """
    vlan_tags = {vlan.vlan for vlan in vlans}
    allow_everything = not should_check_access_rights(account=user) if user else False

    for interface in interfaces:
        if allow_everything:
            interface.iseditable = True
            continue

        vlan_is_acceptable = interface.vlan in vlan_tags
        is_link = bool(interface.to_netbox)
        refuse_link_edit = not CONFIG.get_link_edit() and is_link

        interface.iseditable = vlan_is_acceptable and not refuse_link_edit


def intersect(list_a, list_b):
    """Find intersection between two lists"""
    return list(set(list_a) & set(list_b))


def find_vlans_in_org(org):
    """Find all vlans in an organization and child organizations

    :returns: list of FantasyVlans
    :rtype: list
    """
    vlans = list(org.vlans.all())
    for child_org in org.child_organizations.all():
        vlans.extend(find_vlans_in_org(child_org))
    return [FantasyVlan(x.vlan, x.net_ident) for x in list(set(vlans)) if x.vlan]


def check_format_on_ifalias(ifalias):
    """Verify that format on ifalias is correct if it is defined in config"""
    if not ifalias:
        return True
    ifalias_format = CONFIG.get_ifaliasformat()
    if ifalias_format:
        ifalias_format = re.compile(ifalias_format)
        if ifalias_format.match(ifalias):
            return True
        else:
            _logger.error('Wrong format on ifalias: %s', ifalias)
            return False
    else:
        return True


def get_aliastemplate():
    """Fetch template for displaying ifalias format as help to user"""
    return loader.get_template("portadmin/aliasformat.html")


def save_to_database(interfaces):
    """Save changes for all interfaces to database"""
    for interface in interfaces:
        interface.save()


def filter_vlans(target_vlans, old_vlans, allowed_vlans):
    """Return a list of vlans that matches following criteria

    - All target vlans should be set if the vlan is in allowed_vlans
    - Remove the old_vlans if they are in allowed_vlans
    """
    return list(
        (set(target_vlans) & set(allowed_vlans)) | (set(old_vlans) - set(allowed_vlans))
    )


def should_check_access_rights(account):
    """Return boolean indicating that this user is restricted"""
    return CONFIG.is_vlan_authorization_enabled() and not account.is_admin()


def mark_detained_interfaces(interfaces):
    """Mark interfaces detained in Arnold
    :type interfaces: list[nav.models.manage.Interface]
    """
    for interface in interfaces:
        # If interface is administratively down, check if Arnold is the source
        if (
            interface.ifadminstatus == 2
            and interface.arnold_identities.filter(status='disabled').count() > 0
        ):
            interface.detained = True
        if interface.arnold_identities.filter(status='quarantined').count() > 0:
            interface.detained = True


def add_dot1x_info(interfaces, handler):
    """Add information about dot1x state for interfaces"""

    # Skip if port access control is not enabled (and thus not dot1x)
    if not handler.is_port_access_control_enabled():
        return

    dot1x_states = handler.get_dot1x_enabled_interfaces()

    url_template = CONFIG.get_dot1x_external_url()
    for interface in interfaces:
        interface.dot1xenabled = dot1x_states.get(interface.ifname)
        if url_template:
            interface.dot1x_external_url = url_template.format(
                netbox=interface.netbox, interface=interface
            )


def is_cisco(netbox):
    """Returns true if netbox is of vendor cisco
    :type netbox: manage.Netbox
    """
    return netbox.type.get_enterprise_id() == VENDOR_ID_CISCOSYSTEMS


def add_poe_info(interfaces, handler):
    """Add information about PoE state for interfaces"""
    states = handler.get_poe_states(interfaces)
    for interface in interfaces:
        interface.poe_state = states.get(interface.ifname)
        interface.supports_poe = True if interface.poe_state else False
