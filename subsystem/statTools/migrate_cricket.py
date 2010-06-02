#!/usr/bin/env python
"""
Script to migrate from pre 3.6 versions of NAV to 3.6.
"""
import sys
import re
import getpass
import getopt
from os.path import join, abspath

import nav.path
from nav.rrd.rrdtool_utils import edit_datasource
from nav.db import getConnection

def main(configfile):

#===============================================================================
# Step 1:
# Remove all tuples regarding Cricket in the rrd-database as they are
# possibly erroneous
#===============================================================================
    print "Clearing rrd database"
    clear_rrd_database()
    print "Done"

#===============================================================================
# Step 2:
# Search default files for targettypes which contain temperature oids and
# remove the datasources from the rrd-files
#===============================================================================
    configdir = get_configroot(configfile)
    if not configdir:
        print "Could not get cricket-config path from %s" % configfile
        sys.exit(1)
    datadir = get_datadir(configdir)
    if not datadir:
        print "Could not find datadir in %s" % (join(configdir, 'Defaults'))
        sys.exit(1)

    dirs = ['routers', 'switches']

    print "\nSearching for rrd files with temperature oids"
    for dir in dirs:
        workingdir = join(configdir, dir)
        targetdatadir = join(datadir, dir)
        filename = join(workingdir, 'Defaults')
        try:
            f = file(filename)
        except Exception, e:
            print "Could not open %s: %s" % (filename, e)
            print "See %s for help" % HELPURL
            continue
        
        tempoids = find_tempoids(f.readlines())
        
        if tempoids:
            remove_tempoids(tempoids, targetdatadir)
        else:
            print "%s: No tempoids found" %dir

        
def find_tempoids(lines):
    """
    Find tempoids, return dict with sysname and list of datasources which 
    contain tempoids.
    """
    sysnamepattern = re.compile('targettype\s+(.*)$', re.IGNORECASE)
    dspattern = re.compile('ds\s+=\s+"?(.+)"?')
    temppattern = re.compile('^temp')
    
    ttfound = False
    sysname = ""
    tempoids = {}
    for line in lines:
        ttmatch = sysnamepattern.search(line)
        dsmatch = dspattern.search(line)
        
        if ttmatch:
            sysname = ttmatch.groups()[0].strip()
            #print sysname
            ttfound = True
            
        if dsmatch and ttfound:
            ttfound = False
            datasources = dsmatch.groups()[0].split(',')
            #print datasources
            
            # Check for temp oid
            for i, ds in enumerate(datasources):
                #print i, ds
                m = temppattern.search(ds)
                if m:
                    if tempoids.has_key(sysname):
                        tempoids[sysname].append(i)
                    else:
                        tempoids[sysname] = [i]

    return tempoids
            
def remove_tempoids(tempoids, dir):
    """
    Remove temperature oids from the files in tempoids.
    Dir is path to files.
    """
    for sysname, dslist in tempoids.items():
        rrdfile = join(dir, sysname + ".rrd")
        # Reverse the list as we have to delete the last datasource first.
        for ds in reversed(dslist):
            dsname = 'ds' + str(ds)
            print "Removing %s from %s" % (dsname, rrdfile)
            try:
                edit_datasource(rrdfile, dsname, 'remove')
            except Exception, e:
                print e
                continue 
    
def get_configroot(configfile):
    """ Get path for configroot from cricket-conf.pl """
    comment = re.compile('#')
    match = re.compile('gconfigroot\s*=\s*"(.*)"', re.I)

    try:
        f = open(configfile, 'r')
    except Exception, e:
        print "Could not find cricket-conf.pl: %s" % e
        sys.exit()
    
    for line in f:
        if comment.match(line):
            continue
        m = match.search(line)
        if m:
            #print "Found configroot to be %s" % m.groups()[0]
            return m.groups()[0]

    return False

def get_datadir(path):
    """
    The datadir contains information about where the rrd-files are stored. This
    information must be available in the cricket-config/Defaults file.
    """
    match = re.compile("datadir\s+=\s+(\S+)", re.I)
    filename = "Defaults"
    datadir = False
    
    try:
        f = open(join(path, filename), 'r')
    except Exception, e:
        print "Error opening %s: %s" % (join(path, filename), e[1])
        sys.exit()
                
    for line in f:
        m = match.search(line)
        if m:
            datadir = m.groups()[0]
            #----------------------------------------------------------------- 
            # %auto-base% is used in Cricket as a variable pointing to the 
            # base directory for the cricket-config
            datadir = re.sub("%auto-base%", path, datadir)
            datadir = re.sub("%.*%", "", datadir)
            datadir = abspath(datadir)
            break

    return datadir

def clear_rrd_database():
    """
    Remove all datasource tuples regarding Cricket in the rrd-database as 
    they are possibly erroneous.
    """
    
    conn = getConnection('default')
    c = conn.cursor()
    
    q = """
    DELETE FROM rrd_datasource 
    WHERE rrd_fileid IN 
    (SELECT rrd_fileid FROM rrd_file WHERE subsystem = 'cricket')
    """
    c.execute(q)
    conn.commit()
    

if __name__ == '__main__':

    usage = "Usage: %s -f <cricket-conf.pl>" % sys.argv[0]
    configfile = ''

    user = getpass.getuser()
    if user != 'navcron':
        print "This script needs to be run as user navcron"
        sys.exit()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hf:', ['help', 'file='])
    except getopt.GetoptError, e:
        print str(err)
        print usage
        sys.exit(1)

    for o, a in opts:
        if o in ['-h', '--help']:
            print usage
            sys.exit(1)
        elif o in ['-f', '-file']:
            configfile = a

    if not configfile:
        print usage
        sys.exit(1)

    main(configfile)

