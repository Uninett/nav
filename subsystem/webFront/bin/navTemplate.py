#!/usr/bin/env python
"""
$Id$

This file is part of the NAV project.

This script enables external (i.e. non-Python) NAV systems to retrieve
and fill the contents of the MainTemplate Cheetah template.

Copyright (c) 2003 by NTNU, ITEA
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""

import sys, os
from nav import db, web
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
            navprofiles.setCursorMethod(conn.cursor)

            try:
                id = int(value)
                account = navprofiles.Account(value)
                account.load()
            except ValueError, TypeError:
                account = navprofiles.Account.loadByLogin(value)
            try:
                web.auth._find_user_preferences(account, None)
            except:
                pass
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
