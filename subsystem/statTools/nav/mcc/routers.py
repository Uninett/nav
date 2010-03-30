"""
Creates Cricket config for routers
"""
import sys
import os
import re
import logging
from os.path import join

from nav.db import getConnection

from nav.mcc import utils

def make_config(config):
    dirname = "routers"
    logger = logging.getLogger('mcc.routers')

    # Get path to cricket-config
    configfile = config.get('mcc', 'configfile')
    configroot = utils.get_configroot(configfile)
    if not configroot:
        logger.error("Could not find configroot in %s, exiting."
                     % config.get('mcc', 'configfile'))
        return False

    fullpath = join(configroot, dirname)
    logger.info("Creating config for %s in %s" % (dirname, fullpath))

    # Get views
    views = utils.parse_views()
    if not views:
        logger.error("Error parsing views, exiting")
        return False

    # Get datadir
    datadir = join(utils.get_datadir(configroot), dirname)
    logger.debug("Datadir set to %s" % datadir)

    # Find oids. We search all files as we cannot be certain of the name
    oidlist = find_oids(logger, fullpath)
    oidlist.extend(utils.get_toplevel_oids(configroot))
    if len(oidlist) <= 0:
        logger.error("Could not find oids in %s - exiting." % fullpath)
        return False

    # Connect to database
    conn = getConnection('default')
    c = conn.cursor()

    # Fetch routers
    sql = """
    SELECT netboxid, ro, sysname, ip, room.descr, typename
    FROM netbox
    JOIN room USING (roomid)
    JOIN type USING (typeid)
    WHERE catid IN ('GW','GSW')
    """
    c.execute(sql)

    # Create target-types
    try:
        f = open(join(fullpath, 'mccTargetTypes'), 'w')
    except Exception, e:
        logger.error("Could not write to file: %s" % e)
        return False
    
    targetlist = []
    containers = []
    for (netboxid, ro, sysname, ip, descr, typename) in c.fetchall():
        logger.info("Creating config for %s" % sysname)
        sql = """
        SELECT oidkey, snmpoid FROM netboxsnmpoid
        JOIN snmpoid USING (snmpoidid)
        WHERE netboxid = %s
        AND (oidsource = 'Cricket' OR snmpoid = '1.3.6.1.2.1.1.3.0')
        """

        c.execute(sql, (netboxid,))

        # Check if rrd-file exists. If not, the rrd-file and corresponding
        # datasources are removed from the database, and config is made from
        # scratch.
        fileexists = utils.check_file_existence(datadir, sysname)

        # Find the oids valid for this box that also exists in the cricket
        # config files.
        targetoids = []
        for (oidkey, snmpoid) in c.fetchall():
            if snmpoid in oidlist:
                targetoids.append(oidkey)

        targetoids.sort()

        # Skip to next netbox if no matching oids were found
        if len(targetoids) <= 0:
            logger.error("No oids found for %s" % sysname)
            continue

        if fileexists:
            # Compare datasources we found with the ones in the database, if
            # any.
            targetoids = utils.compare_datasources(
                datadir, sysname, targetoids)

        # Print ds definition to file
        targetlist.append((sysname, ip, ro, descr, typename))
        f.write("targetType %s\n" % sysname)
        f.write("\tds = \"%s\"\n" % ", ".join(targetoids))
            
        # Create view configuration. We do that by comparing the data from
        # views with the targetoids and see what intersections exists.
        intersections = []
        for entry in views:
            intersect = sorted(set(views[entry]).intersection(targetoids))
            if len(intersect) > 0:
                intersections.append("%s: %s"
                                     % (entry, " ".join(intersect)))

        if len(intersections) > 0:
            f.write("\tview = \"%s\"\n\n" % ", ".join(sorted(intersections)))

        # Create container object and fill it
        container = utils.RRDcontainer(sysname, netboxid)
        counter = 0
        for to in sorted(targetoids):
            container.datasources.append(('ds' + str(counter), to, 'GAUGE'))
            counter = counter + 1

        containers.append(container)


    f.close()
                
    try:
        f = open(join(fullpath, utils.TARGETFILENAME), 'w')
    except Exception, e:
        logger.error("Could not write to file: %s" % e)
        return False
        
    # Create targets
    for (sysname, ip, ro, descr, typename) in targetlist:
        displayname = utils.convert_unicode_to_latin1(sysname)
        if descr:
            typename = utils.encode_and_escape(typename)
            descr = utils.encode_and_escape(descr)
            shortdesc = ", ".join([typename, descr])
        else:
            shortdesc = utils.encode_and_escape(typename)

        logger.info("Writing target %s" % sysname)
        f.write("target \"%s\"\n" % sysname)
        f.write("\tdisplay-name\t = \"%s\"\n" % displayname)
        f.write("\tsnmp-host\t= %s\n" % ip)
        f.write("\tsnmp-community\t= %s\n" % ro)
        f.write("\ttarget-type\t= %s\n" % sysname)
        f.write("\tshort-desc\t= \"%s\"\n\n" % shortdesc)

    f.close()

    utils.updatedb(datadir, containers)

    return True


def find_oids(logger, path):
    """ Search all files in path for oids regarding Cricket-configuration """
    oidlist = []
    match = re.compile("OID\s+(\w+)\s+(\S+)")

    files = os.listdir(path)
    for entry in files:
        fullpath = join(path, entry)
        if os.path.isfile(fullpath):
            try:
                f = open(fullpath, 'r')
            except Exception, e:
                logger.error(e)
                return oidlist
        
        for line in f:
            m = match.search(line)
            if m:
                logger.debug("Found oid %s - %s"
                             % (m.groups()[0], m.groups()[1]))
                oidlist.append(m.groups()[1])

    return list(set(oidlist))

    
