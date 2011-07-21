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
LOGGER = logging.getLogger('mcc.routers')


def make_config(config):
    """ Required function, run by mcc.py """

    dirname = "routers"

    # Get path to cricket-config
    configfile = config.get('mcc', 'configfile')
    configroot = utils.get_configroot(configfile)
    path_to_config = join(configroot, dirname)
    path_to_rrd = join(utils.get_datadir(configroot), dirname)

    LOGGER.debug("Datadir set to %s" % path_to_rrd)
    LOGGER.info("Creating config for %s in %s" % (dirname, path_to_config))

    # Get views
    views = utils.parse_views()
    if not views:
        LOGGER.error("Error parsing views, exiting")
        return False

    # Find oids. We search all files as we cannot be certain of the name
    oidlist = find_oids(path_to_config)
    oidlist.extend(utils.get_toplevel_oids(configroot))
    if len(oidlist) <= 0:
        LOGGER.error("Could not find oids in %s - exiting." % path_to_config)
        return False

    containers = []
    target_types = []
    targets = []
    routers = Netbox.objects.filter(category__in=ROUTER_CATEGORIES)
    for router in routers:
        target_oids = find_target_oids(router, oidlist)
        if not target_oids:
            LOGGER.info("No oids found for %s" % router.sysname)
            continue
        target_oids = check_database_sanity(path_to_rrd, router, target_oids)
        target_types.append(
                    create_targettype_config(router, target_oids, views))
        targets.append(create_target_config(router))
        containers.append(create_container(router, target_oids))

    write_target_types(path_to_config, target_types)
    write_targets(path_to_config, targets)
    utils.updatedb(path_to_rrd, containers)

    return True


def find_target_oids(router, oidlist):
    """ Find the oids this router answers to that also exist in the
        cricket config files. """
    snmpoids = NetboxSnmpOid.objects.filter(netbox=router).filter(
                      Q(snmp_oid__oid_source='Cricket') |
                      Q(snmp_oid__oid_key__iexact='sysuptime'))
    targetoids = []
    for snmpoid in snmpoids:
        if snmpoid.snmp_oid.snmp_oid in oidlist:
            targetoids.append(snmpoid.snmp_oid.oid_key)

    targetoids.sort()
    return targetoids


def check_database_sanity(path_to_rrd, router, targetoids):
    """ Check if rrd-file exists. If not the database tuple regarding this
        file is deleted """
    if utils.check_file_existence(path_to_rrd, router.sysname):
        # Compare datasources we found with the ones in the database, if
        # any.
        targetoids = utils.compare_datasources(
            path_to_rrd, router.sysname, targetoids)

    return targetoids


def create_targettype_config(router, targetoids, views):
    """ Create target type config for this router """
    config = ""
    config = config + "targetType %s\n" % router.sysname
    config = config + "\tds = \"%s\"\n" % ", ".join(targetoids)

    # Create view configuration. We do that by comparing the data from
    # views with the targetoids and see what intersections exists.
    intersections = []
    for entry in views:
        intersect = sorted(set(views[entry]).intersection(targetoids))
        if intersect:
            intersections.append("%s: %s" % (entry, " ".join(intersect)))

    if intersections:
        config = config + "\tview = \"%s\"\n\n" % ", ".join(
            sorted(intersections))

    return config


def create_target_config(router):
    """ Create Cricket config for this router """
    displayname = utils.convert_unicode_to_latin1(router.sysname)
    if router.room.description:
        typename = utils.encode_and_escape(router.type.name)
        descr = utils.encode_and_escape(router.room.description)
        shortdesc = ", ".join([typename, descr])
    else:
        shortdesc = utils.encode_and_escape(router.type.name)

    LOGGER.info("Writing target %s" % router.sysname)
    config = ""
    config = config + "target \"%s\"\n" % router.sysname
    config = config + "\tdisplay-name\t = \"%s\"\n" % displayname
    config = config + "\tsnmp-host\t= %s\n" % router.ip
    config = config + "\tsnmp-community\t= %s\n" % router.read_only
    config = config + "\ttarget-type\t= %s\n" % router.sysname
    config = config + "\tshort-desc\t= \"%s\"\n\n" % shortdesc

    return config


def find_oids(path):
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
                LOGGER.error(error)
                return oidlist

        for line in filehandle:
            matcher = match.search(line)
            if matcher:
                LOGGER.debug("Found oid %s - %s"
                             % (matcher.groups()[0], matcher.groups()[1]))
                oidlist.append(matcher.groups()[1])

    return list(set(oidlist))


def create_container(router, targetoids):
    """ Create container object and fill it """
    container = utils.RRDcontainer(router.sysname, router.id)
    counter = 0
    for targetoid in sorted(targetoids):
        container.datasources.append(('ds' + str(counter), targetoid,
                                      'GAUGE'))
        counter = counter + 1

    return container


def write_target_types(path_to_config, target_types):
    """ Write target types to file. Do not fail silently """
    filehandle = open(join(path_to_config, 'navTargetTypes'), 'w')
    filehandle.write("\n".join(target_types))
    filehandle.close()


def write_targets(path_to_config, targets):
    """ Write targets to file. """
    filehandle = open(join(path_to_config, utils.TARGETFILENAME), 'w')
    filehandle.write("\n".join(targets))
    filehandle.close()
