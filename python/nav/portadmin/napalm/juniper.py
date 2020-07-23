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
from typing import List, Any, Dict, Tuple, Sequence

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
TEMPLATE_DELETE_NATIVE_VLAN = """
delete interfaces {ifname} unit {unit} family ethernet-switching native-vlan-id
"""
TEMPLATE_SET_NATIVE_VLAN = """
set interfaces {ifname} unit {unit} family ethernet-switching native-vlan-id {native}
"""
TEMPLATE_SET_PORT_MODE = """
set interfaces {ifname} unit {unit} family ethernet-switching port-mode {mode}
"""
TEMPLATE_DISABLE_PORT = "set interfaces {ifname} disable"
TEMPLATE_ENABLE_PORT = "delete interfaces {ifname} disable"


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
        self._interfaces = {}
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

    def get_interfaces(
        self, interfaces: Sequence[manage.Interface] = None
    ) -> List[Dict[str, Any]]:
        vlan_map = self._get_untagged_vlans()
        args = (interfaces[0].ifname,) if len(interfaces) == 1 else ()
        interfaces = self.get_interface_information(*args)

        def _convert(name, ifc):
            oper = ifc.get("is_up")
            admin = ifc.get("is_enabled")

            # fake a description from master interface if necessary
            descr = ifc["description"]
            if not descr and is_unit(name):
                master, _ = split_master_unit(name)
                if master in interfaces:
                    descr = interfaces[master]["description"]

            return {
                "name": name,
                "description": descr,
                "oper": SNMP_STATUS_MAP[oper],
                "admin": SNMP_STATUS_MAP[admin],
                "vlan": vlan_map.get(name),
            }

        return [_convert(name, ifc) for name, ifc in interfaces.items()]

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

    def get_interface_native_vlan(self, interface: manage.Interface) -> int:
        untagged, _ = self.get_native_and_trunked_vlans(interface)
        return untagged

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

    def set_access(self, interface: manage.Interface, access_vlan: int):
        master, unit = split_master_unit(interface.ifname)
        if not unit:
            raise ManagementError(
                "Cannot set vlan config on non-units", interface.ifname
            )

        current = InterfaceConfigTable(self.device.device).get(master)[master]

        # Deleting native vlan id is only appropriate if the element exists already
        templates = [TEMPLATE_DELETE_NATIVE_VLAN] if current["native_vlan"] else []
        templates += [TEMPLATE_SET_PORT_MODE, TEMPLATE_RESET_VLAN_MEMBERS]

        config = "\n".join(
            tmpl.format(ifname=master, unit=unit, mode="access", members=access_vlan)
            for tmpl in templates
        )
        self.device.load_merge_candidate(config=config)
        self._save_access_interface(interface, access_vlan)

    def _save_access_interface(self, interface: manage.Interface, access_vlan: int):
        """Updates the Interface entry in the database with access config"""
        interface.trunk = False
        interface.vlan = access_vlan
        try:
            allowedvlans = interface.swportallowedvlan
            allowedvlans.save()
        except manage.SwPortAllowedVlan.DoesNotExist:
            pass
        interface.save()

    def set_trunk(
        self, interface: manage.Interface, native_vlan: int, trunk_vlans: Sequence[int]
    ):
        master, unit = split_master_unit(interface.ifname)
        if not unit:
            raise ManagementError(
                "Cannot set vlan config on non-units", interface.ifname
            )

        members = " ".join(str(tag) for tag in trunk_vlans)
        templates = [
            TEMPLATE_SET_PORT_MODE,
            TEMPLATE_SET_NATIVE_VLAN,
            TEMPLATE_RESET_VLAN_MEMBERS,
        ]
        config = "\n".join(
            tmpl.format(
                ifname=master,
                unit=unit,
                mode="trunk",
                native=native_vlan,
                members=members,
            )
            for tmpl in templates
        )

        self.device.load_merge_candidate(config=config)
        self._save_trunk_interface(interface, native_vlan, trunk_vlans)

    @staticmethod
    def _save_trunk_interface(
        interface: manage.Interface, native_vlan: int, trunk_vlans: Sequence[int]
    ):
        """Updates the Interface entry in the database with trunk config"""
        interface.trunk = True
        interface.vlan = native_vlan
        allowedvlan, _ = manage.SwPortAllowedVlan.objects.get_or_create(
            interface=interface
        )
        allowedvlan.set_allowed_vlans(trunk_vlans)
        allowedvlan.save()
        interface.save()

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

    def set_interface_down(self, interface: manage.Interface):
        # does not set oper on logical units, only on physical masters
        master, unit = split_master_unit(interface.ifname)
        config = TEMPLATE_DISABLE_PORT.format(ifname=master)
        self.device.load_merge_candidate(config=config)

        self._save_interface_oper(interface, interface.OPER_DOWN)

    def set_interface_up(self, interface: manage.Interface):
        # does not set oper on logical units, only on physical masters
        master, unit = split_master_unit(interface.ifname)
        config = TEMPLATE_ENABLE_PORT.format(ifname=master)
        self.device.load_merge_candidate(config=config)

        self._save_interface_oper(interface, interface.OPER_UP)

    def _save_interface_oper(self, interface: manage.Interface, ifoperstatus: int):
        master, unit = split_master_unit(interface.ifname)
        interface.ifoperstatus = ifoperstatus
        if unit:  # this was a logical unit, also set the state of the master ifc
            master_interface = manage.Interface.objects.filter(
                netbox=interface.netbox, ifname=master
            )
            master_interface.update(ifoperstatus=ifoperstatus)

    def commit_configuration(self):
        # Only take our sweet time to commit if there are pending changes
        if self.device.compare_config():
            self.device.commit_config(message="Committed from NAV/PortAdmin")

    @property
    def vlans(self):
        """A cached representation of Juniper VLAN table"""
        if not self._vlans:
            self._vlans = VlanTable(self.device.device)
            self._vlans.get()
        return self._vlans

    def get_interface_information(self, interface_name: str = None):
        """Retrieves operational information about ethernet interfaces.

        Getting the full interface table can be slow, especially on stacked switches,
        so this method will use internal caching.

        :param interface_name: Optional interface name to fetch. If specified,
                               only data for matching interface names are retrieved
                               (however, the result may contain data for more interfaces
                               if old data is in the cache).
        """
        # Unable to get PyEZ tables to set a proper key if matching both physical and
        # logical interfaces in a single table, so doing this rpc manually
        if not self._interfaces or (
            interface_name and interface_name not in self._interfaces
        ):
            tree = self.device.device.rpc.get_interface_information(
                terse=True,
                interface_name=interface_name if interface_name else "[afgxe][et]-*",
            )
            self._interfaces.update(self._parse_interface_tree(tree))
        return self._interfaces

    @staticmethod
    def _parse_interface_tree(tree):
        def findtext(elem, text):
            found = elem.findtext(text)
            return found.strip() if found else None

        return {
            findtext(elem, "name"): {
                "name": findtext(elem, "name"),
                "description": findtext(elem, "description"),
                "is_up": findtext(elem, "oper-status") == "up",
                "is_enabled": findtext(elem, "admin-status") == "up",
            }
            for elem in tree.xpath(
                "physical-interface | physical-interface/logical-interface"
            )
        }

    def raise_if_not_configurable(self):
        # FIXME: This is just for prototyping, must change to something sense-making
        if self.netbox.type.get_enterprise_id() != VENDOR_ID_JUNIPER_NETWORKS_INC:
            raise DeviceNotConfigurableError("Can only configure JunOS devices")

    # These are not relevant for Juniper
    get_cisco_voice_vlans = None
    set_cisco_voice_vlan = None
    enable_cisco_cdp = None
    disable_cisco_voice_vlan = None
    disable_cisco_cdp = None


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
