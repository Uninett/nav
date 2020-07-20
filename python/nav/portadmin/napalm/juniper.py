#
# Copyright (C) 2020 Uninett AS
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
"""Juniper specific PortAdmin functionality.

Some references:
- https://www.juniper.net/documentation/en_US/junos-pyez/information-products/pathway-pages/junos-pyez-developer-guide.html
- https://www.juniper.net/documentation/en_US/junos-pyez/topics/reference/general/junos-pyez-tables-op-predefined.html

NAPALM is used as the base framework for fetching and setting configuration here,
but many of the operations PortAdmin needs are not directly supported by the NAPALM API,
so the underlying Juniper PyEZ library is utilized directly in most cases.

"""
from operator import attrgetter
from typing import List, Any, Dict, Tuple

import napalm
from napalm.base.exceptions import ConnectAuthError, ConnectionException

from nav.enterprise.ids import VENDOR_ID_JUNIPER_NETWORKS_INC
from nav.models import manage
from nav.portadmin.handlers import (
    ManagementHandler,
    DeviceNotConfigurableError,
    AuthenticationError,
    NoResponseError,
    ManagementError,
)
from nav.junos.nav_views import (
    EthPortTable,
    EthernetSwitchingInterfaceTable,
    InterfaceConfigTable,
)
from jnpr.junos.op.vlan import VlanTable

from nav.portadmin.vlan import FantasyVlan
from nav.util import first_true

__all__ = ["Juniper"]

# This maps interface oper/admin status values to SNMP values as used in NAV's data
# model. See IF-MIB::ifOperStatus and IF-MIB::ifAdminStatus from RFC 2863 for details.
SNMP_STATUS_MAP = {"up": 1, "down": 2, True: 1, False: 2}

TEMPLATE_SET_INTERFACE_DESCRIPTION = 'set interfaces {ifname} description "{descr}"'
TEMPLATE_DELETE_INTERFACE_DESCRIPTION = "delete interfaces {ifname} description"
TEMPLATE_RESET_VLAN_MEMBERS = """
delete interfaces {ifname} unit {unit} family ethernet-switching vlan members
set interfaces {ifname} unit {unit} family ethernet-switching vlan members [ {members} ]
"""


class Juniper(ManagementHandler):
    """Juniper specific version of a Napalm PortAdmin handler.

    Juniper switches do things a bit differently from the standard model supported by
    NAV. VLAN config is put on logical sub-units of the physical ports. SNMP-wise,
    these count as separate, but related interfaces.

    NAV's standard interpretation from collection is that the logical sub-units are
    switch ports, since these are the interfaces listed in the BRIDGE-MIB, while the
    parent ports are largely ignored as significant.

    This implementation will therefore focus on the logical units as targets for
    administration, but will infer which configuration properties belong on the
    parent interface and fetch/set those parameters from that interface silently.

    """

    VENDOR = VENDOR_ID_JUNIPER_NETWORKS_INC

    def __init__(self, netbox, **kwargs):
        super().__init__(netbox, **kwargs)
        self.driver = napalm.get_network_driver("JunOS")
        self._device = None
        self._ports = None
        self._interfaces = None
        self._vlans = None

    @property
    def device(self):
        """Opens a device connection or returns an existing one"""
        # FIXME: This is just for prototyping, this config must be retrieved from the DB
        if not self._device:
            self._device = self.driver(
                hostname=self.netbox.sysname,
                username="nav",
                password="",
                optional_args={
                    "key_file": "/source/id_netconf",
                    "config_lock": True,
                    "lock_disable": True,
                },
            )
            try:
                self._device.open()
            except ConnectAuthError as err:
                raise AuthenticationError("Authentication failed") from err
            except ConnectionException as err:
                raise NoResponseError("Device did not respond within timeout") from err

        return self._device

    def get_interfaces(self) -> List[Dict[str, Any]]:
        vlan_map = self._get_untagged_vlans()

        def _convert(name, ifc):
            oper = ifc.get("is_up")
            if not isinstance(oper, bool) and iter(oper):
                oper = oper[0]  # sometimes, crazy multiple values are returned
            admin = ifc.get("is_enabled")
            if not isinstance(admin, bool) and iter(admin):
                admin = admin[0]  # sometimes, crazy multiple values are returned

            # fake a description from master interface if necessary
            descr = ifc["description"]
            if not descr and is_unit(name):
                master, _ = split_master_unit(name)
                if master in self.interfaces:
                    descr = self.interfaces[master]["description"]

            return {
                "name": name,
                "description": descr,
                "oper": SNMP_STATUS_MAP[oper],
                "admin": SNMP_STATUS_MAP[admin],
                "vlan": vlan_map.get(name),
            }

        return [_convert(name, ifc) for name, ifc in self.interfaces.items()]

    def _get_untagged_vlans(self):
        # This table gets us tagged/untagged VLANs for each interface
        switching = EthernetSwitchingInterfaceTable(self.device.device)
        switching.get()

        return {
            port.ifname: vlan.tag
            for port in switching
            for vlan in port.vlans
            if not vlan.tagged
        }

    def get_netbox_vlans(self) -> List[FantasyVlan]:
        vlan_objects = manage.Vlan.objects.filter(
            swportvlan__interface__netbox=self.netbox
        ).distinct()

        def _make_vlan(vlan):
            tag = int(vlan.tag)
            try:
                vlan_object = vlan_objects.get(vlan=tag)
            except (manage.Vlan.DoesNotExist, manage.Vlan.MultipleObjectsReturned):
                return FantasyVlan(tag, netident=vlan.name)
            else:
                return FantasyVlan(
                    tag, netident=vlan_object.net_ident, descr=vlan_object.description
                )

        result = {
            _make_vlan(vlan) for vlan in self.vlans if vlan.status.upper() == "ENABLED"
        }
        return sorted(result, key=attrgetter("vlan"))

    def get_native_and_trunked_vlans(self, interface) -> Tuple[int, List[int]]:
        switching = EthernetSwitchingInterfaceTable(self.device.device)
        switching.get(interface_name=interface.ifname)
        vlans = switching[interface.ifname].vlans
        tagged = [vlan.tag for vlan in vlans if vlan.tagged]
        untagged = first_true(vlans, pred=lambda vlan: not vlan.tagged)
        return (untagged.tag if untagged else None), tagged

    def set_interface_description(self, interface: manage.Interface, description: str):
        # never set description on units but on master interface
        master, _ = split_master_unit(interface.ifname)
        description = description.replace('"', r"\"")  # escape quotes

        if description:
            config = TEMPLATE_SET_INTERFACE_DESCRIPTION.format(
                ifname=master, descr=description
            )
        else:
            config = TEMPLATE_DELETE_INTERFACE_DESCRIPTION.format(ifname=master)
        self.device.load_merge_candidate(config=config)

    def set_vlan(self, interface: manage.Interface, vlan: int):
        master, unit = split_master_unit(interface.ifname)
        if not unit:
            raise ManagementError(
                "Cannot set vlan members on non-units", interface.ifname
            )

        config = TEMPLATE_RESET_VLAN_MEMBERS.format(
            ifname=master, unit=unit, members=vlan
        )
        self.device.load_merge_candidate(config=config)

    def get_interface_admin_status(self, interface: manage.Interface) -> int:
        ifc = self.interfaces[interface.ifname]
        admin = ifc.get("is_enabled")
        if not isinstance(admin, bool) and iter(admin):
            admin = admin[0]  # sometimes, crazy multiple values are returned

        return SNMP_STATUS_MAP[admin]

    def cycle_interface(self, interface: manage.Interface, wait: float = 5.0):
        # It isn't clear yet how to do this on Juniper, since PortAdmin performs this
        # step before the configuration alterations are actually committed.
        pass

    def commit_configuration(self):
        self.device.commit_config(message="Committed from NAV/PortAdmin")

    @property
    def vlans(self):
        """A cached representation of Juniper VLAN table"""
        if not self._vlans:
            self._vlans = VlanTable(self.device.device)
            self._vlans.get()
        return self._vlans

    @property
    def interfaces(self):
        """A cached representation of the NAPALM get_interfaces result"""
        if not self._interfaces:
            self._interfaces = self.device.get_interfaces()
        return self._interfaces

    @property
    def ports(self):
        """A cached representation of the switch' ethernet port table"""
        if not self._ports:
            self._ports = EthPortTable(self.device.device)
            self._ports.get()
        return self._ports

    def raise_if_not_configurable(self):
        # FIXME: This is just for prototyping, must change to something sense-making
        if self.netbox.type.get_enterprise_id() != VENDOR_ID_JUNIPER_NETWORKS_INC:
            raise DeviceNotConfigurableError("Can only configure JunOS devices")


# Helper functions


def is_unit(name: str) -> bool:
    """Returns True if name is the name of an interface sub-unit"""
    names = name.split(".")
    return len(names) == 2


def split_master_unit(name: str) -> Tuple[str, str]:
    """Splits an interface name into master and unit parts, if applicable"""
    names = name.split(".")
    if len(names) == 2:
        return names
    else:
        return name, None
