#
# Copyright 2008 (C) Norwegian University of Science and Technology
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

"""
Provides helpfunctions for Arnold web and script
"""

#pylint: disable=E1103

from __future__ import absolute_import

import re
import os
import ConfigParser
import logging
import socket
import email.message
import email.header
import email.charset
from datetime import datetime, timedelta
from IPy import IP
from subprocess import Popen, PIPE
from collections import namedtuple

import nav.Snmp
import nav.bitvector
import nav.buildconf
from nav import logs
from nav.errors import GeneralException
from nav.models.arnold import Identity, Event
from nav.models.manage import Interface
from django.db import connection  # import this after any django models
from nav.util import isValidIP

CONFIGFILE = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
NONBLOCKFILE = nav.buildconf.sysconfdir + "/arnold/nonblock.conf"
LOGGER = logging.getLogger("nav.arnold")

Candidate = namedtuple("Candidate", "camid ip mac interface endtime")


class Memo(object):
    """Simple config file memoization"""
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if args in self.cache:
            if self.is_changed(*args):
                return self.store(*args)
            else:
                return self.cache[args][0]
        else:
            return self.store(*args)

    def is_changed(self, *args):
        """Check if file is changed since last cache"""
        mtime = os.path.getmtime(*args)
        if mtime != self.cache[args][1]:
            return True
        return False

    def store(self, *args):
        """Run function, store result and modification time in cache"""
        value = self.func(*args)
        mtime = os.path.getmtime(*args)
        self.cache[args] = (value, mtime)
        return value


class ChangePortStatusError(GeneralException):
    """An error occured when changing portadminstatus"""
    pass


class ChangePortVlanError(GeneralException):
    """An error occured when changing portvlan"""
    pass


class NoDatabaseInformationError(GeneralException):
    """Could not find information in database for id"""
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


class WrongCatidError(GeneralException):
    """Arnold is not permitted to block ports on equipment of this category"""
    pass


class AlreadyBlockedError(GeneralException):
    """This port is already blocked or quarantined."""
    pass


class InExceptionListError(GeneralException):
    """This ip-address is in the exceptionlist and cannot be blocked."""
    pass


class FileError(GeneralException):
    """Fileerror"""
    pass


class BlockonTrunkError(GeneralException):
    """No action on trunked interface allowed"""
    pass


class NoReadWriteCommunityError(GeneralException):
    """No write community on switch"""
    pass


def find_id_information(ip_or_mac, limit):
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
    candidates = create_candidates(result)
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

    # idValidIP returns 10.0.0.0 if you type 10.0.0. Check that this is not the
    # case.
    input_type = "UNKNOWN"
    if isValidIP(ip_or_mac) and not isValidIP(ip_or_mac).endswith('.0'):
        input_type = "IP"
    elif re.match("^[A-Fa-f0-9]{12}$", mac):
        input_type = "MAC"
    elif re.match("^\d+$", ip_or_mac):
        input_type = "SWPORTID"

    return input_type


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [dict(
        zip([col[0] for col in desc], row)) for row in cursor.fetchall()]


def create_candidates(caminfos):
    """Create candidates"""
    candidates = []
    for caminfo in caminfos:
        if 'ip' not in caminfo:
            caminfo['ip'] = '0.0.0.0'
        interface = Interface.objects.get(pk=caminfo['interfaceid'])
        candidates.append(Candidate(caminfo['camid'], caminfo['ip'],
                                    caminfo['mac'], interface,
                                    caminfo['endtime']))
    return candidates


def find_computer_info(ip_or_mac):
    """Return the latest entry from the cam table for ip_or_mac"""
    return find_id_information(ip_or_mac, 1)[0]


def disable(candidate, justification, username, comment="", determined=False,
            autoenablestep=0):
    """Disable a target by blocking the port"""
    LOGGER.info('Disabling %s - %s on interface %s' % (
                candidate.ip, candidate.mac, candidate.interface))

    if not candidate.interface.netbox.read_write:
        raise NoReadWriteCommunityError
    identity = check_identity(candidate)
    change_port_status('disable', identity)
    identity.status = 'disabled'
    update_identity(identity, justification, determined, autoenablestep)
    create_event(identity, comment, username)

    LOGGER.info("Successfully %s %s (%s)" % (
                identity.status, identity.ip, identity.mac))


def quarantine(candidate, qvlan, justification, username, comment="",
               determined=False, autoenablestep=0):
    """Quarantine a target bu changing vlan on port"""
    LOGGER.info('Quarantining %s - %s on interface %s' % (
        candidate.ip, candidate.mac, candidate.interface))

    if not candidate.interface.netbox.read_write:
        raise NoReadWriteCommunityError
    identity = check_identity(candidate)
    identity.fromvlan = change_port_vlan(identity, qvlan.vlan)
    identity.tovlan = qvlan
    identity.status = 'quarantined'
    update_identity(identity, justification, determined, autoenablestep)
    create_event(identity, comment, username)

    LOGGER.info("Successfully %s %s (%s)" % (
                identity.status, identity.ip, identity.mac))


def check_target(target):
    """Check if target can be blocked or not"""
    LOGGER.debug('Checking target %s', target)
    if find_input_type(target) == 'IP':
        check_non_block(target)
    find_computer_info(target)


def check_identity(candidate):
    """Create or return existing identity object based on target"""
    try:
        identity = Identity.objects.get(interface=candidate.interface,
                                        mac=candidate.mac)
        if identity.status != 'enabled':
            LOGGER.info('This computer is already detained - skipping')
            raise AlreadyBlockedError
        identity.ip = candidate.ip
    except Identity.DoesNotExist:
        identity = Identity()
        identity.interface = candidate.interface
        identity.ip = candidate.ip
        identity.mac = candidate.mac

    # Check if we should not detain this interface for some reason
    should_detain(identity.interface)

    return identity


def update_identity(identity, justification, determined, autoenablestep):
    """Update an identity with common info"""
    identity.justification = justification
    identity.organization = identity.interface.netbox.organization
    identity.keep_closed = 'y' if determined else 'n'
    identity.dns = get_host_name(identity.ip)
    identity.netbios = get_netbios(identity.ip)
    if autoenablestep > 0:
        identity.autoenable = datetime.now() + timedelta(days=autoenablestep)
        identity.autoenablestep = autoenablestep

    identity.save()


def create_event(identity, comment, username):
    """Create event for the action specified in identity"""
    event = Event(identity=identity, comment=comment, action=identity.status,
                  justification=identity.justification,
                  autoenablestep=identity.autoenablestep,
                  executor=username)
    event.save()


def should_detain(interface):
    """Check if this interface should not be detained for some reason"""
    netbox = interface.netbox
    config = get_config(CONFIGFILE)
    allowtypes = [x.strip()
                  for x in str(config.get('arnold', 'allowtypes')).split(',')]

    if netbox.category.id not in allowtypes:
        LOGGER.info("Not allowed to detain on %s" % (netbox.category.id))
        raise WrongCatidError(netbox.category)

    if interface.trunk:
        LOGGER.info("Cannot detain on a trunk")
        raise BlockonTrunkError


def open_port(identity, username, eventcomment=""):
    """
    Takes as input the identityid of the block and username. Opens the
    port (either enable or change vlan) and updates the database.

    If port is not found in the database we assume that the
    switch/module has been replaced. As this normally means that the
    port is enabled, we enable the port in the arnold-database.

    """

    LOGGER.info("openPort: Trying to open identity with id %s" % identity.id)

    try:
        identity.interface
    except Interface.DoesNotExist:
        pass
    else:
        if identity.status == 'disabled':
            change_port_status('enable', identity)
        elif identity.status == 'quarantined':
            change_port_vlan(identity, identity.fromvlan)

    identity.status = 'enabled'
    identity.last_changed = datetime.now()
    identity.fromvlan = None
    identity.tovlan = None
    identity.save()

    event = Event(identity=identity, comment=eventcomment, action='enabled',
                  executor=username)
    event.save()

    LOGGER.info("openPort: Port successfully opened")


def change_port_status(action, identity):
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
    agent = nav.Snmp.Snmp(netbox.ip, netbox.read_write,
                          version=netbox.snmp_version)

    # Disable or enable based on input
    try:
        if action == 'disable':
            LOGGER.info("Disabling %s on %s with %s"
                        % (identity.interface, netbox.ip, query))
            #agent.set(query, 'i', 2)
        elif action == 'enable':
            LOGGER.info("Enabling %s on %s with %s"
                        % (identity.interface, netbox.ip, query))
            #agent.set(query, 'i', 1)

    except nav.Snmp.AgentError, why:
        LOGGER.error("Error when executing snmpquery: %s" % why)
        raise ChangePortStatusError(why)


def change_port_vlan(identity, vlan):
    """
    Change switchport access vlan. Returns vlan on port before change.

    Reasons for not successful change may be:
    - Wrong community, use rw-community
    - rw-community not set on netbox
    - port is a trunk

    oid for getting and setting vlan
    CISCO
    cisco.ciscoMgmt.ciscoVlanMembershipMIB.ciscoVlanMembershipMIBObjects.
    vmMembership.vmMembershipTable.vmMembershipEntry.vmVlan.<ifindex>

    """
    # Check vlanformat
    if not re.search('\d+', str(vlan)):
        raise ChangePortVlanError("Wrong format on vlan %s" % vlan)

    interface = identity.interface
    netbox = interface.netbox
    vendorid = netbox.type.vendor.id

    if vendorid == 'cisco':
        oid = "1.3.6.1.4.1.9.9.68.1.2.2.1.2"
        variable_type = 'i'
    elif vendorid == 'hp':
        oid = "1.3.6.1.2.1.17.7.1.4.5.1.1"
        variable_type = 'u'
    else:
        raise NotSupportedError(vendorid)

    query = oid + '.' + str(interface.ifindex)

    snmpget = nav.Snmp.Snmp(netbox.ip, netbox.read_only, netbox.snmp_version)
    snmpset = nav.Snmp.Snmp(netbox.ip, netbox.read_write, netbox.snmp_version)

    # Fetch the vlan currently on the port
    try:
        fromvlan = snmpget.get(query)
    except (nav.Snmp.NoSuchObjectError, nav.Snmp.TimeOutException), why:
        raise ChangePortVlanError(why)

    # If the vlan on the interface is the same as we try to set, do
    # nothing.
    if fromvlan == int(vlan):
        return fromvlan

    try:
        #snmpset.set(query, variable_type, vlan)
        pass
    except nav.Snmp.AgentError, why:
        raise ChangePortVlanError(why)

    # Ok, here comes the tricky part. On HP if we change vlan on a
    # port using dot1qPvid, the fromvlan will put the vlan in
    # trunkmode. To remedy this we use dot1qVlanStaticEgressPorts to
    # fetch and unset the tagged vlans.

    # The good thing about this is that it should work on any netbox
    # that supports Q-BRIDGE-MIB.

    if vendorid == 'hp':
        # Fetch dot1qVlanStaticEgressPorts
        dot1qvlanstaticegressports = '1.3.6.1.2.1.17.7.1.4.3.1.2.' + \
                                     str(fromvlan)
        try:
            hexports = snmpget.get(dot1qvlanstaticegressports)
        except nav.Snmp.NoSuchObjectError, why:
            raise ChangePortVlanError(why)

        # Create new octetstring and set it
        newhexports = compute_octet_string(hexports, interface.ifindex,
                                           'disable')

        try:
#            snmpset.set(dot1qvlanstaticegressports, 's', newhexports)
            pass
        except nav.Snmp.NoSuchObjectError, why:
            raise ChangePortVlanError(why)

    return fromvlan


def sendmail(fromaddr, toaddr, subject, msg):
    """
    Sends mail using mailprogram configured in arnold.conf

    NB: Expects all strings to be in utf-8 format.

    """

    # Get mailprogram from config-file
    config = get_config(CONFIGFILE)
    mailprogram = config.get('arnold', 'mailprogram')

    try:
        program = Popen(mailprogram, stdin=PIPE).stdin
    except OSError, error:
        LOGGER.error('Error opening mailprogram: %s', error.strerror)
        return

    # Define charset and set content-transfer-encoding to
    # quoted-printable
    charset = email.charset.Charset('utf-8')
    charset.header_encoding = email.charset.QP
    charset.body_encoding = email.charset.QP

    # Create message-object, fill it and set correct charset.
    message = email.message.Message()
    header = email.header.Header(subject, charset)
    message['To'] = toaddr
    message['From'] = fromaddr
    message['Subject'] = header

    message.set_charset(charset)
    message.set_payload(msg)

    # send mail
    program.communicate(message.as_string())


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

    # Try to locate nmblookup
    command, _ = Popen(['which', 'nmblookup'], stdout=PIPE).communicate()
    if not command:
        return ""

    result, _ = Popen([command.strip(), "-A", ip], stdout=PIPE).communicate()
    if not result:
        return ""

    # For each line in output, try to find name of computer.
    for line in result.split("\n\t"):
        if re.search("<00>", line):
            match_object = re.search("(\S+)\s+<00>", line)
            return match_object.group(1) or ""

    # If it times out or for some other reason doesn't match
    return ""


def check_non_block(ip):
    """Checks if the ip is in the nonblocklist."""
    nonblockdict = parse_nonblock_file(NONBLOCKFILE)

    # We have the result of the nonblock.cfg-file in the dict
    # nonblockdict. This dict contains 3 things:
    # 1 - Specific ip-addresses
    # 2 - Ip-ranges (129.241.xxx.xxx/xx)
    # 3 - Ip lists (129.241.xxx.xxx-xxx)

    # Specific ip-addresses
    if ip in nonblockdict['ip']:
        LOGGER.info('Computer in nonblock list, skipping')
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

    return str(bit)


@Memo
def parse_nonblock_file(filename):
    """Parse nonblocklist and make it ready for use."""

    nonblockdict = {'ip': {}, 'range': {}}

    # Open nonblocklist, parse it.
    try:
        handle = open(filename)
    except IOError, why:
        raise FileError(why)

    for line in handle.readlines():
        line = line.strip()

        # Skip comments
        if line.startswith('#'):
            continue

        if re.search('^\d+\.\d+\.\d+\.\d+$', line):
            # Single ip-address
            nonblockdict['ip'][line] = 1
        elif re.search('^\d+\.\d+\.\d+\.\d+\/\d+$', line):
            # Range
            nonblockdict['range'][line] = 1

    handle.close()

    return nonblockdict


@Memo
def get_config(configfile):
    """Get config from file"""
    config = ConfigParser.ConfigParser()
    config.read(configfile)
    return config


def init_logging(logfile):
    """Create logger for logging to file"""
    logs.set_log_levels()

    filehandler = logging.FileHandler(logfile)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] '
                                  '[%(name)s] %(message)s')
    filehandler.setFormatter(formatter)
    root = logging.getLogger('')
    root.addHandler(filehandler)


def is_inside_vlans(ip, vlans):
    """Check if ip is inside the vlans

    vlans: a string with comma-separated vlans.

    """
    vlans = [x.strip() for x in vlans.split(',')]

    # For each vlan, check if it is inside the prefix of the vlan.
    for vlan in vlans:
        if vlan.isdigit() and is_valid_ip(ip):
            if Prefix.objects.filter(vlan__vlan=vlan).extra(
                    where=['%s << netaddr'], params=[ip]):
                return True
    return False
