#!/usr/bin/env python
# -*- testargs: --list -*-
#
# Copyright 2017 (C) Uninett AS
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
Use this to run automatic detentions based on detention profiles

Usage: start_arnold [options] id
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
import argparse
from os.path import join

from nav.bootstrap import bootstrap_django
from nav.config import find_config_file

bootstrap_django(__file__)

from nav.logs import init_generic_logging
import nav.arnold
from nav.arnold import (
    find_computer_info,
    is_inside_vlans,
    quarantine,
    disable,
    GeneralException,
)
from nav.models.arnold import DetentionProfile, Identity
from nav.models.manage import Prefix

LOG_FILE = "arnold/start_arnold.log"
_logger = logging.getLogger('nav.start_arnold')


def main(args=None):
    """Main controller"""

    if args is None:
        args = parse_command_options()

    init_generic_logging(logfile=LOG_FILE, stderr=False, read_config=True)

    if args.listblocktypes:
        print_detention_profiles()
        return

    _logger.info('Starting automatic detentions based on %s', args.profile.name)
    addresses = get_addresses_to_detain(args)

    detentions = []  # List of successfully blocked ip-addresses
    for address, comment in addresses:
        try:
            detentions.append(detain(address, args.profile, comment))
        except GeneralException as error:
            _logger.error(error)
            continue

    if args.profile.mailfile and detentions:
        report_detentions(args.profile, detentions)


def print_detention_profiles():
    """Print all existing detention profiles"""
    output_format = "%-5s %-5s %s"
    print(output_format % ("ID", "Act", "Title"))
    for profile in DetentionProfile.objects.all():
        print(output_format % (profile.id, profile.active, profile.name))


def get_addresses_to_detain(options):
    """Get and parse addresses to detain either from file or from stdin"""
    if options.filename:
        try:
            handle = open(options.filename, 'r')
        except IOError as error:
            _logger.error(error)
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
        match = re.match(r"([^ ]+)(\s+.+)?", line)
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
    _logger.debug("Trying to detain %s", address)

    username = getpass.getuser()
    candidate = find_computer_info(address)

    if profile.active_on_vlans and not is_inside_vlans(
        candidate.ip, profile.active_on_vlans
    ):
        _logger.error(
            "%s is not inside defined vlanrange for this predefined detention",
            address,
        )
        return

    duration = find_duration(candidate, profile)

    if profile.detention_type == 'disable':
        disable(candidate, profile.justification, username, comment, duration)
    else:
        quarantine(
            candidate,
            profile.quarantine_vlan,
            profile.justification,
            username,
            comment,
            duration,
        )

    return address


def find_duration(candidate, profile):
    """Find duration for this candidate based on profile

    If this candidate has been detained before on this interface and the
    profile has defined exponential detainment, increase the detainment for
    this candidate.

    :param nav.arnold.Candidate candidate: The candidate to find duration for
    :param DetentionProfile profile: The profile used for detention
    """
    autoenablestep = profile.duration

    if profile.incremental == 'y':
        try:
            identity = Identity.objects.get(
                mac=candidate.mac, interface=candidate.interface
            )
        except Identity.DoesNotExist:
            pass
        else:
            event = identity.events.filter(
                justification=profile.justification, autoenablestep__isnull=False
            ).order_by('-event_time')

            if event:
                autoenablestep = event[0].autoenablestep * 2

    _logger.debug("Setting duration to %s days", autoenablestep)
    return autoenablestep


def report_detentions(profile, detentions):
    """For all ip's that are detained, group by contactinfo and send mail"""
    _logger.debug("Trying to report detentions")

    emails = find_contact_addresses(detentions)

    try:
        mailfile = find_config_file(join("arnold", "mailtemplates", profile.mailfile))
        message_template = open(mailfile).read()
    except IOError as error:
        _logger.error(error)
        return

    for email, iplist in emails.items():
        _logger.info("Sending mail to %s", email)

        fromaddr = 'noreply'
        toaddr = email
        reason = profile.name
        subject = "Computers detained because of %s" % profile.justification

        msg = message_template
        msg = re.sub(r'\$reason', reason, msg)
        msg = re.sub(r'\$list', "\n".join([" ".join(x) for x in iplist]), msg)

        try:
            nav.arnold.sendmail(fromaddr, toaddr, subject, msg)
        except Exception as error:  # noqa: BLE001
            _logger.error(error)
            continue


def find_contact_addresses(detentions):
    """Find contact addresses for each ip in detentions list"""
    emails = {}
    for ip in detentions:
        organization = get_organization(ip)
        if not organization:
            _logger.info("No organization found for %s", ip)
            continue

        if not organization.contact:
            _logger.info("No contact info for %s", organization)
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
        where=['%s << netaddr'], params=[ip]
    )
    if prefixes:
        prefix = min(prefixes, key=methodcaller('get_prefix_length'))
        return prefix.vlan.organization
    else:
        return None


def parse_command_options():
    """Parse options from commandline"""
    parser = argparse.ArgumentParser(
        description="Accepts a list of IP addresses to block",
        epilog="Address list can either be piped in to stdin, or use the -f "
        "option to specify a file containing a list of addresses",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-i",
        "--blockid",
        dest="profile",
        type=valid_profile,
        help="id of blocktype to use",
    )
    parser.add_argument("-f", "--filename", help="filename with IPs to detain")
    group.add_argument(
        "--list",
        action="store_true",
        dest="listblocktypes",
        help="list predefined detentions/blocktypes",
    )

    return parser.parse_args()


def valid_profile(detention_profile_id):
    """Verifies that a detention profile id is valid"""
    try:
        profile = DetentionProfile.objects.get(pk=detention_profile_id)
    except DetentionProfile.DoesNotExist:
        raise argparse.ArgumentTypeError(
            "No such profile id: %s" % detention_profile_id
        )

    if profile.active == 'n':
        raise argparse.ArgumentTypeError(
            "Detention profile is inactive: %s" % profile.name
        )

    return profile


if __name__ == '__main__':
    main()
