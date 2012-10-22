"""
Creates Cricket config for netboxes
"""

import logging
from os.path import join

from nav.models.manage import Netbox
from nav.mcc import utils, dbutils

CATEGORIES = {'routers': ['GW', 'GSW'],
              'switches': ['SW']}
LOGGER = logging.getLogger('mcc.netboxes')


def make_config(config):
    """ Required function, run by mcc.py """

    # Get path to cricket-config
    configfile = config.get('mcc', 'configfile')
    configroot = utils.get_configroot(configfile)

    # Get views
    views = utils.parse_views()
    if not views:
        LOGGER.error("Error parsing views, exiting")
        return False

    dirnames = ['routers', 'switches']

    for dirname in dirnames:
        create_subtree_config(configroot, dirname, views)

    return True

def create_subtree_config(configroot, dirname, views):
    """ Create config for this directory """

    path_to_config = join(configroot, dirname)
    path_to_rrd = join(utils.get_datadir(configroot), dirname)

    LOGGER.debug("Datadir set to %s" % path_to_rrd)
    LOGGER.info("Creating config for %s in %s" % (dirname, path_to_config))

    # Find oids. We search all files as we cannot be certain of the name
    oidlist = utils.find_oids(path_to_config)
    oidlist.extend(utils.get_toplevel_oids(configroot))
    if len(oidlist) <= 0:
        LOGGER.error("Could not find oids in %s - exiting." % path_to_config)
        return False

    containers = []
    target_types = []
    targets = []
    netboxes = Netbox.objects.filter(category__in=CATEGORIES[dirname])
    for netbox in netboxes:
        target_oids = utils.find_target_oids(netbox, oidlist)
        if not target_oids:
            LOGGER.info("No oids found for %s" % netbox.sysname)
            continue
        target_types.append(
            create_targettype_config(netbox, target_oids, views))
        targets.append(create_target_config(netbox))
        containers.append(create_container(netbox, target_oids))

    utils.write_target_types(path_to_config, target_types)
    utils.write_targets(path_to_config, targets)
    dbutils.updatedb(path_to_rrd, containers)

    return True


def create_targettype_config(netbox, snmpoids, views):
    """ Create target type config for this router """

    targetoids = [x.oid_key for x in snmpoids]
    config = ""
    config = config + "targetType %s\n" % netbox.sysname
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


def create_target_config(netbox):
    """ Create Cricket config for this netbox """
    displayname = utils.convert_unicode_to_latin1(netbox.sysname)
    typename = utils.encode_and_escape(netbox.type.name if netbox.type else '')
    if netbox.room.description:
        descr = utils.encode_and_escape(netbox.room.description)
        shortdesc = ", ".join([typename, descr])
    else:
        shortdesc = typename

    LOGGER.info("Writing target %s" % netbox.sysname)
    config = [
        'target "%s"' % str(netbox.sysname),
        '\tdisplay-name\t= "%s"' % displayname,
        '\tsnmp-host\t= %s' % str(netbox.ip),
        '\tsnmp-community\t= %s' % str(netbox.read_only),
        '\ttarget-type\t= %s' % str(netbox.sysname),
        '\tshort-desc\t= "%s"' % shortdesc,
        ''
    ]

    return "\n".join(config)


def create_container(netbox, targetoids):
    """ Create container object and fill it """
    container = utils.RRDcontainer(netbox.sysname, netbox.id)
    counter = 0
    for targetoid in targetoids:
        container.datasources.append(
            utils.Datasource('ds' + str(counter), targetoid.oid_key, 'GAUGE',
                             targetoid.unit))
        counter = counter + 1

    return container


