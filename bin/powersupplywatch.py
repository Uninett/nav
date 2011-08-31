#!/usr/bin/env python
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
from os.path import join
from datetime import datetime

import time
import logging
import logging.handlers
import os
import os.path
import pwd
import sys
from optparse import OptionParser

# import NAV libraries
import nav.config
import nav.daemon
import nav.logs
import nav.path
import nav.db
from nav.Snmp.pysnmp_se import Snmp
from nav.Snmp.errors import *

from nav.models.manage import Netbox
from nav.models.manage import PowerSupplyState

# These have to be imported after the envrionment is setup
from django.db import DatabaseError, connection
from nav.alertengine.base import check_alerts

LOGFILE = join(nav.buildconf.localstatedir, "log/powersupplywatch.log")
# Loglevel (case-sensitive), may be:
# DEBUG, INFO, WARNING, ERROR, CRITICAL
LOGLEVEL = 'INFO'

logger = None

class SNMPHandler(object):
    """
    A generic class for handling power-supplies in a netbox.
    """
    pwr_supplies_oid = '.1.3.6.1.4.1.11.2.14.11.1.2.6.1.4'
    pwr_status_oid = '.1.3.6.1.4.1.11.2.14.11.1.2.6.1.4'
    pwr_name_oid = '.1.3.6.1.4.1.11.2.14.11.1.2.6.1.7'

    def __init__(self, netbox):
        self.netbox = netbox
        self.snmp_handle = None

    def get_netbox(self):
        return self.netbox

    def get_snmp_handle(self):
        if not self.snmp_handle:
            self.snmp_handle = Snmp(self.netbox.ip,
                                    self.netbox.read_only,
                                    self.netbox.snmp_version)
        return self.snmp_handle

    def get_power_supplies(self):
        pwr_supplies = []
        try:
            try:
                pwr_supplies = self.get_snmp_handle().bulkwalk(
                                            self.pwr_supplies_oid)
            except UnsupportedSnmpVersionError, e:
                pwr_supplies = self.get_snmp_handle().walk(self.pwr_supplies_oid)
        except TimeOutException, e:
            pass
        return pwr_supplies

    def _get_legal_index(self, index):
        if isinstance(index, int):
            index = str(index)
        if not (isinstance(index, str) or isinstance(index, unicode)):
            raise TypeError('Illegal value for power-index')
        if not index.isdigit():
            raise TypeError('Illegal value for power-index')
        return index
    
    def is_power_supply_ok(self, pwr_index):
        status = -1
        pwr_index = self._get_legal_index(pwr_index)
        status = self.get_snmp_handle().get(self.pwr_status_oid + "." +
                                            pwr_index)
        if isinstance(status, str) or isinstance(status, unicode):
            if status.isdigit():
                status = int(status)
        return (status == 4 or status == 5)

    def get_power_name(self, pwr_index):
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
        super(Cisco, self).__init__(netbox)

    def is_power_supply_ok(self, pwr_index):
        status = -1
        pwr_index = self._get_legal_index(pwr_index)
        status = self.get_snmp_handle().get(self.pwr_status_oid + "." +
                                                pwr_index)
        if isinstance(status, str) or isinstance(status, unicode):
            if status.isdigit():
                status = int(status)
        return (status == 1)
    
VENDOR_CISCO = 9
VENDOR_HP = 11

class SNMPFactory(object):
    @classmethod
    def get_instance(cls, netbox):
        vendor_id = None
        if netbox.type:
            vendor_id = netbox.type.get_enterprise_id()
        if vendor_id and vendor_id == VENDOR_CISCO:
            return Cisco(netbox)
        if vendor_id and vendor_id == VENDOR_HP:
            return HP(netbox)
        return SNMPHandler(netbox)


def get_logger():
    """ Return a custom logger """
    format = "[%(asctime)s] [%(levelname)s] %(message)s"
    filehandler = logging.FileHandler(LOGFILE)
    formatter = logging.Formatter(format)
    filehandler.setFormatter(formatter)
    logger = logging.getLogger('powersupplywatch')
    logger.addHandler(filehandler)
    logger.setLevel(logging.getLevelName(LOGLEVEL))
    return logger

def get_netboxes(sysnames):
    if len(sysnames) > 0:
        return Netbox.objects.filter(sysname__in=sysnames)
    else:
        return Netbox.objects.all()

def post_event(netbox, pwr_name, state):
    """Posts an event on the eventqueue"""

    source = "powersupplywatch"
    target = "eventEngine"
    eventtypeid = "info"
    value = 100
    severity = 50
    event = nav.event.Event(source=source, target=target,
                            netboxid=netbox.id,
                            eventtypeid=eventtypeid,
                            state=pwr_name + " " + state
                            value=value,
                            severity=severity)
    event['sysname'] = netbox.sysname
    event['alerttype'] = 'powerSupplyWarning'
    try:
        event.post()
    except Exception, why:
        print >> sys.stderr, "%s" % why
        return False
    return True

def main():
    global logger
    #logger = get_logger()

    parser = OptionParser()
    parser.add_option("-d", "--dry-run", action="store_true", dest="dryrun",
            help="Dry run.  No changes will be made and no events posted")
    parser.add_option("-f", "--file", dest="hostsfile",
            help="A file with hostnames to check. Must be one FQDN per line")
    parser.add_option("-n", "--netbox", dest="hostname",
            help="Check only this hostname.  Must be a FQDN")
    opts, args = parser.parse_args()
    
    sysnames = []
    if opts.hostname:
        sysnames.append(opts.hostname.strip())
    if opts.hostsfile:
        f = None
        try:
            f = open(opts.hostsfile, 'r')
        except IOError as (errno, strerror):
            err_str = "I/O error ({0}): " + opts.hostsfile + " ({1})"
            print >> sys.stderr, err_str.format(errno, strerror)
            sys.exit(2)
        for line in f:
            line.strip()
            if line:
                sysnames.append(line.strip())
        f.close()

    dup_powers = {}
    for netbox in get_netboxes(sysnames):
        handle = SNMPFactory.get_instance(netbox)
        pwr_supplies = handle.get_power_supplies()
        if len(pwr_supplies) > 1:
            dup_powers[handle] = pwr_supplies
    
    for handle, pwr_supplies in dup_powers.items():
        print >> sys.stdout, '%s:' % handle.get_netbox().sysname
        i = 1;
        for pwr in pwr_supplies:
            pwr_name = handle.get_power_name(str(i))
            up = handle.is_power_supply_ok(str(i))
            stored_state = None
            stored_states = PowerSupplyState.objects.filter(
                        netbox=handle.get_netbox()).filter(power_name=pwr_name)
            if len(stored_states) > 0:
                if len(stored_states) == 1:
                    stored_state = stored_states[0]
                else:
                    print >> sys.stderr, "Something is very wrong"
                    sys.exit(3)
            if not stored_state and not up:
                new_state = PowerSupplyState(netbox=handle.get_netbox(),
                                            power_name=pwr_name, state='down')
                if post_event(handle.get_netbox(), pwr_name, 'down'):
                    new_state.event_posted = datetime.now()
                else:
                    new_state.event_posted = None
                new_state.save()
            if stored_state:
                if 'down' == stored_state.state and not up:
                    if not stored_state.event_posted:
                        if post_event(handle.get_netbox(), pwr_name, 'down'):
                            stored_state.event_posted = datetime.now()
                        else:
                            stored_state.event_posted = None
                    stored_state.save()
                if 'down' == stored_state.state and up:
                    if post_event(handle.get_netbox(), pwr_name, 'up'):
                        stored_state.delete()
            i += 1
        
    sys.exit(0)

if __name__ == '__main__':
    main()
