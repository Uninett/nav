#!/usr/bin/env python
import ConfigParser
import re
import sys
import os
from os.path import join

from nav import path
from nav.models.oid import SnmpOid

DIRS = ['routers', 'switches'] # What directories to parse

def main(configpath):
    """
    Locate all OID's defined in Crickets default files - more specifically from
    the router and switches subtree. Verify that they are present in the
    snmpoid table, and if not insert them there.
    """

    # Find oids assuming these directories are leaf nodes
    oids = []
    c = re.compile('\s*OID\s+(\w+)\s+(\S+)')
    for dir in DIRS:
        path = join(configpath, dir)
        for file in os.listdir(path):
            file = join(path, file)
            if file.endswith('~'):
                continue
            try:
                f = open(file, 'r')
            except Exception, e:
                print e
                continue

            for line in f.readlines():
                m = c.search(line)
                if m:
                    oidkey, snmpoid = m.groups()
                    #print "%s: OID %s %s" %(file, oidkey, snmpoid)
                    oids.append((oidkey, snmpoid))

    print "Found %s oids in Crickets config files" % len(oids)

    # Check if oids are present in snmpoid table, insert if not.
    inserted = updated = 0
    for oidkey, snmpoid in oids:
        try:
            s = SnmpOid.objects.get(snmp_oid=snmpoid)
            if oidkey != s.oid_key:
                print "Updating %s: %s => %s" % (snmpoid, s.oid_key, oidkey)
                s.oid_key = oidkey
                s.save()
                updated += 1
            else:
                print "In database: %s:%s" % (oidkey, snmpoid)
        except SnmpOid.DoesNotExist:
            print "Inserting %s:%s" % (oidkey, snmpoid)
            s = SnmpOid(oid_key=oidkey, snmp_oid=snmpoid, oid_source='Cricket',
                        get_next=False)
            s.save()
            inserted += 1

    # Delete the dreaded temperature oids
    for oidkey in ['tempOutlet','tempInlet','tempState']:
        try:
            s = SnmpOid.objects.get(oid_key=oidkey, oid_source='Cricket')
            s.delete()
            print "Deleted %s" %oidkey
        except:
            pass
        
    print "Inserted: %s" % inserted
    print "Updated: %s" % updated


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
        print "Could not find %s: %s" % (configfile, e)
        sys.exit(1)

    # Locate path to cricket config file in the mcc config file
    try:
        configfile = config.get('mcc', 'configfile')
    except Exception, e:
        print "Could not find Cricket config file: %s" % e
        sys.exit(1)

    # Find cricket-config directory
    try: 
        f = open(configfile, 'r')
    except Exception, e:
        print "Could not open Cricket config file: %s" % e
        sys.exit(1)

    c = re.compile('^\s*\\$gConfigRoot\s*=\s*\"(.*)\"', re.I)
    configpath = False
    for line in f.readlines():
        m = c.search(line)
        if m:
            configpath = m.groups()[0]
            print "Setting cricket config path to %s" % configpath
            break

    if not configpath:
        print "Could not find cricket's configpath"
        sys.exit(1)

    main(configpath)
