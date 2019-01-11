#
# Copyright (C) 2010 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Interface description convention parsers.

Each description parser takes two arguments: A sysname and an ifalias value.
If the ifalias value cannot be parsed by the given description parser, it will
return a None value.

"""

import re

NTNU_CORE_LAN_PATTERN = re.compile(r"""
    (?P<net_type>(core|lan)) ,
    (?P<org>[^,]+) ,
    (?P<ident> (?P<usage>[^\d,]+) (?P<n>\d+)? ) ( ,
    (?P<comment>[^,]*) ( ,
    (?P<vlan>\d+) )? )?
    """, re.X | re.I)

NTNU_LINK_PATTERN = re.compile(r"""
    (?P<net_type>link) ,
    (?P<to_router>[^,]+) ( ,
    (?P<comment>[^,]*) ( ,
    (?P<vlan>\d+) )? )?
    """, re.X | re.I)

NTNU_ELINK_PATTERN = re.compile(r"""
    (?P<net_type>elink) ,
    (?P<to_router>[^,]+) ,
    (?P<to_org>[^,]+) ( ,
    (?P<comment>[^,]*) ( ,
    (?P<vlan>\d+) )? )?
    """, re.X | re.I)


def parse_ntnu_convention(sysname, ifalias):
    """Parses router port description, using NTNU conventions.

    The conventions are documented at
    https://nav.uninett.no/wiki/subnetsandvlans

    """
    # Strip leading and trailing whitespace from each part individually
    string = ','.join([s.strip() for s in ifalias.split(',')])
    for pattern in (NTNU_CORE_LAN_PATTERN,
                    NTNU_LINK_PATTERN,
                    NTNU_ELINK_PATTERN):
        match = pattern.match(string)
        if match:
            break
    if not match:
        return None

    d = match.groupdict()
    if 'vlan' in d and d['vlan']:
        d['vlan'] = int(d['vlan'])
    if 'n' in d and d['n'] is not None:
        d['n'] = int(d['n'])

    if d['net_type'] in ('core', 'lan'):
        d['netident'] = ','.join(str(d[s])
                                 for s in ('org', 'ident', 'comment')
                                 if s in d and d[s])
    elif d['net_type'] in ('link', 'elink'):
        d['netident'] = "%s,%s" % (sysname, d['to_router'])
    return d


UNINETT_PATTERN = re.compile(r"""
    (?P<comment>[^,]+) ,
    (?P<netident>.*)
    """, re.X | re.I)


def parse_uninett_convention(_sysname, ifalias):
    """Parse router port description, using Uninett conventions."""
    # Strip leading and trailing whitespace from each part individually
    string = ','.join([s.strip() for s in ifalias.split(',')])
    match = UNINETT_PATTERN.match(string)
    if not match:
        return None

    return match.groupdict()
