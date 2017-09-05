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
"""Extract Launchpad bug and GitHub issue titles from input.

This program scans its input, assumed to be Git change log messages, extracts
what seems to be Launchpad bug IDs and GitHub issue IDs, retrieves the titles
of these bug IDs and prints a set of details suitable for inclusion NAV's
CHANGES file.

To use, simply pipe the output of your desired git log command through this
program. Example:

  hg log -l50 | buglog.py

If you aren't sure that all bug report references can be found in the
commit log messages' summary line, add the -v option to hg log.
"""

from __future__ import print_function

try:
    from urllib.request import Request, urlopen
except ImportError:
    from urllib2 import Request, urlopen
import re
import sys
import textwrap
import json

BUG_URL = 'https://launchpad.net/bugs/{bug_id}/+text'
ISSUE_URL = 'https://github.com/UNINETT/nav/issues/{bug_id}'
COMMITLOG_PATTERN = re.compile(r'((bug)?fix for|fix(es|ed)?|close(s|d)?):? '
                               r'+(?P<lp>lp)? *# *(?P<bug_id>[0-9]+)', re.I)


class Bug(object):
    prefix = ""

    def __init__(self, number):
        self.number = number
        self._title = None

    def __str__(self):
        """Return bugfix details formatted for NAV's CHANGES file."""
        lead_in = "  * {}#{:<7} (".format(self.prefix, self.number)
        indent = " " * len(lead_in)
        line = "{}{})".format(lead_in, self.title)

        return '\n'.join(
            textwrap.wrap(line, width=80, subsequent_indent=indent))

    def __hash__(self):
        return hash(self.prefix + str(self.number))

    def __cmp__(self, other):
        return cmp(self.number, other.number)


class LaunchpadBug(Bug):
    prefix = "LP"

    @property
    def title(self):
        """Retrieve the title of a Launchpad bug report."""
        if not self._title:
            for line in self._get_details():
                if line.startswith('title:'):
                    title = line.split(':', 1)[1]
                    self._title = title.strip()
        return self._title

    def _get_details(self):
        """Returns a list of strings detailing the bug"""
        url = BUG_URL.format(bug_id=self.number)
        info = urlopen(url)
        return info.readlines()


class GithubIssue(Bug):
    prefix = "GH"

    @property
    def title(self):
        details = self._get_details()
        return details.get('title', 'N/A')

    def _get_details(self):
        """Returns a JSON structure detailing the bug"""
        url = ISSUE_URL.format(bug_id=self.number)
        req = Request(url, headers={
            'Accept': 'application/json'
        })
        data = urlopen(req).read()
        return json.loads(data)


def filter_log(file):
    """Filter VCS log output.

    Returns a generator. For each line of the input file that looks like a
    reference to a Launchpad bug report or GitHub issue, yields a tuple
    consisting of the line itself and a regexp Match object. The match object
    will contain a named group called 'bug_id', which contains the bug report
    id number.

      file -- An open file or other file-like/iterable object.

    """
    for line in file:
        match = COMMITLOG_PATTERN.search(line)
        if match:
            yield (line, match)


def filter_bugs(matches):
    for line, match in matches:
        bug_id = int(match.group('bug_id'))
        if match.group('lp'):
            yield LaunchpadBug(bug_id)
        else:
            yield GithubIssue(bug_id)


def main(args):
    if sys.stdin.isatty():
        print(__doc__, end=' ')
        sys.exit(0)

    bugs = set()
    for bug in filter_bugs(filter_log(sys.stdin)):
        bugs.add(bug)

    for bug in sorted(bugs):
        print(bug)

if __name__ == '__main__':
    main(sys.argv[1:])
