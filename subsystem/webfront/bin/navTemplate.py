#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
This script enables external (i.e. non-Python) NAV systems to retrieve
and fill the contents of the MainTemplate Cheetah template.
"""

import sys, os
from nav import db, web
import nav.web.auth
from nav.db import navprofiles
from nav.web.templates.MainTemplate import MainTemplate

def main(argv):
    vars = {}

    for arg in argv:
        key, value = arg.split('=', 1)
        vars[key] = value

    if not vars.has_key('user'):
        vars['user'] = 0
        
    page = MainTemplate()
    for key, value in vars.items():
        # Make some special considerations for special variable names.  Anything
        if key == "user":
            conn = db.getConnection('navprofile', 'navprofile')

            try:
                id = int(value)
                account = navprofiles.Account(value)
                account.load()
            except ValueError, TypeError:
                account = navprofiles.Account.loadByLogin(value)
            nav.web.auth._find_user_preferences(account, None)
            page.user = account
        elif key == "content":
            func = lambda : vars['content']
            setattr(page, key, func)
        elif key == "path":
            path = [ ("Home", "/") ]
            list = value.split(':')
            if len(list) % 2 != 0:
                raise "element count of 'path' must be an even number"
            while len(list) > 0:
                text = list.pop(0)
                url = list.pop(0)
                path.append( (text, url) )
            page.path = path
        else:
            setattr(page, key, value)

    print page

def usage():
    """Print a usage summary to stderr"""
    summary = """Usage: navTemplate.py [--help] [variable=value] ...

Retrieves the NAV web MainTemplate and fills the variables of the
template according to the supplied arguments.

Special variables:
    user   - An account login or id; alters the contents of the
             returned page according to this users settings.

    path   - A list of name/url pairs that describe the path browsed
             to get to this page.  The input should be formatted as:
             "name:url:name:url ...".  The output will always prefix
             this list with the front page url.  The last url element
             may and should be omitted, as no link to the current page
             is required.

    content - The actual content of the page returned.
"""
    sys.stderr.write(summary)

if __name__ == '__main__':
    if '--help' in sys.argv:
        usage()
    else:
        main(sys.argv[1:])
else:
    raise "This module is runtime only, should not be imported"
