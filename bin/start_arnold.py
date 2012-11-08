#!/usr/bin/env python
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
Use this to run automatic detentions based on detention profiles

Usage: start_arnold.py [options] id
Pipe in ip-addresses to block or use the -f option to specify file

Options:
  -h, --help   show this help message and exit
  -i BLOCKID   id of blocktype to use
  -f FILENAME  filename with id's to detain
  --list       list predefined detentions

Always uses the last interface the ip was seen on whether the ip is active
there or not.

"""

import getpass
import logging
import re
import sys
from operator import methodcaller
from optparse import OptionParser
from os.path import join

import nav.buildconf
from nav.arnold import (init_logging, find_computer_info, is_inside_vlans,
                        quarantine, disable, GeneralException)
from nav.models.arnold import DetentionProfile, Identity
from nav.models.manage import Prefix

LOGGER = logging.getLogger('start_arnold')


def main(options):
    """Main controller"""

    init_logging(nav.buildconf.localstatedir + "/log/arnold/start_arnold.log")

    if options.listblocktypes:
        print_detention_profiles()
        return

    profile = verify_options(options)
    if not profile:
        return

    LOGGER.info('Starting automatic detentions based on %s' % profile.name)
    addresses = get_addresses_to_detain(options)

    detentions = []  # List of successfully blocked ip-addresses
    for address, comment in addresses:
        try:
            detentions.append(detain(address, profile, comment))
        except GeneralException, error:
            LOGGER.error(error)
            continue

    if profile.mailfile and detentions:
        report_detentions(profile, detentions)


def print_detention_profiles():
    """Print all existing detention profiles"""
    output_format = "%-5s %-5s %s"
    print output_format % ("ID", "Act", "Title")
    for profile in DetentionProfile.objects.all():
        print output_format % (profile.id, profile.active, profile.name)


def verify_options(options):
    """Verify that the options passed in are sane"""

    if not options.blockid:
        LOGGER.info("No profile id given")
        return

    try:
        profile = DetentionProfile.objects.get(pk=options.blockid)
    except DetentionProfile.DoesNotExist:
        LOGGER.debug(
            "No such profile id: %s" % options.blockid)
        return

    if profile.active == 'n':
        LOGGER.info("Detention profile is inactive: %s" % options.blockid)
        return

    return profile


def get_addresses_to_detain(options):
    """Get and parse addresses to detain either from file or from stdin"""
    if options.filename:
        try:
            handle = open(options.filename, 'r')
        except IOError, error:
            LOGGER.error(error)
            return
        return parse_input(handle.readlines())
    else:
        return parse_input(sys.stdin.readlines())


def parse_input(lines):
    """Use the first word in the line as an address to detain

    The rest of the line is used as comment

    """
    addresses = []

    for line in lines:
        if re.match('#', line):
            continue

        # "chomp"
        if line and line[-1] == '\n':
            line = line[:-1]

        # Grab first part of line, use that as an address to block. Grab the
        # rest and use it as comment.
        match = re.match("([^ ]+)(\s+.+)?", line)
        if match:
            address, comment = match.groups()
            if comment:
                comment.strip()
            else:
                comment = ""
            addresses.append((address, comment))

    return addresses


def detain(address, profile, comment=''):
    """Detain address with the given profile"""
    LOGGER.debug("Trying to detain %s" % address)

    username = getpass.getuser()
    candidate = find_computer_info(address)

    if profile.active_on_vlans and not is_inside_vlans(
            candidate.ip, profile.active_on_vlans):
        LOGGER.error(
            "%s is not inside defined vlanrange for this predefined "
            "detention" % address)
        return

    duration = find_duration(candidate, profile)

    if profile.detention_type == 'disable':
        disable(candidate, profile.justification, username, comment, duration)
    else:
        quarantine(candidate, profile.quarantine_vlan, profile.justification,
                   username, comment, duration)

    return address


def find_duration(candidate, profile):
    """Find duration for this candidate based on profile

    If this candidate has been detained before on this interface and the
    profile has defined exponential detainment, increase the detainment for
    this candidate.

    """
    autoenablestep = profile.duration
    try:
        identity = Identity.objects.get(mac=candidate.mac,
                                        interface=candidate.interface)
    except Identity.DoesNotExist:
        pass
    else:
        event = identity.event_set.filter(
            justification=profile.justification,
            autoenablestep__isnull=False).order_by('-event_time')

        if event:
            autoenablestep = event[0].autoenablestep
            if profile.incremental == 'y':
                autoenablestep *= 2

    LOGGER.debug("Setting duration to %s days" % autoenablestep)
    return autoenablestep


def report_detentions(profile, detentions):
    """For all ip's that are detained, group by contactinfo and send mail"""
    LOGGER.debug("Trying to report detentions")

    emails = find_contact_addresses(detentions)

    try:
        mailfile = join(nav.buildconf.sysconfdir, "/arnold/mailtemplates/",
                        profile.mailfile)
        message_template = open(mailfile).read()
    except IOError, error:
        LOGGER.error(error)
        return

    for email, iplist in emails.items():
        LOGGER.info("Sending mail to %s" % email)

        fromaddr = 'noreply'
        toaddr = email
        reason = profile.name
        subject = "Computers detained because of %s" % profile.justification

        msg = message_template
        msg = re.sub(r'\$reason', reason, msg)
        msg = re.sub(r'\$list', "\n".join([" ".join(x) for x in iplist]), msg)

        try:
            nav.arnold.sendmail(fromaddr, toaddr, subject, msg)
        except Exception, error:
            LOGGER.error(error)
            continue


def find_contact_addresses(detentions):
    """Find contact addresses for each ip in detentions list"""
    emails = {}
    for ip in detentions:
        organization = get_organization(ip)
        if not organization:
            LOGGER.info("No organization found for %s" % ip)
            continue

        if not organization.contact:
            LOGGER.info("No contact info for %s" % organization)
            continue

        dns = nav.arnold.get_host_name(ip)
        netbios = nav.arnold.get_netbios(ip)
        splitaddresses = [x.strip() for x in organization.contact.split(',')]

        for email in splitaddresses:
            if email in emails:
                emails[email].append([ip, dns, netbios])
            else:
                emails[email] = [[ip, dns, netbios]]

    return emails


def get_organization(ip):
    """Find the organization this ip belongs to"""
    prefixes = Prefix.objects.filter(vlan__net_type='lan').extra(
        where=['%s << netaddr'], params=[ip])
    if prefixes:
        prefix = min(prefixes, key=methodcaller('get_prefix_length'))
        return prefix.vlan.organization
    else:
        return None


def parse_command_options():
    """Parse options from commandline"""
    usage = """usage: %prog [options] id
Pipe in ip-addresses to block or use the -f option to specify file"""
    parser = OptionParser(usage)
    parser.add_option("-i", dest="blockid", help="id of blocktype to use")
    parser.add_option("-f", dest="filename",
                      help="filename with id's to detain")
    parser.add_option("--list", action="store_true", dest="listblocktypes",
                      help="list predefined detentions")

    return parser.parse_args()


if __name__ == '__main__':

    OPTS, ARGS = parse_command_options()
    main(OPTS)
