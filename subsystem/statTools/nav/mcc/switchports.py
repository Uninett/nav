"""
Creates Cricket config for switch ports.
"""
import logging
import os
import re
from os.path import join, isdir

from nav.db import getConnection
from nav.mcc import utils

logger = logging.getLogger(__name__)

def make_config(config):
    dirname = 'switch-ports'
    # Get path to cricket-config
    configfile = config.get('mcc', 'configfile')
    configroot = utils.get_configroot(configfile)

    if not configroot:
        logger.error("Could not find configroot in %s, exiting."
                     % config.get('mcc', 'configfile'))
        return False

    fullpath = join(configroot, dirname)
    logger.info("Creating config for %s in %s" % (dirname, fullpath))
    
    # Get all subdirectories. The purpose of this is to clean up all
    # directories which may be left over from previous runs but are not
    # included in this run.
    subdirs = []
    for d in os.listdir(fullpath):
        subdir = join(fullpath, d)
        if os.path.isdir(subdir):
            subdirs.append(subdir)
    logger.debug("Subdirs: %s" % subdirs)

    # Get datadir
    datadir = join(utils.get_datadir(configroot), dirname)
    logger.debug("Datadir set to %s" % datadir)

    # Find datasources for the predefined target-types
    datasources = get_interface_datasources(configroot)
    if not datasources:
        return False

    # Connect to database
    conn = getConnection('default')
    c = conn.cursor()

    # Get all switches from database
    sql = """
    SELECT netboxid, sysname, ip, ro, snmp_version
    FROM netbox
    WHERE catid IN ('SW', 'GSW')
    ORDER BY sysname
    """
    c.execute(sql)
    
    containers = []
    for (netboxid, sysname, ip, ro, snmp_version) in c.fetchall():
        if snmp_version == 2:
            snmp_version = '2c'
        else:
            snmp_version = str(snmp_version)
            
        targetdir = join(fullpath, sysname)
        logger.info("Creating config for %s" % targetdir)

        # Remove targetdir from subdirs
        logger.debug('Removing %s from subdirs' % targetdir)
        try:
            subdirs.remove(targetdir)
        except ValueError, e:
            logger.error("%s not in %s" % (targetdir, subdirs))
        logger.debug(subdirs)

        # Check if directory exists
        if not isdir(targetdir):
            logger.info("Creating directory %s" % targetdir)
            try:
                os.mkdir(targetdir, 0755)
            except Exception, e:
                logger.error("Error creating %s: %s" % (targetdir, e))
                continue

        # Open targets file for writing
        try:
            f = open(join(targetdir, utils.TARGETFILENAME), 'w')
        except Exception, e:
            logger.error("Could not open targetsfile for writing: %s" % e)
            continue
        
        # Fetch all interfaces for this netbox
        interfacesq = """
        SELECT interfaceid, ifname, ifindex, ifalias
        FROM netbox
        JOIN interface_swport USING (netboxid)
        WHERE netboxid = %s
        AND gone_since IS NULL
        ORDER BY ifindex
        """
        c.execute(interfacesq, (netboxid,))

        # Fill in default targetconfig
        if c.rowcount <= 0:
            logger.info("No interfaces found for %s" % sysname)
            continue
        
        f.write("target --default--\n")
        f.write("\tsnmp-host\t= %s\n" % ip)
        f.write("\tsnmp-version\t= %s\n" % snmp_version)
        if snmp_version == '2c':
            f.write("\ttarget-type\t= snmpv2-interface\n")
        f.write("\tsnmp-community\t= %s\n\n" % ro)

        reversecounter = c.rowcount

        targets = []

        # Fill in targets
        for (interfaceid, ifname, ifindex, ifalias) in c.fetchall():
            if not ifname:
                logger.error("%s: No ifname found for interfaceid %s"
                             % (sysname, swportid))
                continue

            ifalias = ifalias or '-'
            targetname = utils.create_target_name(ifname)
            displayname = utils.filter_name(ifname)
            shortdesc = utils.filter_name(ifalias)

            logger.info('Creating target %s (%s)' % (targetname, displayname))

            f.write("target \"%s\"\n" % targetname)
            f.write("\tdisplay-name = \"%s\"\n" % displayname)
            f.write("\tinterface-index = %s\n" % ifindex)
            f.write("\tshort-desc = \"%s\"\n" % shortdesc)
            f.write("\tifname = %s\n" % ifname)
            f.write("\torder = %s\n\n" % reversecounter)
            reversecounter = reversecounter - 1

            targets.append(targetname)

            # filename ()
            # Netboxid
            # key - swport
            # value - swportid
            container = utils.RRDcontainer(targetname + '.rrd',
                                             netboxid, sysname, 'swport',
                                             interfaceid)

            counter = 0
            for ds in datasources[snmp_version]:
                container.datasources.append(
                    ('ds' + str(counter), ds, 'DERIVE')
                    )
                counter = counter + 1

            containers.append(container)

        # Make a target for all graphs, put it on top with order
        f.write("target \"all\"\n")
        f.write("\ttargets = \"%s\"\n" % ";".join(targets))
        f.write("\torder = %s\n" % (c.rowcount + 1))

        f.close()


    utils.updatedb(datadir, containers)
    utils.remove_old_config(subdirs)
    return True

def get_interface_datasources(configroot):
    """ Get datasource for v1 and v2 targettypes """
    
    filename = join(configroot, 'Defaults')
    try:
        f = open(filename, 'r')
    except Exception, e:
        logger.error("Could not open %s: %s" % (filename, e))
        return False

    matchv1 = re.compile("targettype\s+standard-interface", re.I)
    matchv2 = re.compile("targettype\s+snmpv2-interface", re.I)
    dsmatch = re.compile("ds\s+=\s+\"(.+)\"")

    m1 = False
    m2 = False

    datasources = {}
    for line in f:
        if matchv1.search(line):
            m1 = True
            m2 = False
        elif matchv2.search(line):
            m1 = False
            m2 = True

        ds = dsmatch.search(line)
        if ds and m1:
            datasources['1'] = [x.strip() for x in ds.groups()[0].split(',')]
            m1 = False
            
        elif ds and m2:
            datasources['2c'] = [x.strip() for x in ds.groups()[0].split(',')]
            m2 = False

    f.close()

    return datasources
