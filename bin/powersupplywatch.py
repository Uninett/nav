#! /usr/bin/env python
# encoding: utf-8
#
# Copyright (C) 2011 UNINETT AS
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
A script to poll the powersupply- and fan-states in netboxes, send alerts at
state-changes and store states in DB.
"""

from os.path import join
from datetime import datetime

import logging
import logging.handlers
import sys
from optparse import OptionParser

# import NAV libraries
import nav.config
import nav.daemon
import nav.logs
import nav.path
import nav.db
from nav.event import Event
from nav.Snmp.pysnmp_se import Snmp
from nav.models.manage import PowerSupplyOrFan

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

# Mapping between vendors and fan-states
VENDOR_FAN_STATES = {
                VENDOR_CISCO: {
                                CISCO_FAN_STATE_UNKNOWN: 'u',
                                CISCO_FAN_STATE_UP: 'y',
                                CISCO_FAN_STATE_DOWN: 'n',
                                CISCO_FAN_STATE_WARNING: 'w',
                                },
                VENDOR_HP: {
                                CISCO_FAN_STATE_WARNING: 'n',
                                HP_FAN_STATE_REMOVED: 'u',
                                HP_FAN_STATE_OFF: 'u',
                                HP_FAN_STATE_UNDERSPEED: 'w',
                                HP_FAN_STATE_OVERSPEED: 'w',
                                HP_FAN_STATE_OK: 'y',
                                HP_FAN_STATE_MAXSTATE: 'w',
                            },
                }

# Mapping between vendors and psu-states
VENDOR_PSU_STATES = {
                VENDOR_CISCO: {
                                CISCO_PSU_OFF_ENV_OTHER: 'n',
                                CISCO_PSU_ON: 'y',
                                CISCO_PSU_OFF_ADMIN: 'u',
                                CISCO_PSU_OFF_DENIED: 'n',
                                CISCO_PSU_OFF_ENV_POWER: 'n',
                                CISCO_PSU_OFF_ENV_TEMP: 'n',
                                CISCO_PSU_OFF_ENV_FAN: 'n',
                                CISCO_PSU_OFF_FAILED: 'n',
                                CISCO_PSU_ON_BUT_FAN_FAIL: 'w',
                                CISCO_PSU_OFF_COOLING: 'n',
                                CISCO_PSU_OFF_CONNECTOR_RATING: 'n',
                                CISCO_PSU_ON_BUT_INLINE_POWER_FAIL: 'n',
                                },
                VENDOR_HP: {
                                HP_PSU_PS_NOT_PRESENT: 'u',
                                HP_PSU_PS_NOT_PLUGGED: 'u',
                                HP_PSU_PS_POWERED: 'y',
                                HP_PSU_PS_FAILED: 'n',
                                HP_PSU_PS_PERM_FAILURE: 'n',
                                HP_PSU_PS_MAX: 'w',
                            },
                }

LOGFILE = join(nav.buildconf.localstatedir, "log/powersupplywatch.log")
# Loglevel (case-sensitive), may be:
# DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGLEVEL = 'DEBUG'

logger = None
dry_run = False
should_verify = False
snmp_handles = {}


def get_logger():
    """ Return a custom logger."""
    format_pattern = "[%(asctime)s] [%(levelname)s] %(message)s"
    filehandler = logging.FileHandler(LOGFILE)
    log_formatter = logging.Formatter(format_pattern)
    filehandler.setFormatter(log_formatter)
    log = logging.getLogger('powersupplywatch')
    log.addHandler(filehandler)
    log.setLevel(logging.getLevelName(LOGLEVEL))
    return log


def verify(msg):
    """Write message to stderr"""
    if should_verify:
        print >> sys.stderr, msg
    # Convenient to include a debug-statement too
    logger.debug(msg)


def post_event(psu_or_fan, status):
    """ Posts an event on the eventqueue."""
    source = "powersupplywatch"
    target = "eventEngine"
    eventtypeid = "moduleState"
    value = 100
    severity = 50
    device_id = None
    try:
        if psu_or_fan.device:
            device_id = psu_or_fan.device.id
    except Exception, ex:
        pass
    event = Event(source=source, target=target,
                            deviceid=device_id,
                            netboxid=psu_or_fan.netbox.id,
                            eventtypeid=eventtypeid,
                            value=value,
                            severity=severity)
    event['sysname'] = psu_or_fan.netbox.sysname
    if (PowerSupplyOrFan.STATE_DOWN == status
            or PowerSupplyOrFan.STATE_WARNING == status):
        event['alerttype'] = 'moduleDown'
    elif PowerSupplyOrFan.STATE_UP == status:
        event['alerttype'] = 'moduleUp'
    event['powername'] = psu_or_fan.name
    event['state'] = status
    verify('Posting event: %s' % event)
    try:
        event.post()
    except Exception, why:
        msg = 'post_event: exception = %s' % why
        verify(msg)
        logger.error(msg)
        return False
    return True


def read_hostsfile(filename):
    """ Read file with hostnames."""
    verify('Reading hosts from %s' % filename)
    hostnames = []
    hosts_file = None
    try:
        hosts_file = open(filename, 'r')
    except IOError as (errno, strerror):
        err_str = "I/O error ({0}): " + filename + " ({1})"
        print >> sys.stderr, err_str.format(errno, strerror)
        logger.error(err_str)
        sys.exit(2)
    for line in hosts_file:
        sysname = line.strip()
        if sysname and len(sysname) > 0:
            hostnames.append(sysname)
    hosts_file.close()
    verify('Hosts from %s: %s' % (filename, hostnames))
    return hostnames


def get_psus_and_fans(sysnames):
    """ Get netboxes from DB,- if hostnames are specified fetch only those;
    otherwise fetch all."""
    verify('Getting PSUs and FANs')
    psus_and_fans = None
    if sysnames and len(sysnames) > 0:
        psus_and_fans = PowerSupplyOrFan.objects.filter(
                            netbox__sysname__in=sysnames).order_by('netbox')
    else:
        psus_and_fans = PowerSupplyOrFan.objects.all().order_by('netbox')
    verify('Got %s PSUs and FANs' % len(psus_and_fans))
    return psus_and_fans


def get_snmp_handle(netbox):
    """Allocate an Snmp-handle for a given netbox"""
    global snmp_handles
    if not netbox.sysname in snmp_handles:
        verify('Allocate SNMP-handle for %s' % netbox.sysname)
        snmp_handles[netbox.sysname] = Snmp(netbox.ip, netbox.read_only,
                                                    netbox.snmp_version)
    return snmp_handles.get(netbox.sysname, None)


def is_fan(psu_or_fan):
    """Determine if this PowerSupplyOrFan-object is a FAN"""
    return (psu_or_fan.physical_class == 'fan')


def is_psu(psu_or_fan):
    """Determine if this PowerSupplyOrFan-object is a PSU"""
    return (psu_or_fan.physical_class == 'powerSupply')


def get_state(numerical_state, vendor_id, vendor_state_dict):
    """Get the state as a character, based on numerical state, vendor-id.
    and state-dictitonary"""
    if not numerical_state or not vendor_id:
        return 'u'
    vendor_states = vendor_state_dict.get(vendor_id, None)
    if not vendor_states:
        return 'u'
    return vendor_states.get(numerical_state, None)


def get_fan_state(fan_state, vendor_id):
    """Get the state as a character, based on numerical state and vendor-id."""
    return get_state(fan_state, vendor_id, VENDOR_FAN_STATES)


def get_psu_state(psu_state, vendor_id):
    """Get the state as a character, based on numerical state and vendor-id."""
    return get_state(psu_state, vendor_id, VENDOR_PSU_STATES)


def handle_status(psu_or_fan, status):
    """Check status-value,- post alerts and store state in DB if necessary"""
    if psu_or_fan.up != status:
        if psu_or_fan.up == 'y' or psu_or_fan.up == 'u':
            if status == 'w' or status == 'n':
                psu_or_fan.downsince = datetime.now()
                verify('Posting down-event...')
                if not dry_run:
                    post_event(psu_or_fan, status)
        elif psu_or_fan.up == 'n' or psu_or_fan.up == 'w':
            if status == 'y':
                psu_or_fan.downsince = None
                verify('Posting up-event...')
                if not dry_run:
                    post_event(psu_or_fan, status)
        psu_or_fan.up = status
        if not dry_run:
            verify('Save state to database.')
            psu_or_fan.save()
        else:
            verify('Dry run, not saving state.')


def check_psus_and_fans(to_check):
    """Check the state of the given PSUs and FANs, check against state in the
    DB, send alerts if necessary and store any changes."""
    for psu_or_fan in to_check:
        snmp_handle = get_snmp_handle(psu_or_fan.netbox)
        numerical_status = None
        verify('Polling %s: %s' % (psu_or_fan.netbox.sysname, psu_or_fan.name))
        if psu_or_fan.sensor_oid and snmp_handle:
            try:
                numerical_status = snmp_handle.get(psu_or_fan.sensor_oid)
            except Exception, ex:
                msg = '%s: %s, Exception = %s' % (psu_or_fan.netbox.sysname,
                    psu_or_fan.name, ex)
                verify(msg)
                logger.error(msg)
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
            verify('Stored state = %s; polled state = %s' %
                                    (psu_or_fan.up, status))
            handle_status(psu_or_fan, status)


def main():
    """Plain good old main..."""
    global logger
    global dry_run
    global should_verify

    logger = get_logger()

    parser = OptionParser()
    parser.add_option("-d", "--dry-run", action="store_true", dest="dryrun",
            help="Dry run.  No changes will be made and no events posted")
    parser.add_option("-f", "--file", dest="hostsfile",
            help="A file with hostnames to check. Must be one FQDN per line")
    parser.add_option("-n", "--netbox", dest="hostname",
            help="Check only this hostname.  Must be a FQDN")
    parser.add_option("-v", "--verify", action="store_true", dest="verify",
            help="Print (lots of) debug-information to stderr")
    opts, args = parser.parse_args()

    if opts.dryrun:
        dry_run = opts.dryrun

    if opts.verify:
        should_verify = opts.verify

    sysnames = []
    if opts.hostname:
        sysnames.append(opts.hostname.strip())
    if opts.hostsfile:
        sysnames.extend(read_hostsfile(opts.hostsfile))

    verify('Start checking PSUs and FANs')
    check_psus_and_fans(get_psus_and_fans(sysnames))
    sys.exit(0)


if __name__ == '__main__':
    main()
