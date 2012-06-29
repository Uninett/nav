"""
Creates Cricket config for router interfaces.
"""
import logging
import re
import os
from os.path import join, isdir

from nav.mcc import utils, dbutils
from nav.models.manage import Netbox

LOGGER = logging.getLogger(__name__)

CATEGORIES = {'router-interfaces': ['GW', 'GSW'],
              'switch-ports': ['SW', 'GSW']}

INTERFACE_FILTERS = {'router-interfaces': {'gwportprefix__isnull': False},
                     'switch-ports': {'baseport__isnull': False}}


def make_config(config):
    """Make interface config"""

    try:
        configfile = config.get('mcc', 'configfile')
        configroot = utils.get_configroot(configfile)
    except utils.NoConfigRootException:
        LOGGER.error("Could not find configroot in %s, exiting."
        % config.get('mcc', 'configfile'))
        return False

    dirnames = CATEGORIES.keys()

    results = []
    for dirname in dirnames:
        results.append(start_config_creation(dirname, configroot))

    return all(results)


def start_config_creation(dirname, configroot):
    """Start config creation for this config directory"""

    rrdconfigpath = join(configroot, dirname)
    rrddatadir = join(utils.get_datadir(configroot), dirname)

    LOGGER.info("Creating config for %s in %s" % (dirname, rrdconfigpath))

    # Find datasources for the predefined target-types
    datasources = get_interface_datasources(configroot)
    if not datasources:
        return False

    configdirs = []  # The directories we have created config in
    netboxes = Netbox.objects.filter(category__in=CATEGORIES[dirname])
    containers = []  # containers are objects used for database storage
    for netbox in netboxes:
        targetdir = join(rrdconfigpath, netbox.sysname)
        configdirs.append(targetdir)

        # Check if directory exists
        if not isdir(targetdir):
            LOGGER.info("Creating directory %s" % targetdir)
            try:
                os.mkdir(targetdir, 0755)
            except OSError, error:
                LOGGER.error("Error creating %s: %s" % (targetdir, error))
                continue

        containers.extend(create_interface_config(
            netbox, targetdir, dirname, datasources))

    dbutils.updatedb(rrddatadir, containers)
    utils.find_and_remove_old_config(rrdconfigpath, configdirs)

    return True


def create_interface_config(netbox, targetdir, dirname, datasources):
    """Create config for this router and store it in targetdir

    returns: a list of containers
    """
    LOGGER.info("Creating config for %s" % targetdir)

    interfaces = netbox.interface_set.filter(
        **INTERFACE_FILTERS[dirname]).distinct().order_by('ifindex')

    reversecounter = interfaces.count()
    snmp_version = format_snmp_version(netbox)
    stringbuilder = []

    if interfaces.count() <= 0:
        LOGGER.info("No interfaces found for %s" % netbox.sysname)
        return []

    # Create default target config for this router
    stringbuilder.extend(create_default_target(netbox, snmp_version))

    containers = []
    targets = []
    for interface in interfaces:
        if not interface.ifname:
            LOGGER.error("%s: No ifname found for interfaceid %s" % (
                netbox.sysname, interface.id))
            continue

        targetname = utils.create_target_name(interface.ifname)
        stringbuilder.extend(
            create_target(interface, targetname, reversecounter))
        reversecounter -= 1
        targets.append(targetname)

        containers.append(create_rrd_container(datasources, interface, netbox,
            snmp_version, targetname))

    # Make a target for all graphs, put it on top with order
    stringbuilder.extend(create_all_target(targets, interfaces.count()))

    # Write targets to file
    if write_to_file(targetdir, stringbuilder):
        return containers
    else:
        return []


def create_default_target(router, snmp_version):
    """Create common config for this router"""

    strings = ["target --default--\n",
               "\tsnmp-host\t= %s\n" % router.ip,
               "\tsnmp-version\t= %s\n" % snmp_version]
    if snmp_version == '2c':
        strings.append("\ttarget-type\t= snmpv2-interface\n")
    strings.append("\tsnmp-community\t= %s\n\n" % router.read_only)

    return strings


def create_target(interface, targetname, reversecounter):
    """Create config for interface"""

    ifalias = interface.ifalias or '-'
    displayname = utils.encode_and_escape(interface.ifname)
    shortdesc = utils.encode_and_escape(ifalias)

    LOGGER.info('Creating target %s (%s)' % (targetname, displayname))

    strings = ["target \"%s\"\n" % targetname,
               "\tdisplay-name = \"%s\"\n" % displayname,
               "\tinterface-index = %s\n" % interface.ifindex,
               "\tshort-desc = \"%s\"\n" % shortdesc,
               "\tifname = \"%s\"\n" % interface.ifname,
               "\torder = %s\n\n" % reversecounter]

    return strings


def create_all_target(targets, count):
    """Create all-target to display all graphs on one page"""

    strings = ["target \"all\"\n",
               "\ttargets = \"%s\"\n" % ";".join(targets),
               "\torder = %s\n" % (count + 1)]

    return strings


def format_snmp_version(router):
    """Convert snmp-version from int to string"""
    if router.snmp_version == 2:
        return '2c'
    else:
        return str(router.snmp_version)


def create_rrd_container(datasources, interface, router, snmp_version,
                         targetname):
    """Create the container used for db-storage"""

    container = utils.RRDcontainer(
        targetname + ".rrd", router.id, router.sysname, 'interface',
        interface.id, speed=interface.speed)
    counter = 0
    for datasource in datasources[snmp_version]:
        container.datasources.append(
            ('ds' + str(counter), datasource, 'DERIVE')
        )
        counter += 1
    return container


def write_to_file(targetdir, strings):
    """Write all targets to file

    returns: boolean indicating success
    """
    try:
        handle = open(join(targetdir, utils.TARGETFILENAME), 'w')
    except IOError, error:
        LOGGER.error("Could not open targetsfile for writing: %s" % error)
        return False

    handle.writelines(strings)
    handle.close()

    return True


def get_interface_datasources(configroot):
    """Get datasource for v1 and v2 targettypes"""

    lines = read_defaults_file(configroot)

    matchv1 = re.compile("targettype\s+standard-interface", re.I)
    matchv2 = re.compile("targettype\s+snmpv2-interface", re.I)
    dsmatch = re.compile("ds\s+=\s+\"(.+)\"")

    is_standard_interface = False
    is_v2_interface = False

    datasources = {}
    for line in lines:
        if matchv1.search(line):
            is_standard_interface = True
            is_v2_interface = False
        elif matchv2.search(line):
            is_standard_interface = False
            is_v2_interface = True

        datasource_match = dsmatch.search(line)
        if datasource_match and is_standard_interface:
            datasources['1'] = [x.strip() for x in
                                datasource_match.groups()[0].split(',')]
            is_standard_interface = False

        elif datasource_match and is_v2_interface:
            datasources['2c'] = [x.strip() for x in
                                 datasource_match.groups()[0].split(',')]
            is_v2_interface = False

    return datasources


def read_defaults_file(filepath):
    """Open and return Defaults-file from path"""
    filename = join(filepath, 'Defaults')
    try:
        filehandle = open(filename, 'r')
        lines = filehandle.readlines()
        filehandle.close()
        return lines
    except IOError, error:
        LOGGER.error("Could not open %s: %s" % (filename, error))
        return []


