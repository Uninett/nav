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
from typing import Any, Optional, Sequence

from django.template.loader import get_template
from napalm.base.exceptions import ConnectAuthError, ConnectionException
from jnpr.junos.op.vlan import VlanTable
from jnpr.junos.exception import RpcError
from lxml.etree import ElementTree

from nav.napalm import connect as napalm_connect
from nav.enterprise.ids import VENDOR_ID_JUNIPER_NETWORKS_INC
from nav.models import manage
from nav.portadmin.handlers import (
    ManagementHandler,
    DeviceNotConfigurableError,
    AuthenticationError,
    NoResponseError,
    ProtocolError,
    PoeState,
    POEStateNotSupportedError,
    POENotSupportedError,
    XMLParseError,
)
from nav.junos.nav_views import (
    EthernetSwitchingInterfaceTable,
    ElsEthernetSwitchingInterfaceTable,
    ElsEthernetSwitchingInterfaceTableJunOS20,
    InterfaceConfigTable,
    ElsVlanTable,
)

from nav.portadmin.vlan import FantasyVlan
from nav.util import first_true

__all__ = ["Juniper"]

# This maps interface oper/admin status values to SNMP values as used in NAV's data
# model. See IF-MIB::ifOperStatus and IF-MIB::ifAdminStatus from RFC 2863 for details.
SNMP_STATUS_MAP = {"up": 1, "down": 2, True: 1, False: 2}


def wrap_unhandled_rpc_errors(func):
    """Decorates RPC-enabled handler function to ensure unhandled RpcErrors are
    translated into ProtocolErrors, which can be reported nicely to the end user by
    the PortAdmin framework
    """

    def wrap_rpc_errors(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RpcError as error:
            raise ProtocolError(f"Device raised RpcError: {error.message}") from error

    return wrap_rpc_errors


class Juniper(ManagementHandler):
    """Juniper specific version of a Napalm PortAdmin handler.

    Juniper switches do things a bit differently from the standard model supported by
    NAV. VLAN config is put on logical sub-units of the physical ports. SNMP-wise,
    sub-units are presented as interfaces on a conceptually higher level than their
    "parent" interface. NAV doesn't really understand or care about this unusual
    relationship between pairs of interfaces - it will only see that the interfaces
    are somehow related.

    On non-ELS switches, the sub-interfaces are reported in the BRIDGE-MIB and
    Q-BRIDGE-MIB, causing NAV to view these units as the actual switch ports. On ELS
    switches, the parent interfaces are reported as the switch ports - yet, VLAN config
    still belongs on unit 0 when uploading config changes outside of SNMP.

    This implementation will therefore always consider any given switch port
    reference to be a pair of master/unit interfaces, regardless of whether the
    reference is to the master or the unit. When building new configuration, it will
    split configuration options appropriatelt between the master and the unit before
    uploading and merging config changes using NAPALM/PyEZ.
    """

    VENDOR = VENDOR_ID_JUNIPER_NETWORKS_INC
    PROTOCOL = manage.ManagementProfile.PROTOCOL_NAPALM
    POE_ENABLED = PoeState(state=1, name="ENABLED")
    POE_DISABLED = PoeState(state=2, name="DISABLED")
    POE_OPTIONS = [POE_ENABLED, POE_DISABLED]

    def __init__(self, netbox: manage.Netbox, **kwargs):
        super().__init__(netbox, **kwargs)
        self._device = None
        self._profile = None
        self._interfaces = {}
        self._vlans = None
        self._is_els = None

    @property
    def profile(self) -> manage.ManagementProfile:
        """Returns the selected NAPALM profile for this netbox"""
        if not self._profile:
            self._profile = self.netbox.profiles.filter(protocol=self.PROTOCOL).first()
        return self._profile

    @property
    def device(self):
        """Opens a device connection or returns an existing one"""
        if not self._device:
            self.raise_if_not_configurable()
            try:
                self._device = napalm_connect(self.netbox, self.profile)
            except ConnectAuthError as err:
                raise AuthenticationError("Authentication failed") from err
            except ConnectionException as err:
                raise NoResponseError("Device did not respond within timeout") from err

        return self._device

    @property
    def is_els(self) -> bool:
        """Returns True if this is an ELS config style Juniper switch"""
        if self._is_els is None:
            self._is_els = self.device.device.facts.get("switch_style") == "VLAN_L2NG"
        return self._is_els

    @property
    def _els_ethernet_switching_interface_table(self):
        return (
            ElsEthernetSwitchingInterfaceTable
            if self.junos_major_version < 20
            else ElsEthernetSwitchingInterfaceTableJunOS20
        )

    @property
    def junos_major_version(self) -> int:
        """Returns the major JunOS version running on the switch"""
        version = self.device.device.facts.get("version")
        if version:
            major, _ = version.split(".", maxsplit=1)
            return int(major)

    def get_interfaces(
        self, interfaces: Sequence[manage.Interface] = None
    ) -> list[dict[str, Any]]:
        vlan_map = self._get_untagged_vlans()
        if interfaces and len(interfaces) == 1:
            # we can use a filter if only a single interface was specified
            interfaces = self.get_interface_information(interfaces[0].ifname)
        else:
            interfaces = self.get_interface_information()

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
        if not self.is_els:
            # This table gets us tagged/untagged VLANs for each interface
            switching = EthernetSwitchingInterfaceTable(self.device.device)
            switching.get()

            return {
                port.ifname: vlan.tag
                for port in switching
                for vlan in port.vlans
                if not vlan.tagged
            }
        else:
            switching = self._els_ethernet_switching_interface_table(self.device.device)
            switching.get()
            return {port.ifname: port.tag for port in switching if not port.tagged}

    def get_netbox_vlans(self) -> list[FantasyVlan]:
        vlan_objects = manage.Vlan.objects.filter(
            swport_vlans__interface__netbox=self.netbox
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
            _make_vlan(vlan)
            for vlan in self.vlans
            if isinstance(vlan.tag, int) or vlan.tag.isdigit()
        }
        return sorted(result, key=attrgetter("vlan"))

    def get_netbox_vlan_tags(self) -> list[int]:
        return [vlan.tag for vlan in self.vlans]

    def get_interface_native_vlan(self, interface: manage.Interface) -> int:
        untagged, _ = self.get_native_and_trunked_vlans(interface)
        return untagged

    def set_native_vlan(self, interface: manage.Interface, vlan: int):
        raise NotImplementedError  # This is in fact never used on Juniper!

    def get_native_and_trunked_vlans(self, interface) -> tuple[int, list[int]]:
        if not self.is_els:
            switching = EthernetSwitchingInterfaceTable(self.device.device)
            switching.get(interface_name=interface.ifname)
            vlans = switching[interface.ifname].vlans
        else:
            switching = self._els_ethernet_switching_interface_table(self.device.device)
            switching.get(interface_name=interface.ifname)
            vlans = [vlan for vlan in switching if vlan.tagged is not None]

        tagged = [vlan.tag for vlan in vlans if vlan.tagged]
        untagged = first_true(vlans, pred=lambda vlan: not vlan.tagged)
        return (untagged.tag if untagged else None), tagged

    @wrap_unhandled_rpc_errors
    def set_interface_description(self, interface: manage.Interface, description: str):
        # never set description on units but on master interface
        master, _ = split_master_unit(interface.ifname)
        context = {
            "is_els": self.is_els,
            "ifname": master,
            "description": description.replace('"', r"\""),  # escape quotes
        }
        template = get_template("portadmin/junos-set-interface-description.djt")
        config = template.render(context)
        self.device.load_merge_candidate(config=config)

    @wrap_unhandled_rpc_errors
    def set_vlan(self, interface: manage.Interface, vlan: int):
        self.set_access(interface, vlan)

    @wrap_unhandled_rpc_errors
    def set_access(self, interface: manage.Interface, access_vlan: int):
        master, unit = split_master_unit(interface.ifname)
        current = InterfaceConfigTable(self.device.device).get(master)[master]
        template = get_template("portadmin/junos-set-access-port-vlan.djt")
        context = {
            "is_els": self.is_els,
            "delete_native_vlan": bool(current["native_vlan"]),
            "ifname": master,
            "unit": unit,
            "members": access_vlan,
        }
        config = template.render(context)
        self.device.load_merge_candidate(config=config)
        self._save_access_interface(interface, access_vlan)

    @staticmethod
    def _save_access_interface(interface: manage.Interface, access_vlan: int):
        """Updates the Interface entry in the database with access config"""
        interface.trunk = False
        interface.vlan = access_vlan
        try:
            allowedvlans = interface.swport_allowed_vlan
            allowedvlans.save()
        except manage.SwPortAllowedVlan.DoesNotExist:
            pass
        interface.save()

    @wrap_unhandled_rpc_errors
    def set_trunk(
        self, interface: manage.Interface, native_vlan: int, trunk_vlans: Sequence[int]
    ):
        master, unit = split_master_unit(interface.ifname)
        template = get_template("portadmin/junos-set-trunk-port-vlans.djt")
        members = " ".join(str(tag) for tag in trunk_vlans)
        context = {
            "is_els": self.is_els,
            "ifname": master,
            "unit": unit,
            "native_vlan": native_vlan,
            "members": members,
        }
        config = template.render(context)
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
        info = self.get_interface_information(interface.ifname)
        ifc = info[interface.ifname]
        admin = ifc.get("is_enabled")
        if admin and not isinstance(admin, bool) and iter(admin):
            admin = admin[0]  # sometimes, crazy multiple values are returned

        return SNMP_STATUS_MAP[admin]

    def cycle_interfaces(
        self,
        interfaces: Sequence[manage.Interface],
        wait: float = 0,
        commit: bool = False,
    ):
        # There is no need for waiting on Juniper; there is a need to commit,
        # and that operation will likely delay at least as much as the wait would have
        return super().cycle_interfaces(interfaces=interfaces, wait=0, commit=True)

    @wrap_unhandled_rpc_errors
    def set_interface_down(self, interface: manage.Interface):
        # does not set oper on logical units, only on physical masters
        master, _unit = split_master_unit(interface.ifname)
        template = get_template("portadmin/junos-disable-interface.djt")
        config = template.render({"ifname": master, "disable": True})
        self.device.load_merge_candidate(config=config)

        self._save_interface_oper(interface, interface.OPER_DOWN)

    @wrap_unhandled_rpc_errors
    def set_interface_up(self, interface: manage.Interface):
        # does not set oper on logical units, only on physical masters
        master, _unit = split_master_unit(interface.ifname)
        template = get_template("portadmin/junos-disable-interface.djt")
        config = template.render({"ifname": master, "disable": False})
        self.device.load_merge_candidate(config=config)

        self._save_interface_oper(interface, interface.OPER_UP)

    @staticmethod
    def _save_interface_oper(interface: manage.Interface, ifoperstatus: int):
        master, unit = split_master_unit(interface.ifname)
        interface.ifoperstatus = ifoperstatus
        if unit:  # this was a logical unit, also set the state of the master ifc
            master_interface = manage.Interface.objects.filter(
                netbox=interface.netbox, ifname=master
            )
            master_interface.update(ifoperstatus=ifoperstatus)

    @wrap_unhandled_rpc_errors
    def commit_configuration(self):
        # Only take our sweet time to commit if there are pending changes
        if self.device.compare_config():
            self.device.commit_config(message="Committed from NAV/PortAdmin")

    @property
    def vlans(self):
        """A cached representation of Juniper VLAN table"""
        if not self._vlans:
            self._vlans = (
                ElsVlanTable(self.device.device)
                if self.is_els
                else VlanTable(self.device.device)
            )
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
        if self.netbox.type.get_enterprise_id() != VENDOR_ID_JUNIPER_NETWORKS_INC:
            raise DeviceNotConfigurableError("Can only configure JunOS devices")
        if not self.profile:
            raise DeviceNotConfigurableError("Device has no NAPALM profile")

    def get_poe_state_options(self) -> Sequence[PoeState]:
        """Returns the available options for enabling/disabling PoE on this netbox"""
        return self.POE_OPTIONS

    @wrap_unhandled_rpc_errors
    def set_poe_state(self, interface: manage.Interface, state: PoeState):
        """Set state for enabling/disabling PoE on this interface.
        Available options should be retrieved using `get_poe_state_options`
        """
        if not isinstance(state, PoeState):
            raise TypeError("state must be a PoeState object")
        if state == self.POE_ENABLED:
            template = get_template("portadmin/junos-enable-poe.djt")
        elif state == self.POE_DISABLED:
            template = get_template("portadmin/junos-disable-poe.djt")
        else:
            raise POEStateNotSupportedError(f"state {state} is not a valid state")
        master, _ = split_master_unit(interface.ifname)
        config = template.render({"ifname": master})
        self.device.load_merge_candidate(config=config)

    def get_poe_states(
        self, interfaces: Optional[Sequence[manage.Interface]] = None
    ) -> dict[str, Optional[PoeState]]:
        """Retrieves current PoE state for interfaces on this device.

        :param interfaces: Optional sequence of interfaces to filter for, as fetching
                           data for all interfaces may be a waste of time if only a
                           single interface is needed. If this parameter is omitted,
                           the default behavior is to filter on all Interface objects
                           registered for this device.
        :returns: A dict mapping interfaces to their discovered PoE state.
                  The key matches the `ifname` attribute for the related
                  Interface object.
                  The value will be None if the interface does not support PoE.
        """
        if not interfaces:
            if self.netbox.interfaces:
                interfaces = self.netbox.interfaces
            else:
                return {}
        if len(interfaces) == 1:
            interface = interfaces[0]
            try:
                state = self._get_single_poe_state(interface)
            except POENotSupportedError:
                state = None
            return {interface.ifname: state}
        else:
            return self._get_poe_states_bulk(interfaces)

    def _get_single_poe_state(self, interface: manage.Interface) -> PoeState:
        tree = self._get_poe_interface_information(ifname=interface.ifname)
        matching_elements = tree.xpath(
            "//poe/interface-information-detail/interface-enabled-detail"
        )
        # Interfaces that do not support PoE will not have this element
        if not matching_elements:
            raise POENotSupportedError(
                f"Interface {interface.ifname} does not support PoE"
            )
        if len(matching_elements) != 1:
            raise XMLParseError(
                f"Expected 1 matching element in xml response, "
                f"{len(matching_elements)} found"
            )
        ifenabled = matching_elements[0].text.lower()
        return self._poe_string_to_state(ifenabled)

    def _get_poe_states_bulk(
        self, interfaces: Sequence[manage.Interface]
    ) -> dict[str, Optional[PoeState]]:
        tree = self._get_all_poe_interface_information()
        interface_information_elements = tree.findall(".//interface-information")
        ifname_to_state_dict = {}
        for element in interface_information_elements:
            ifname = element.findall(".//interface-name")[0].text.strip().lower()
            ifenabled = element.findall(".//interface-enabled")[0].text.strip().lower()
            ifname_to_state_dict[ifname] = self._poe_string_to_state(ifenabled)
        ifindex_to_state_dict = {
            interface.ifname: ifname_to_state_dict.get(interface.ifname.lower())
            for interface in interfaces
        }
        return ifindex_to_state_dict

    @wrap_unhandled_rpc_errors
    def _get_all_poe_interface_information(self) -> ElementTree:
        return self.device.device.rpc.get_poe_interface_information()

    @wrap_unhandled_rpc_errors
    def _get_poe_interface_information(self, ifname: str) -> ElementTree:
        return self.device.device.rpc.get_poe_interface_information(ifname=ifname)

    def _poe_string_to_state(self, state_str: str) -> PoeState:
        """Converts from internal juniper state names to
        corresponding PoeState objects
        """
        state_cleaned = state_str.strip().lower()
        if state_cleaned == "enabled":
            return self.POE_ENABLED
        elif state_cleaned == "disabled":
            return self.POE_DISABLED
        else:
            raise POEStateNotSupportedError(f"Unknown PoE state {state_str}")

    # FIXME Implement dot1x fetcher methods
    # dot1x authentication configuration fetchers aren't implemented yet, for lack
    # of configured devices to test on
    # def is_dot1x_enabled(self, interface: manage.Interface) -> bool:
    # def get_dot1x_enabled_interfaces(self) -> dict[str, bool]:
    # def is_port_access_control_enabled(self) -> bool:

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


def split_master_unit(name: str) -> tuple[str, str]:
    """Splits an interface name into master and unit parts. If the name doesn't
    already refer to a unit, unit 0 will be assumed.
    """
    names = name.split(".")
    if len(names) == 2:
        return names
    else:
        return name, "0"
