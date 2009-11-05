#!/usr/bin/env python
import ConfigParser
import re
import sys
import os
from os.path import join

from nav.db import getConnection
from nav import path

def main(configpath):
    """
    Locate all OID's defined in Crickets default files - more specifically from
    the router and switches subtree. Verify that they are present in the
    snmpoid table, and if not insert them there.
    """

    conn = getConnection('default')
    cur = conn.cursor()

    # What directories to parse
    dirs = ['routers', 'switches']

    # Find oids assuming these directories are leaf nodes
    oids = []
    c = re.compile('\s*OID\s+(\w+)\s+(\S+)')
    for dir in dirs:
        path = join(configpath, dir)
        for file in os.listdir(path):
            file = join(path, file)
            try:
                f = open(file, 'r')
            except Exception, e:
                print e
                continue

            for line in f.readlines():
                m = c.search(line)
                if m:
                    oidkey, snmpoid = m.groups()
                    print "%s: OID %s %s" %(file, oidkey, snmpoid)
                    oids.append((oidkey, snmpoid))

    # Check if oids are present in snmpoid table, insert if not.
    for oidkey, snmpoid in oids:
        q = "SELECT oidkey FROM snmpoid WHERE snmpoid = %s"
        cur.execute(q, (snmpoid,))

        if cur.rowcount <= 0:
            print "Inserting %s:%s" %(oidkey, snmpoid)
            q = """
                INSERT INTO snmpoid 
                (oidkey, snmpoid, oidsource, getnext)
                VALUES
                (%s, %s, 'Cricket', 'f')
                """
            cur.execute(q, (oidkey, snmpoid))
        elif oidkey != cur.fetchone()[0]:
            print "Updating %s:%s" %(oidkey, snmpoid)
            q = """
                UPDATE snmpoid
                SET oidkey = %s, oidsource = 'Cricket', getnext = 'f'
                WHERE snmpoid = %s
                """
            cur.execute(q, (oidkey, snmpoid))
        else:
            print "%s:%s already in database" %(oidkey, snmpoid)

    conn.commit()


if __name__ == '__main__':
    # Locate the mcc config file
    mcc_configfile = "mcc.conf"
    if not os.path.exists(mcc_configfile):
        # Search for configfile in navs config directory
        mcc_configfile = join(path.sysconfdir, mcc_configfile)

    # Read the mcc config file
    config = ConfigParser.ConfigParser()
    try:
        config.readfp(open(mcc_configfile, 'r'))
    except Exception, e:
        print "Could not find %s: %s" %(configfile, e)
        sys.exit()

    # Locate path to cricket config file in the mcc config file
    try:
        configfile = config.get('mcc','configfile')
    except Exception, e:
        print "Could not find Cricket config file: %s" %e
        sys.exit()

    # Find cricket-config directory
    try: 
        f = open(configfile, 'r')
    except Exception, e:
        print "Could not open Cricket config file: %s" %e
        sys.exit()

    c = re.compile('gConfigRoot\s*=\s*\"(.*)\"',re.I)
    configpath = False
    for line in f.readlines():
        m = c.search(line)
        if m:
            configpath = m.groups()[0]
            print "Setting cricket config path to %s" %configpath
            break

    if not configpath:
        print "Could not find crickets configpath"
        sys.exit()

    main(configpath)
