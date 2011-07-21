#!/usr/bin/env python
#
# Copyright (C) 2008, 2011 UNINETT AS
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
"""Extract Launchpad bug report references from input.

This program scans its input, assumed to be Mercurial change log
messages, extracts what seems to be Launchpad bug ids, retrieves the
titles of these bug ids from Launchpad and prints a set of details
suitable for inclusion NAV's CHANGES file.

To use, simply pipe the output of your desired hg log command through
this program.  Example:

  hg log -l50 | buglog.py

If you aren't sure that all bug report references can be found in the
commit log messages' summary line, add the -v option to hg log.
"""

import urllib2
import re
import sys

BUG_URL = 'https://launchpad.net/bugs/%d/+text'
COMMITLOG_PATTERN = re.compile(r'((bug)?fix for|fix(es)?|closes?) '
                               r'+(lp)? *# *(?P<bug_id>[0-9]{6,})', re.I)

def get_bug_details(bug_id):
    """Retrieve text detail of a launchpad bug report.

    bug_id -- The Launchpad bug id.

    Returns a list of strings detailing the bug.
    """
    url = BUG_URL % bug_id
    info = urllib2.urlopen(url)
    return info.readlines()

def get_bug_title(bug_id):
    """Retrieve the title of a launchpad bug report."""
    for line in get_bug_details(bug_id):
        if line.startswith('title:'):
            title = line.split(':', 1)[1]
            return title.strip()

def bugfix_format(bug_id):
    """Return bugfix details formatted for NAV's CHANGES file."""
    title = get_bug_title(bug_id)
    return "  * LP#%d (%s)" % (bug_id, title)

def filter_log(file):
    """Filter hg log output.

    Returns a generator.  For each line of the input file that looks
    like a reference to a Launchpad bug report, yields a tuple
    consisting of the line itself and a regexp Match object.  The
    match object will contain a named group called 'bug_id', which
    contains the bug report id number.

      file -- An open file or other file-like/iterable object.
    """
    for line in file:
        match = COMMITLOG_PATTERN.search(line)
        if match:
            yield (line, match)

def filter_bugids(matches):
    for line, match in matches:
        yield int(match.group('bug_id'))

def main(args):
    if sys.stdin.isatty():
        print __doc__,
        sys.exit(0)

    bug_ids = set()
    for bug_id in filter_bugids(filter_log(sys.stdin)):
        bug_ids.add(bug_id)

    for bug_id in sorted(bug_ids):
        print bugfix_format(bug_id)

if __name__ == '__main__':
    main(sys.argv[1:])
