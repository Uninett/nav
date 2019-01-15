#!/usr/bin/env python
#
# Copyright (C) 2011, 2012, 2014, 2017 Uninett AS
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
A program to poll the states of known power supplies and fan units in netboxes,
storing their last known state in the NAV db and post NAV events on state
changes.
"""

import logging
logging.raiseExceptions = False

import sys
from datetime import datetime
import argparse

from nav.bootstrap import bootstrap_django
bootstrap_django(__file__)

# import NAV libraries
from nav.event import Event
from nav.Snmp import Snmp
from nav.models.manage import PowerSupplyOrFan, Device
from nav.logs import init_generic_logging


VENDOR_CISCO = 9
VENDOR_HP = 11

# All the states and their constants are copies of values in
# CSICO-ENTITY-FRU-CONTROL-MIB,- and POWERSUPPLY-MIB and FAN-MIB
# from HP
#
# Possible FAN states for Cisco
CISCO_FAN_STATE_UNKNOWN = 1
CISCO_FAN_STATE_UP = 2
CISCO_FAN_STATE_DOWN = 3
CISCO_FAN_STATE_WARNING = 4

# Possible FAN states for HP
HP_FAN_STATE_FAILED = 0
HP_FAN_STATE_REMOVED = 1
HP_FAN_STATE_OFF = 2
HP_FAN_STATE_UNDERSPEED = 3
HP_FAN_STATE_OVERSPEED = 4
HP_FAN_STATE_OK = 5
HP_FAN_STATE_MAXSTATE = 6

# Possible PSU states for Cisco
CISCO_PSU_OFF_ENV_OTHER = 1
CISCO_PSU_ON = 2
CISCO_PSU_OFF_ADMIN = 3
CISCO_PSU_OFF_DENIED = 4
CISCO_PSU_OFF_ENV_POWER = 5
CISCO_PSU_OFF_ENV_TEMP = 6
CISCO_PSU_OFF_ENV_FAN = 7
CISCO_PSU_OFF_FAILED = 8
CISCO_PSU_ON_BUT_FAN_FAIL = 9
CISCO_PSU_OFF_COOLING = 10
CISCO_PSU_OFF_CONNECTOR_RATING = 11
CISCO_PSU_ON_BUT_INLINE_POWER_FAIL = 12

# Possible PSU states for HP
HP_PSU_PS_NOT_PRESENT = 1
HP_PSU_PS_NOT_PLUGGED = 2
HP_PSU_PS_POWERED = 3
HP_PSU_PS_FAILED = 4
HP_PSU_PS_PERM_FAILURE = 5
HP_PSU_PS_MAX = 5

# Shorthand for database states
STATE_UNKNOWN = PowerSupplyOrFan.STATE_UNKNOWN
STATE_UP = PowerSupplyOrFan.STATE_UP
STATE_DOWN = PowerSupplyOrFan.STATE_DOWN
STATE_WARNING = PowerSupplyOrFan.STATE_WARNING

STATE_MAP = dict(PowerSupplyOrFan.STATE_CHOICES)

# Mapping between vendors and fan-states
VENDOR_FAN_STATES = {
    VENDOR_CISCO: {
        CISCO_FAN_STATE_UNKNOWN: STATE_UNKNOWN,
        CISCO_FAN_STATE_UP: STATE_UP,
        CISCO_FAN_STATE_DOWN: STATE_DOWN,
        CISCO_FAN_STATE_WARNING: STATE_WARNING,
    },
    VENDOR_HP: {
        HP_FAN_STATE_FAILED: STATE_DOWN,
        HP_FAN_STATE_REMOVED: STATE_UNKNOWN,
        HP_FAN_STATE_OFF: STATE_UNKNOWN,
        HP_FAN_STATE_UNDERSPEED: STATE_WARNING,
        HP_FAN_STATE_OVERSPEED: STATE_WARNING,
        HP_FAN_STATE_OK: STATE_UP,
        HP_FAN_STATE_MAXSTATE: STATE_WARNING,
    },
}

# Mapping between vendors and psu-states
VENDOR_PSU_STATES = {
    VENDOR_CISCO: {
        CISCO_PSU_OFF_ENV_OTHER: STATE_DOWN,
        CISCO_PSU_ON: STATE_UP,
        CISCO_PSU_OFF_ADMIN: STATE_UNKNOWN,
        CISCO_PSU_OFF_DENIED: STATE_DOWN,
        CISCO_PSU_OFF_ENV_POWER: STATE_DOWN,
        CISCO_PSU_OFF_ENV_TEMP: STATE_DOWN,
        CISCO_PSU_OFF_ENV_FAN: STATE_DOWN,
        CISCO_PSU_OFF_FAILED: STATE_DOWN,
        CISCO_PSU_ON_BUT_FAN_FAIL: STATE_WARNING,
        CISCO_PSU_OFF_COOLING: STATE_DOWN,
        CISCO_PSU_OFF_CONNECTOR_RATING: STATE_DOWN,
        CISCO_PSU_ON_BUT_INLINE_POWER_FAIL: STATE_DOWN,
    },
    VENDOR_HP: {
        HP_PSU_PS_NOT_PRESENT: STATE_UNKNOWN,
        HP_PSU_PS_NOT_PLUGGED: STATE_DOWN,
        HP_PSU_PS_POWERED: STATE_UP,
        HP_PSU_PS_FAILED: STATE_DOWN,
        HP_PSU_PS_PERM_FAILURE: STATE_DOWN,
        HP_PSU_PS_MAX: STATE_WARNING,
    },
}

LOGFILE = "powersupplywatch.log"
LOGGER = logging.getLogger('nav.powersupplywatch')


def main():
    """Main program"""
    init_generic_logging(
        logfile=LOGFILE,
        stderr=True,
        read_config=False,
        stderr_level=logging.ERROR if sys.stderr.isatty() else logging.CRITICAL,
    )

    opts = parse_args()

    if opts.verify:
        LOGGER.info("-v option used, setting log level to DEBUG")
        stderr = logging.getLogger('')
        stderr.setLevel(logging.DEBUG)
        LOGGER.setLevel(logging.DEBUG)

    sysnames = []
    if opts.hostname:
        sysnames.append(opts.hostname.strip())
    if opts.hostsfile:
        sysnames.extend(read_hostsfile(opts.hostsfile))

    LOGGER.debug('Start checking PSUs and FANs')
    check_psus_and_fans(get_psus_and_fans(sysnames),
                        dryrun=opts.dryrun)


def parse_args():
    """Parses the command line arguments"""
    parser = argparse.ArgumentParser(
        description="Powersupply and fan status monitor for NAV"
    )
    parser.add_argument(
        "-d", "--dry-run", action="store_true", dest="dryrun",
        help="Dry run.  No changes will be made and no events posted")
    parser.add_argument(
        "-f", "--file", dest="hostsfile",
        help="A file with hostnames to check. Must be one FQDN per line")
    parser.add_argument(
        "-n", "--netbox", dest="hostname",
        help="Check only this hostname.  Must be a FQDN")
    parser.add_argument(
        "-v", "--verify", action="store_true",
        help="Print (lots of) debug-information to stderr")
    return parser.parse_args()


def read_hostsfile(filename):
    """ Read file with hostnames."""
    LOGGER.debug('Reading hosts from %s', filename)
    hostnames = []
    try:
        hosts_file = open(filename, 'r')
    except IOError as error:
        LOGGER.error("I/O error (%s): %s (%s)",
                     error.errno, filename, error.strerror)
        sys.exit(2)
    for line in hosts_file:
        sysname = line.strip()
        if sysname and len(sysname) > 0:
            hostnames.append(sysname)
    hosts_file.close()
    LOGGER.debug('Hosts from %s: %s', filename, hostnames)
    return hostnames


def get_psus_and_fans(sysnames):
    """
    Loads netboxes from DB.

    :param sysnames: A list of sysnames to fetch. If empty, all netboxes are
                     fetched.
    :type sysnames: list
    :return: A QuerySet of PowerSupplyOrFan objects.

    """
    LOGGER.debug('Getting PSUs and FANs')
    if sysnames and len(sysnames) > 0:
        psus_and_fans = PowerSupplyOrFan.objects.filter(
            netbox__sysname__in=sysnames).order_by('netbox')
    else:
        psus_and_fans = PowerSupplyOrFan.objects.all().order_by('netbox')
    LOGGER.debug('Got %s PSUs and FANs', len(psus_and_fans))
    return psus_and_fans


def check_psus_and_fans(to_check, dryrun=False):
    """
    Checks the state of the given PSUs and FANs, compares against state in the
    DB, sends alerts if necessary, and stores any changes.
    """
    for psu_or_fan in to_check:
        snmp_handle = get_snmp_handle(psu_or_fan.netbox)
        numerical_status = None
        LOGGER.debug('Polling %s: %s',
                     psu_or_fan.netbox.sysname, psu_or_fan.name)
        if psu_or_fan.sensor_oid and snmp_handle:
            try:
                numerical_status = snmp_handle.get(psu_or_fan.sensor_oid)
            except Exception as ex:
                LOGGER.error('%s: %s, Exception = %s',
                             psu_or_fan.netbox.sysname, psu_or_fan.name, ex)
                # Don't jump out, continue to next psu or fan
                continue
        vendor_id = None
        if psu_or_fan.netbox.type:
            vendor_id = psu_or_fan.netbox.type.get_enterprise_id()
        status = None
        if is_fan(psu_or_fan):
            status = get_fan_state(numerical_status, vendor_id)
        elif is_psu(psu_or_fan):
            status = get_psu_state(numerical_status, vendor_id)
        if status:
            LOGGER.debug('Stored state = %s; polled state = %s',
                         STATE_MAP[psu_or_fan.up], STATE_MAP[status])
            handle_status(psu_or_fan, status, dryrun)


def get_snmp_handle(netbox):
    """Allocates an Snmp-handle for a given netbox"""
    LOGGER.debug('Allocate SNMP-handle for %s', netbox.sysname)
    return Snmp(netbox.ip, netbox.read_only, netbox.snmp_version)


def handle_status(psu_or_fan, status, dry_run=False):
    """Checks status-value, posts alerts and stores state in DB if necessary"""
    _handle_internal_state(psu_or_fan, status, dry_run)
    _handle_alert_state(psu_or_fan, status, dry_run)


def _handle_internal_state(psu_or_fan, status, dry_run=False):
    if psu_or_fan.up == status:
        # state is unchanged, no need to save
        return

    if psu_or_fan.up in (STATE_UP, STATE_UNKNOWN) and status in (STATE_WARNING,
                                                                 STATE_DOWN):
        psu_or_fan.downsince = datetime.now()
    elif psu_or_fan.up in (STATE_DOWN, STATE_WARNING) and status == STATE_UP:
        psu_or_fan.downsince = None

    psu_or_fan.up = status

    if not dry_run:
        LOGGER.debug('Saving state to database.')
        psu_or_fan.save()
    else:
        LOGGER.debug('Dry run, not saving state.')


def _handle_alert_state(psu_or_fan, status, dry_run=False):
    has_alerts = bool(psu_or_fan.get_unresolved_alerts().count())
    should_post = (
        status == STATE_UP and has_alerts
    ) or (
        status in (STATE_DOWN, STATE_WARNING) and not has_alerts
    )

    if should_post and not dry_run:
        LOGGER.debug('Posting event (%s)...', STATE_MAP[status])
        post_event(psu_or_fan, status)


def post_event(psu_or_fan, status):
    """ Posts an event on the eventqueue."""
    source = "powersupplywatch"
    target = "eventEngine"
    eventtypeid = "psuState" if is_psu(psu_or_fan) else "fanState"
    value = 100
    severity = 50

    try:
        device_id = psu_or_fan.device.id
    except (Device.DoesNotExist, AttributeError):
        device_id = None

    event = Event(source=source, target=target,
                  deviceid=device_id,
                  netboxid=psu_or_fan.netbox.id,
                  subid=psu_or_fan.id,
                  eventtypeid=eventtypeid,
                  state='x',
                  value=value,
                  severity=severity)
    event['sysname'] = psu_or_fan.netbox.sysname
    if status in (PowerSupplyOrFan.STATE_DOWN,
                  PowerSupplyOrFan.STATE_WARNING):
        event['alerttype'] = 'psuNotOK' if is_psu(psu_or_fan) else 'fanNotOK'
        event.state = 's'
    elif status == PowerSupplyOrFan.STATE_UP:
        event['alerttype'] = 'psuOK' if is_psu(psu_or_fan) else 'fanOK'
        event.state = 'e'
    event['unitname'] = psu_or_fan.name
    event['state'] = status
    LOGGER.debug('Posting event: %s', event)
    try:
        event.post()
    except Exception as why:
        LOGGER.error('post_event: exception = %s', why)
        return False
    return True


def is_fan(psu_or_fan):
    """Determine if this PowerSupplyOrFan-object is a FAN"""
    return psu_or_fan.physical_class == 'fan'


def is_psu(psu_or_fan):
    """Determine if this PowerSupplyOrFan-object is a PSU"""
    return psu_or_fan.physical_class == 'powerSupply'


def get_fan_state(fan_state, vendor_id):
    """Get the state as a character, based on numerical state and vendor-id."""
    return get_state(fan_state, vendor_id, VENDOR_FAN_STATES)


def get_psu_state(psu_state, vendor_id):
    """Get the state as a character, based on numerical state and vendor-id."""
    return get_state(psu_state, vendor_id, VENDOR_PSU_STATES)


def get_state(numerical_state, vendor_id, vendor_state_dict):
    """Get the state as a character, based on numerical state, vendor-id.
    and state-dictitonary"""
    if not numerical_state or not vendor_id:
        return STATE_UNKNOWN
    vendor_states = vendor_state_dict.get(vendor_id, None)
    if not vendor_states:
        return STATE_UNKNOWN
    return vendor_states.get(numerical_state, None)


if __name__ == '__main__':
    main()
