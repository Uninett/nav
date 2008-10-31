#!/usr/bin/env python

"""This program performs various NAV database schema maintenance.

For the time being, all it does is verify that all NAV namespaces are
present in the database search path.  If they are not, the search path
is modified accordingly.
"""

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2 <http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt>"

import sys
import getopt

from nav.db import getConnection
from nav.config import readConfig

dbconf = readConfig('db.conf')

def verify_search_path():
    """Verify that all NAV schemas are in the database search_path."""
    wanted_schemas = [
        'manage',
        'profiles',
        'logger',
        'arnold',
        ]
    add_schemas = []

    cx = getConnection('default')
    c = cx.cursor()
    c.execute('SHOW search_path')

    search_path = c.fetchone()[0]
    schemas = [s.strip() for s in search_path.split(',')]

    for w in wanted_schemas:
        if w not in schemas:
            add_schemas.append(w)

    if add_schemas:
        dbname = dbconf['db_nav']
        
        schemas += add_schemas
        print "Adding namespaces to %s search_path: %s" % \
              (dbname, ", ".join(add_schemas))
        sql = "ALTER DATABASE %s SET search_PATH TO %s" % \
              (dbname, ", ".join(schemas))
        print sql
        c.execute(sql)
        cx.commit()
    else:
        print "NAV db search_path is ok."

def usage():
    """ Print a usage screen to stderr."""
    print >> sys.stderr, __doc__

def main(args):
    try:
        opts, args = getopt.getopt(args, '-h', ['--help'])
    except getopt.GetoptError, error:
        print >> sys.stderr, error
        usage()
        sys.exit(1)

    for opt,val in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)

    verify_search_path()
    
if __name__ == '__main__':
    main(sys.argv[1:])
