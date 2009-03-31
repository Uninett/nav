#!/usr/bin/env python
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details. 
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Mercurial extensions for NAV development.

This extension adds two new commands to hg:

  bug-commit  Commits a fix for a given Launchpad bug report.
  qbug        Creates a new MQ patch for a given Launchpad bug report.
"""
import urllib2

from mercurial.i18n import _
from mercurial import commands
from hgext import mq

BUG_URL = 'https://launchpad.net/bugs/%d/+text'
BUG_TEMPLATE = 'Fix for LP#%s (%s)'
def fetch_bug_details(bug_id):
    url = BUG_URL % bug_id
    info = [l for l in urllib2.urlopen(url) if l.startswith('title:')]
    title = info[0].split(':', 1)[1]
    return title.strip()

def bug_commit(ui, repo, bug_no, *pats, **opts):
    """commit a fix for a Launchpad registered bug.

    Performs a regular commit, but given a Launchpad bug number will
    pre-fill the log message with details of the bug report from
    Launchpad.
    """
    details = fetch_bug_details(int(bug_no))
    opts['message'] = BUG_TEMPLATE % (bug_no, details) + "\n"
    opts['force_editor'] = True
    return commands.commit(ui, repo, *pats, **opts)

def qbug(ui, repo, bug_no, *args, **opts):
    """start a new patch to fix a specific Launchpad bug report.

    Does the same as the qnew command, but fetches bug report details
    from Launchpad and initializes the patch description with it.
    """
    details = fetch_bug_details(int(bug_no))
    patch_name = "bug-%s.patch" % bug_no

    opts['message'] = BUG_TEMPLATE % (bug_no, details)
    result = mq.new(ui, repo, patch_name, *args, **opts)
    ui.write("Starting new patch for LP#%s (%s)\n" % (bug_no, details))
    return result


cmdtable = {
    # cmd name     function call
    "bug-commit": (bug_commit,
                   # see mercurial/fancyopts.py for all of the command
                   # flag options.
                   commands.walkopts + commands.commitopts + 
                   commands.commitopts2,
                   "hg bug-commit [OPTION] BUGNUMBER [FILE]..."),
    "qbug":
        (qbug,
         [('e', 'edit', None, _('edit commit message')),
          ('f', 'force', None, _('import uncommitted changes into patch')),
          ('g', 'git', None, _('use git extended diff format')),
          ] + commands.walkopts + commands.commitopts + mq.headeropts,
         'hg qbug [-e] [-f] BUGNUMBER [FILE]...'),
}
