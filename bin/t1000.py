#!/usr/bin/env python
#
# Copyright 2008 Norwegian University of Science and Technology
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
t1000 finds blocked computers that have moved and blocks them again.

Usage:
sudo -u navcron ./t1000.py

t1000 is meant to be run as a cronjob. It checks the database for any
detained ports. If it finds any, it checks if the mac-address is active on
some other port and detains that port.

"""

import sys
import logging
import getpass
from datetime import datetime, timedelta

import nav.buildconf
from nav.util import is_valid_ip

from nav.arnold import (find_computer_info, disable, quarantine,
                        NoDatabaseInformationError, GeneralException,
                        init_logging)
from nav.models.arnold import Identity, DetentionProfile
from nav.models.manage import Interface, Prefix

CONFIGFILE = nav.buildconf.sysconfdir + "/arnold/arnold.conf"

LOGGER = logging.getLogger('t1000')


def main():
    """Main controller"""
    init_logging(nav.buildconf.localstatedir + "/log/arnold/t1000.log")
    LOGGER.info("Starting t1000")

    # Fetch all mac-addresses that we have detained, check if they are
    # active somewhere else. As NAV collects arp and cam data periodically,
    # we need to give one hour slack to ensure data is correct.

    identities = Identity.objects.filter(
        last_changed__lte=datetime.now() - timedelta(hours=1),
        status__in=['disabled', 'quarantined'])

    if len(identities) <= 0:
        LOGGER.info("No detained ports in database where lastchanged > 1 "
                    "hour.")
        sys.exit(0)

    for identity in identities:
        LOGGER.info("%s is %s, checking for activity"
                    % (identity.mac, identity.status))
        try:
            caminfo = find_computer_info(identity.mac)
        except NoDatabaseInformationError, error:
            LOGGER.info(error)
            continue

        # If this mac-address is active behind another port, block it.
        if caminfo['endtime'] > datetime.now():
            pursue(identity, caminfo)
        else:
            LOGGER.info("Mac not active.")


def pursue(identity, caminfo):
    """Try to detain this identity if applicable"""
    LOGGER.info("Found active mac")
    identity.ip = caminfo['ip']

    # Check if this reason is a part of any detention profile. If it is we
    # need to fetch the vlans from that profile and see if the new ip is on
    # one of those vlans or have to be skipped.

    profile = is_detained_by_profile(identity)
    if profile and not should_detain(identity, profile):
        return

    try:
        identity.interface = Interface.objects.get(
            netbox__sysname=caminfo['sysname'],
            ifindex=caminfo['ifindex'])
    except Interface.DoesNotExist:
        LOGGER.error('Could not find interface to detain')
        return
    identity.autoenablestep = find_autoenable_step(identity)

    LOGGER.debug("Setting autoenablestep to %s" % identity.autoenablestep)

    detain(identity)


def is_detained_by_profile(identity):
    """Check that this identity is detained with a detention profile"""
    try:
        return DetentionProfile.objects.get(
            justification=identity.justification)
    except DetentionProfile.DoesNotExist:
        return None


def find_autoenable_step(identity):
    """Find and set autoenable and autoenablestep"""
    event = identity.event_set.filter(
        autoenablestep__isnull=False,
        justification=identity.justification).order_by('-event_time')[0]

    profile = is_detained_by_profile(identity)
    autoenablestep = event.autoenablestep

    # If detainment is incremental, increase autoenablestep
    if profile and profile.incremental:
        autoenablestep *= 2

    return autoenablestep


def should_detain(identity, profile):
    """Verify that this identity is inside the defined vlans for the profile"""
    LOGGER.info('%s is %s by a profile' % (identity.mac, identity.status))
    if profile.active_on_vlans:
        if not is_inside_vlans(identity.ip, profile.active_on_vlans):
            LOGGER.info("Ip not in activeonvlans")
            return False
        else:
            LOGGER.debug("Ip in activeonvlans")
    else:
        LOGGER.debug("Profile has no activeonvlans set")

    return True


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


def detain(identity):
    """Detain based on identity info"""
    username = getpass.getuser()
    comment = "Detained automatically when switching ports"

    try:
        if identity.status == 'disabled':
            LOGGER.debug("Trying to disable %s" % identity.mac)
            disable(identity, identity.justification, username, comment,
                    identity.keep_closed, identity.autoenablestep)

        elif identity.status == 'quarantined':
            LOGGER.debug("Trying to quarantine %s with vlan %s"
                         % (identity.mac, identity.tovlan))
            quarantine(identity, identity.tovlan, identity.justification,
                       username, comment, identity.keep_closed,
                       identity.autoenablestep)
    except GeneralException, error:
        LOGGER.error(error)


if __name__ == '__main__':
    main()
