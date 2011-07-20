"""
Creates Cricket config for routers
"""

import os
import re
import logging
from os.path import join

from nav.models.manage import Netbox
from nav.models.oid import NetboxSnmpOid
from django.db.models import Q
from nav.mcc import utils


ROUTER_CATEGORIES = ['GW', 'GSW']


def make_config(config):
    """ Required function, run by mcc.py """

    # This function should be divided in to many smaller ones.

    dirname = "routers"
    logger = logging.getLogger('mcc.routers')

    # Get path to cricket-config
    configfile = config.get('mcc', 'configfile')
    configroot = utils.get_configroot(configfile)
    fullpath = join(configroot, dirname)

    logger.info("Creating config for %s in %s" % (dirname, fullpath))

    # Get views
    views = utils.parse_views()
    if not views:
        logger.error("Error parsing views, exiting")
        return False

    # Get datadir
    datadir = join(configroot, dirname)
    logger.debug("Datadir set to %s" % datadir)

    # Find oids. We search all files as we cannot be certain of the name
    oidlist = find_oids(logger, fullpath)
    oidlist.extend(utils.get_toplevel_oids(configroot))
    if len(oidlist) <= 0:
        logger.error("Could not find oids in %s - exiting." % fullpath)
        return False

    routers = Netbox.objects.filter(category__in=ROUTER_CATEGORIES)

    # Create target-types
    try:
        filehandle = open(join(fullpath, 'navTargetTypes'), 'w')
    except IOError, error:
        logger.error("Could not write to file: %s" % error)
        return False

    targetlist = []
    containers = []
    for router in routers:
        logger.info("Creating config for %s" % router.sysname)

        snmpoids = NetboxSnmpOid.objects.filter(netbox=router).filter(
            Q(snmp_oid__oid_source='Cricket') |
            Q(snmp_oid__oid_key__iexact='sysuptime'))

        # Find the oids valid for this box that also exists in the cricket
        # config files.
        targetoids = []
        for snmpoid in snmpoids:
            if snmpoid.snmp_oid.snmp_oid in oidlist:
                targetoids.append(snmpoid.snmp_oid.oid_key)

        targetoids.sort()

        # Skip to next netbox if no matching oids were found
        if not targetoids:
            logger.error("No oids found for %s" % router.sysname)
            continue

        # Check if rrd-file exists. If not, the rrd-file and corresponding
        # datasources are removed from the database, and config is made from
        # scratch.
        if utils.check_file_existence(datadir, router.sysname):
            # Compare datasources we found with the ones in the database, if
            # any.
            targetoids = utils.compare_datasources(
                datadir, router.sysname, targetoids)

        # Print ds definition to file
        targetlist.append((router.sysname, router.ip, router.read_only,
                           router.room.description, router.type.name))
        filehandle.write("targetType %s\n" % router.sysname)
        filehandle.write("\tds = \"%s\"\n" % ", ".join(targetoids))

        # Create view configuration. We do that by comparing the data from
        # views with the targetoids and see what intersections exists.
        intersections = []
        for entry in views:
            intersect = sorted(set(views[entry]).intersection(targetoids))
            if intersect:
                intersections.append("%s: %s"
                                     % (entry, " ".join(intersect)))

        if intersections:
            filehandle.write("\tview = \"%s\"\n\n" % ", ".join(
                sorted(intersections)))

        # Create container object and fill it
        container = utils.RRDcontainer(router.sysname, router.id)
        counter = 0
        for targetoid in sorted(targetoids):
            container.datasources.append(('ds' + str(counter), targetoid,
                                          'GAUGE'))
            counter = counter + 1

        containers.append(container)


    filehandle.close()

    try:
        filehandle = open(join(fullpath, utils.TARGETFILENAME), 'w')
    except IOError, error:
        logger.error("Could not write to file: %s" % error)
        return False

    # Create targets
    for (sysname, ip, readonly, descr, typename) in targetlist:
        displayname = utils.convert_unicode_to_latin1(sysname)
        if descr:
            typename = utils.encode_and_escape(typename)
            descr = utils.encode_and_escape(descr)
            shortdesc = ", ".join([typename, descr])
        else:
            shortdesc = utils.encode_and_escape(typename)

        logger.info("Writing target %s" % sysname)
        filehandle.write("target \"%s\"\n" % sysname)
        filehandle.write("\tdisplay-name\t = \"%s\"\n" % displayname)
        filehandle.write("\tsnmp-host\t= %s\n" % ip)
        filehandle.write("\tsnmp-community\t= %s\n" % readonly)
        filehandle.write("\ttarget-type\t= %s\n" % sysname)
        filehandle.write("\tshort-desc\t= \"%s\"\n\n" % shortdesc)

    filehandle.close()

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
                filehandle = open(fullpath, 'r')
            except IOError, error:
                logger.error(error)
                return oidlist

        for line in filehandle:
            matcher = match.search(line)
            if matcher:
                logger.debug("Found oid %s - %s"
                             % (matcher.groups()[0], matcher.groups()[1]))
                oidlist.append(matcher.groups()[1])

    return list(set(oidlist))
