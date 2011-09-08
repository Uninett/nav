#! /usr/bin/env python
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
A script to poll the power-supply states in netboxes.
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
from nav.Snmp.errors import UnsupportedSnmpVersionError
from nav.Snmp.errors import TimeOutException
from nav.models.manage import Netbox
from nav.models.manage import PowerSupplyState

LOGFILE = join(nav.buildconf.localstatedir, "log/powersupplywatch.log")
# Loglevel (case-sensitive), may be:
# DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGLEVEL = 'INFO'

logger = None
should_verify = False


class SNMPHandler(object):
    """
    A generic class for handling power-supplies in a netbox.
    """
    pwr_supplies_oid = '.1.3.6.1.4.1.11.2.14.11.1.2.6.1.4'
    pwr_status_oid = '.1.3.6.1.4.1.11.2.14.11.1.2.6.1.4'
    pwr_name_oid = '.1.3.6.1.4.1.11.2.14.11.1.2.6.1.7'

    def __init__(self, netbox):
        """ A plain and old constructor."""
        self.netbox = netbox
        self.snmp_handle = None

    def get_netbox(self):
        """ Return the current netbox."""
        return self.netbox

    def get_snmp_handle(self):
        """ Allocate a snmp-handle for the netbox."""
        if not self.snmp_handle:
            self.snmp_handle = Snmp(self.netbox.ip,
                                    self.netbox.read_only,
                                    self.netbox.snmp_version)
        return self.snmp_handle

    def get_power_supplies(self):
        """ Walk a netbox and try to find all possible power-supplies."""
        pwr_supplies = []
        try:
            try:
                pwr_supplies = self.get_snmp_handle().bulkwalk(
                                            self.pwr_supplies_oid)
            except UnsupportedSnmpVersionError, unsupported_snmp_ver_ex:
                pwr_supplies = self.get_snmp_handle().walk(
                                                        self.pwr_supplies_oid)
        except TimeOutException, timed_out_ex:
            logger.info('%s timed out' % self.netbox.sysname)
        return pwr_supplies

    def _get_legal_index(self, index):
        """ Check that the index is valid. """
        if isinstance(index, int):
            index = str(index)
        if not (isinstance(index, str) or isinstance(index, unicode)):
            raise TypeError('Illegal value for power-index')
        if not index.isdigit():
            raise TypeError('Illegal value for power-index')
        return index

    def is_power_supply_ok(self, pwr_index):
        """ Poll status from power-sensor in a netbox."""
        status = -1
        pwr_index = self._get_legal_index(pwr_index)
        status = self.get_snmp_handle().get(self.pwr_status_oid + "." +
                                            pwr_index)
        if isinstance(status, str) or isinstance(status, unicode):
            if status.isdigit():
                status = int(status)
        return (status == 4 or status == 5)

    def get_power_name(self, pwr_index):
        """ Get power name."""
        pwr_index = self._get_legal_index(pwr_index)
        return self.get_snmp_handle().get(self.pwr_name_oid + "." + pwr_index)


class HP(SNMPHandler):
    """
    A specialised class for handling power-supplies in HP netbox.
    """

    def __init__(self, netbox):
        super(HP, self).__init__(netbox)


class Cisco(SNMPHandler):
    """
    A specialised class for handling power-supplies in Cisco netbox.
    """
    pwr_supplies_oid = '.1.3.6.1.4.1.9.9.13.1.5.1.2'
    pwr_status_oid = '.1.3.6.1.4.1.9.9.13.1.5.1.3'
    pwr_name_oid = '.1.3.6.1.4.1.9.9.13.1.5.1.2'

    def __init__(self, netbox):
        """ Nothing more than a constructor."""
        super(Cisco, self).__init__(netbox)

    def is_power_supply_ok(self, pwr_index):
        """ Poll status from power-sensor in a Cisco netbox."""
        status = -1
        pwr_index = self._get_legal_index(pwr_index)
        status = self.get_snmp_handle().get(self.pwr_status_oid + "." +
                                                pwr_index)
        if isinstance(status, str) or isinstance(status, unicode):
            if status.isdigit():
                status = int(status)
        return (status == 1)

# ISO vendor-identities
VENDOR_CISCO = 9
VENDOR_HP = 11


class SNMPFactory(object):
    """
    Factory for makeing snmp-handles depending on vendor-identities.
    """

    @classmethod
    def get_instance(cls, netbox):
        """
        Get a snmp-handle to a given netbox.  Currently handle only
        HP- and Cisco-netboxes.
        """
        vendor_id = None
        if netbox.type:
            vendor_id = netbox.type.get_enterprise_id()
        if vendor_id and vendor_id == VENDOR_CISCO:
            return Cisco(netbox)
        if vendor_id and vendor_id == VENDOR_HP:
            return HP(netbox)
        return SNMPHandler(netbox)


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
    """ Print message to stderr if verify-option is given."""
    if should_verify:
        print >> sys.stderr, msg


def get_netboxes(sysnames):
    """ Get netboxes from DB,- if hostnames are specified fetch only those;
    otherwise fetch all."""
    if sysnames and len(sysnames) > 0:
        return Netbox.objects.filter(sysname__in=sysnames)
    else:
        return Netbox.objects.all()


def post_event(netbox, pwr_name, status):
    """ Posts an event on the eventqueue."""
    source = "powersupplywatch"
    target = "eventEngine"
    eventtypeid = "moduleState"
    value = 100
    severity = 50
    event = Event(source=source, target=target,
                            netboxid=netbox.id,
                            eventtypeid=eventtypeid,
                            value=value,
                            severity=severity)
    event['sysname'] = netbox.sysname
    if PowerSupplyState.STATE_DOWN == status:
        event['alerttype'] = 'moduleDown'
    elif PowerSupplyState.STATE_UP == status:
        event['alerttype'] = 'moduleUp'
    event['powername'] = pwr_name
    event['state'] = status
    try:
        event.post()
    except Exception, why:
        msg = 'post_event: exception = %s' % why
        verify(msg)
        logger.error(msg)
        return False
    return True


def get_power_state(netbox, pwr_name):
    """
    Get the power-state from DB for this netbox and power-supply.
    """
    return PowerSupplyState.objects.filter(netbox=netbox).filter(
                                                        name=pwr_name)


def store_state_down(netbox, pwr_name):
    """ Store a record in DB with down-state."""
    new_state = PowerSupplyState(netbox=netbox,
                                        name=pwr_name,
                                        state=PowerSupplyState.STATE_DOWN)
    if post_event(netbox, pwr_name, PowerSupplyState.STATE_DOWN):
        verify("Event posted successfully")
        new_state.event_posted = datetime.now()
    else:
        verify("Post event failed")
        new_state.event_posted = None
    new_state.save()
    verify("New record saved successfully.")


def handle_power_state(netbox, stored_state, pwr_name, pwr_up):
    """
    Handle states,- create or delete states, and post events as necessary.
    """
    if not stored_state and not pwr_up:
        msg = ('%s: %s has gone down.  Store state in DB' %
                    (netbox.sysname, pwr_name))
        verify(msg)
        logger.warn(msg)
        store_state_down(netbox, pwr_name)
    if stored_state:
        if PowerSupplyState.STATE_DOWN == stored_state.state and not pwr_up:
            verify("State is down and polled state is down")
            if not stored_state.event_posted:
                verify("Event not posted for this")
                if post_event(netbox, pwr_name, PowerSupplyState.STATE_DOWN):
                    verify("Event posted successfully")
                    stored_state.event_posted = datetime.now()
                else:
                    verify("Post event failed")
                    stored_state.event_posted = None
                stored_state.save()
        if PowerSupplyState.STATE_DOWN == stored_state.state and pwr_up:
            msg = '%s: %s has come up' % (netbox.sysname, pwr_name)
            verify(msg)
            logger.info(msg)
            if post_event(netbox, pwr_name, PowerSupplyState.STATE_UP):
                verify("Event posted successfully")
                stored_state.delete()
                verify("Record deleted successfully")
        if PowerSupplyState.STATE_UP == stored_state.state and pwr_up:
            # This should not happen...
            stored_state.delete()
        if PowerSupplyState.STATE_UP == stored_state.state and not pwr_up:
            # nor this...
            stored_state.delete()
            store_state_down(netbox, pwr_name)


def handle_too_many_states(power_states, netbox, pwr_name):
    """
    Function that take actions when we discover more than one
    state-record in DB.
    """
    # The safest is probably to delete all states. Anyone?
    msg = ('%s: %s %d records in DB; Will delete all' %
                (netbox.sysname, pwr_name, len(power_states)))
    verify(msg)
    logger.error(msg)
    delete_power_states(power_states)


def delete_power_states(power_states):
    """ Delete the given power-supply states from DB."""
    if power_states:
        for state in power_states:
            state.delete()


def read_hostsfile(filename):
    """ Read file with hostnames."""
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
        line.strip()
        if line:
            hostnames.append(line.strip())
    hosts_file.close()
    return hostnames


def main():
    """ Plain old main..."""
    global logger
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

    if opts.verify:
        should_verify = opts.verify

    sysnames = []
    if opts.hostname:
        sysnames.append(opts.hostname.strip())
    if opts.hostsfile:
        sysnames.extend(read_hostsfile(opts.hostsfile))

    dup_powers = {}
    for netbox in get_netboxes(sysnames):
        handle = SNMPFactory.get_instance(netbox)
        msg = '%s: Collecting power-supplies' % netbox.sysname
        verify(msg)
        logger.debug(msg)
        pwr_supplies = handle.get_power_supplies()
        msg = ("%s: Number of power-supplies %d" %
                (netbox.sysname, len(pwr_supplies)))
        verify(msg)
        logger.debug(msg)
        if len(pwr_supplies) > 1:
            dup_powers[handle] = pwr_supplies

    for handle, pwr_supplies in dup_powers.items():
        power_supply_index = 1
        for pwr in pwr_supplies:
            pwr_name = handle.get_power_name(str(power_supply_index))
            pwr_up = handle.is_power_supply_ok(str(power_supply_index))
            stored_states = get_power_state(handle.get_netbox(), pwr_name)
            stored_state = None
            if len(stored_states) > 0:
                if len(stored_states) == 1:
                    stored_state = stored_states[0]
                elif len(stored_states) > 1:
                    handle_too_many_states(stored_states, handle.get_netbox(),
                                                pwr_name)
            pwr_status = PowerSupplyState.STATE_DOWN
            if pwr_up:
                pwr_status = PowerSupplyState.STATE_UP
            msg = '%s: %s is %s' % (handle.get_netbox().sysname, pwr_name,
                                        (pwr_status))
            verify(msg)
            logger.debug(msg)
            if not opts.dryrun:
                handle_power_state(handle.get_netbox(), stored_state,
                                    pwr_name, pwr_up)
            power_supply_index += 1
    sys.exit(0)

if __name__ == '__main__':
    main()
