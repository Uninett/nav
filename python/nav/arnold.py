#
# Copyright (C) 2018 Uninett AS
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

"""
Provides helpfunctions for Arnold web and script
"""

import re
import os
import configparser

import logging
import socket
from datetime import datetime, timedelta
from collections import namedtuple
from smtplib import SMTPException
from typing import Callable

from IPy import IP
from django.db import connection
from django.core.mail import EmailMessage

import nav.Snmp
from nav.Snmp.errors import AgentError
import nav.bitvector
import nav.buildconf
from nav.Snmp.profile import get_snmp_session_for_profile
from nav.config import find_config_file
from nav.errors import GeneralException
from nav.models.arnold import Identity, Event
from nav.models.manage import Interface, Prefix
from nav.netbiostracker.tracker import scan, parse_get_workstations
from nav.portadmin.management import ManagementFactory
from nav.portadmin.snmp.base import NoReadWriteManagementProfileError
from nav.util import is_valid_ip

CONFIGFILE = os.path.join("arnold", "arnold.conf")
NONBLOCKFILE = os.path.join("arnold", "nonblock.conf")
_logger = logging.getLogger(__name__)

Candidate = namedtuple("Candidate", "camid ip mac interface endtime")


class Memo(object):
    """Simple config file memoization"""

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, filename):
        if filename in self.cache:
            if self.is_changed(filename):
                return self.store(filename)
            else:
                return self.cache[filename][0]
        else:
            return self.store(filename)

    def is_changed(self, filename):
        """Check if file is changed since last cache"""
        mtime = os.path.getmtime(filename)
        if mtime != self.cache[filename][1]:
            return True
        return False

    def store(self, filename):
        """Run function, store result and modification time in cache"""
        value = self.func(filename)
        mtime = os.path.getmtime(filename)
        self.cache[filename] = (value, mtime)
        return value


class ChangePortStatusError(GeneralException):
    """An error occured when changing portadminstatus"""

    pass


class ChangePortVlanError(GeneralException):
    """An error occured when changing portvlan"""

    pass


class NoDatabaseInformationError(GeneralException):
    """No information available for id"""

    pass


class PortNotFoundError(GeneralException):
    """Could not find port in database"""

    pass


class UnknownTypeError(GeneralException):
    """Unknown type (not ip or mac)"""

    pass


class DbError(GeneralException):
    """Error when querying database"""

    pass


class NotSupportedError(GeneralException):
    """This vendor does not support snmp set of vlan"""

    pass


class NoSuchProgramError(GeneralException):
    """No such program"""

    pass


class DetainmentNotAllowedError(GeneralException):
    """Detainment not allowed"""

    pass


class WrongCatidError(DetainmentNotAllowedError):
    """Arnold is not permitted to block ports on equipment of this category"""

    pass


class AlreadyBlockedError(DetainmentNotAllowedError):
    """This port is already blocked or quarantined."""

    pass


class InExceptionListError(DetainmentNotAllowedError):
    """This ip-address is in the exceptionlist and cannot be blocked."""

    pass


class FileError(GeneralException):
    """Fileerror"""

    pass


class BlockonTrunkError(DetainmentNotAllowedError):
    """No action on trunked interface allowed"""

    pass


def find_id_information(ip_or_mac, limit, trunk_ok=False):
    """Look in arp and cam tables to find camtuple with ip_or_mac

    Returns $limit number of Candidates

    If ip_or_mac is ip, then we can find info in arp. If it is a mac-address
    we cannot find ip-address and it is set to a default value. In both
    cases we are able to find the interface where the ip_or_mac is located.

    """
    cursor = connection.cursor()
    category = find_input_type(ip_or_mac)

    # Get data from database based on id
    if category not in ['IP', 'MAC']:
        raise UnknownTypeError(ip_or_mac)

    query = ""
    if category == 'IP':
        # Find cam and arp-data which relates to the time where this ip was
        # last active.
        query = """
        SELECT *, cam.start_time AS starttime, cam.end_time AS endtime
        FROM cam
        JOIN (SELECT ip, mac, start_time AS ipstarttime,
        end_time AS ipendtime
              FROM arp
              WHERE ip=%s
              ORDER BY end_time DESC
              LIMIT 2) arpaggr USING (mac)
        LEFT JOIN interface ON (cam.ifindex=interface.ifindex
                            AND cam.netboxid=interface.netboxid)
        WHERE (cam.start_time, cam.end_time)
        OVERLAPS (arpaggr.ipstarttime, arpaggr.ipendtime)
        ORDER BY endtime DESC
        LIMIT %s
        """

    elif category == 'MAC':
        # Fetch last camtuple regarding this macaddress
        query = """
        SELECT *, cam.start_time AS starttime, cam.end_time AS endtime
        FROM cam
        LEFT JOIN interface ON (cam.ifindex=interface.ifindex
                            AND cam.netboxid=interface.netboxid)
        WHERE mac = %s
        ORDER BY endtime DESC
        LIMIT %s
        """

    cursor.execute(query, [ip_or_mac, limit])
    result = dictfetchall(cursor)
    candidates = create_candidates(result, trunk_ok)
    if candidates:
        return candidates
    else:
        raise NoDatabaseInformationError(ip_or_mac)


def find_input_type(ip_or_mac):
    """Try to determine whether input is a valid ip-address,
    mac-address or an swportid. Return type and reformatted input as a
    tuple"""
    # Support mac-adresses on xx:xx... format
    ip_or_mac = str(ip_or_mac)
    mac = ip_or_mac.replace(':', '')

    input_type = "UNKNOWN"
    if is_valid_ip(ip_or_mac, strict=True):
        input_type = "IP"
    elif re.match("^[A-Fa-f0-9]{12}$", mac):
        input_type = "MAC"
    elif re.match(r"^\d+$", ip_or_mac):
        input_type = "SWPORTID"

    return input_type


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()]


def create_candidates(caminfos, trunk_ok=False):
    """Create candidates"""
    candidates = []
    for caminfo in caminfos:
        if 'ip' not in caminfo:
            caminfo['ip'] = '0.0.0.0'
        try:
            interface = Interface.objects.get(pk=caminfo['interfaceid'])
            raise_if_detainment_not_allowed(interface, trunk_ok=trunk_ok)
        except (Interface.DoesNotExist, DetainmentNotAllowedError):
            continue
        else:
            candidates.append(
                Candidate(
                    caminfo['camid'],
                    caminfo['ip'],
                    caminfo['mac'],
                    interface,
                    caminfo['endtime'],
                )
            )
    return candidates


def find_computer_info(ip_or_mac, trunk_ok=False):
    """Return the latest entry from the cam table for ip_or_mac"""
    return find_id_information(ip_or_mac, 5, trunk_ok)[0]


def disable(candidate, justification, username, comment="", autoenablestep=0):
    """Disable a target by blocking the port"""
    _logger.info(
        'Disabling %s - %s on interface %s',
        candidate.ip,
        candidate.mac,
        candidate.interface,
    )

    if not candidate.interface.netbox.get_preferred_snmp_management_profile(
        require_write=True
    ):
        raise NoReadWriteManagementProfileError(
            "%s has no read-write management profile" % candidate.interface.netbox
        )
    identity = check_identity(candidate)
    change_port_status('disable', identity)
    identity.status = 'disabled'
    update_identity(identity, justification, autoenablestep)
    create_event(identity, comment, username)

    _logger.info("Successfully %s %s (%s)", identity.status, identity.ip, identity.mac)


def quarantine(candidate, qvlan, justification, username, comment="", autoenablestep=0):
    """Quarantine a target bu changing vlan on port"""
    _logger.info(
        'Quarantining %s - %s on interface %s',
        candidate.ip,
        candidate.mac,
        candidate.interface,
    )

    if not candidate.interface.netbox.get_preferred_snmp_management_profile(
        require_write=True
    ):
        raise NoReadWriteManagementProfileError(
            "%s has no read-write management profile" % candidate.interface.netbox
        )
    identity = check_identity(candidate)
    identity.fromvlan = change_port_vlan(identity, qvlan.vlan)
    identity.tovlan = qvlan
    identity.status = 'quarantined'
    update_identity(identity, justification, autoenablestep)
    create_event(identity, comment, username)

    _logger.info("Successfully %s %s (%s)", identity.status, identity.ip, identity.mac)


def check_target(target, trunk_ok=False):
    """Check if target can be blocked or not"""
    _logger.debug('Checking target %s', target)
    if find_input_type(target) == 'IP':
        check_non_block(target)
    find_computer_info(target, trunk_ok)


def check_identity(candidate):
    """Create or return existing identity object based on target"""
    try:
        identity = Identity.objects.get(
            interface=candidate.interface, mac=candidate.mac
        )
        if identity.status != 'enabled':
            raise AlreadyBlockedError
        identity.ip = candidate.ip
    except Identity.DoesNotExist:
        identity = Identity()
        identity.interface = candidate.interface
        identity.ip = candidate.ip
        identity.mac = candidate.mac

    # Check if we should not detain this interface for some reason
    raise_if_detainment_not_allowed(identity.interface)

    return identity


def update_identity(identity, justification, autoenablestep):
    """Update an identity with common info"""
    identity.justification = justification
    identity.organization = identity.interface.netbox.organization
    identity.dns = get_host_name(identity.ip)
    identity.netbios = get_netbios(identity.ip)
    identity.textual_interface = str(identity.interface)
    if autoenablestep:
        identity.autoenable = datetime.now() + timedelta(days=autoenablestep)
        identity.autoenablestep = autoenablestep

    identity.save()


def create_event(identity, comment, username):
    """Create event for the action specified in identity"""
    event = Event(
        identity=identity,
        comment=comment,
        action=identity.status,
        justification=identity.justification,
        autoenablestep=identity.autoenablestep,
        executor=username,
    )
    event.save()


def raise_if_detainment_not_allowed(interface, trunk_ok=False):
    """Raises an exception if this interface should not be detained"""
    netbox = interface.netbox
    config = get_config(find_config_file(CONFIGFILE))
    allowtypes = [x.strip() for x in str(config.get('arnold', 'allowtypes')).split(',')]

    if netbox.category.id not in allowtypes:
        _logger.info("Not allowed to detain on %s", netbox.category.id)
        raise WrongCatidError(netbox.category)

    if not trunk_ok and interface.trunk:
        _logger.info("Cannot detain on a trunk")
        raise BlockonTrunkError


def open_port(identity, username, eventcomment=""):
    """
    Takes as input the identityid of the block and username. Opens the
    port (either enable or change vlan) and updates the database.

    If port is not found in the database we assume that the
    switch/module has been replaced. As this normally means that the
    port is enabled, we enable the port in the arnold-database.

    """

    try:
        identity.interface
    except Interface.DoesNotExist:
        _logger.info("Interface did not exist, enabling in database only")
    else:
        _logger.info(
            "Trying to lift detention for %s on %s", identity.mac, identity.interface
        )
        if identity.status == 'disabled':
            change_port_status('enable', identity)
        elif identity.status == 'quarantined':
            change_port_vlan(identity, identity.fromvlan)

    identity.status = 'enabled'
    identity.last_changed = datetime.now()
    identity.fromvlan = None
    identity.tovlan = None
    identity.autoenable = None
    identity.save()

    event = Event(
        identity=identity, comment=eventcomment, action='enabled', executor=username
    )
    event.save()

    _logger.info("openPort: Port successfully opened")


def change_port_status(
    action,
    identity,
    agent_getter: Callable = get_snmp_session_for_profile,
):
    """Use SNMP to change status on an interface.

    We use ifadminstatus to enable and disable ports
    ifAdminStatus has the following values:
    1 - up
    2 - down
    3 - testing (no operational packets can be passed)

    """
    oid = '.1.3.6.1.2.1.2.2.1.7'
    ifindex = identity.interface.ifindex
    query = oid + '.' + str(ifindex)

    # Create snmp-object
    netbox = identity.interface.netbox
    profile = netbox.get_preferred_snmp_management_profile(require_write=True)

    if not profile:
        raise NoReadWriteManagementProfileError(
            "%s has no read-write management profile" % netbox
        )

    agent = agent_getter(profile)(host=netbox.ip)

    # Disable or enable based on input
    try:
        if action == 'disable':
            agent.set(query, 'i', 2)
            _logger.info(
                'Setting ifadminstatus down on interface %s', identity.interface
            )
        elif action == 'enable':
            agent.set(query, 'i', 1)
            _logger.info('Setting ifadminstatus up on interface %s', identity.interface)
    except AgentError as why:
        _logger.error("Error when executing snmpquery: %s", why)
        raise ChangePortStatusError(why)


def change_port_vlan(identity, vlan):
    """
    Change switchport access vlan. Returns vlan on port before change.

    Reasons for not successful change may be:
    - Wrong community, use rw-community
    - rw-community not set on netbox
    - port is a trunk

    """
    interface = identity.interface
    netbox = interface.netbox

    agent = ManagementFactory().get_instance(netbox)
    try:
        fromvlan = agent.get_interface_native_vlan(interface)
    except Exception as error:  # noqa: BLE001
        raise ChangePortVlanError(error)
    else:
        _logger.info('Setting vlan %s on interface %s', vlan, interface)
        try:
            agent.set_vlan(interface, vlan)
            agent.cycle_interfaces([interface])
        except Exception as error:  # noqa: BLE001
            raise ChangePortVlanError(error)
        else:
            return fromvlan


def sendmail(from_email, toaddr, subject, msg):
    """Sends mail using Djangos internal mail system"""

    try:
        email = EmailMessage(subject, msg, from_email=from_email, to=[toaddr])
        email.send()
    except (SMTPException, socket.error) as error:
        _logger.error('Failed to send mail to %s: %s', toaddr, error)


def get_host_name(ip):
    """Get hostname based on ip-address. Return 'N/A' if not found."""
    hostname = "N/A"

    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except socket.herror:
        pass

    return hostname


def get_netbios(ip):
    """Get netbiosname of computer with ip"""

    netbios_dump = scan([ip], verbose=True)
    if not netbios_dump:
        return ""

    parsed_results = parse_get_workstations(netbios_dump)
    return parsed_results.get(ip, "")


def check_non_block(ip):
    """Checks if the ip is in the nonblocklist."""
    nonblockdict = parse_nonblock_file(find_config_file(NONBLOCKFILE))

    # We have the result of the nonblock.cfg-file in the dict
    # nonblockdict. This dict contains 3 things:
    # 1 - Specific ip-addresses
    # 2 - Ip-ranges (129.241.xxx.xxx/xx)
    # 3 - Ip lists (129.241.xxx.xxx-xxx)

    # Specific ip-addresses
    if ip in nonblockdict['ip']:
        _logger.info('Computer in nonblock list, skipping')
        raise InExceptionListError

    # Ip-ranges
    for ip_range in nonblockdict['range']:
        if ip in IP(ip_range):
            raise InExceptionListError


def compute_octet_string(hexstring, port, action='enable'):
    """
    hexstring: the returnvalue of the snmpquery
    port: the number of the port to add
    """

    bit = nav.bitvector.BitVector(hexstring)

    # Add port to string
    port -= 1
    if action == 'enable':
        bit[port] = 1
    else:
        bit[port] = 0

    return bit.to_bytes()


@Memo
def parse_nonblock_file(filename):
    """Parse nonblocklist and make it ready for use."""

    nonblockdict = {'ip': {}, 'range': {}}

    # Open nonblocklist, parse it.
    try:
        handle = open(filename)
    except IOError as why:
        raise FileError(why)

    for line in handle.readlines():
        line = line.strip()

        # Skip comments
        if line.startswith('#'):
            continue

        if re.search(r'^\d+\.\d+\.\d+\.\d+$', line):
            # Single ip-address
            nonblockdict['ip'][line] = 1
        elif re.search(r'^\d+\.\d+\.\d+\.\d+\/\d+$', line):
            # Range
            nonblockdict['range'][line] = 1

    handle.close()

    return nonblockdict


@Memo
def get_config(configfile):
    """Get config from file"""
    config = configparser.ConfigParser()
    config.read(configfile)
    return config


def is_inside_vlans(ip, vlans):
    """Check if ip is inside the vlans

    vlans: a string with comma-separated vlans.

    """
    vlans = [x.strip() for x in vlans.split(',')]

    # For each vlan, check if it is inside the prefix of the vlan.
    for vlan in vlans:
        if vlan.isdigit() and is_valid_ip(ip):
            if Prefix.objects.filter(vlan__vlan=vlan).extra(
                where=['%s << netaddr'], params=[ip]
            ):
                return True
    return False
