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
        target_oids = utils.check_database_sanity(path_to_rrd, netbox,
                                                  target_oids)
        target_types.append(
            utils.create_targettype_config(netbox, target_oids, views))
        targets.append(utils.create_target_config(netbox))
        containers.append(utils.create_container(netbox, target_oids))

    utils.write_target_types(path_to_config, target_types)
    utils.write_targets(path_to_config, targets)
    dbutils.updatedb(path_to_rrd, containers)

    return True
