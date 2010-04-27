#!/usr/bin/env python

import sys
import getopt
from nav.db import getConnection

def main():
    print "Deleting tuples regarding Cricket rrd-files from rrd database."
    
    conn = getConnection('default')
    c = conn.cursor()
    
    query = """
    DELETE FROM rrd_file WHERE subsystem = 'cricket'
    """
    c.execute(query)
    
    print "\nNow run makecricketconfig.pl to fill the rrd database."
    

if __name__ == '__main__':
    
    help = """Usage: Use the -x flag to delete from the database.
This script will remove all entries in the rrd database regarding Cricket.
After this is done you must run makecricketconfig.pl to fill the database again."""
    
    if len(sys.argv) <= 1:
        print help
        sys.exit()
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hx")
    except getopt.GetoptError, err:
        print help
        sys.exit()
    
    for o, a in opts:
        if o == '-x': 
            main()
        else:
            print help
