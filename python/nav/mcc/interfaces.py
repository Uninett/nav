"""
Creates Cricket config for router interfaces.
"""
import logging
import re
import os
from os.path import join, isdir

from nav.mcc import utils, dbutils
from nav.models.manage import Netbox
from nav.models.oid import NetboxSnmpOid, SnmpOid

LOGGER = logging.getLogger(__name__)

IPV6MODULE = 'ipv6-counters'

CONFIG = {
    IPV6MODULE: {
        'dirname': 'ipv6-interfaces',
        'categories': ['GW', 'GSW'],
        'filter': {'gwportprefix__isnull': False},
        'extra': {'where': ['family(gwip)=6']}
    },
    'router-interfaces-counters': {
        'dirname': 'router-interfaces',
        'categories': ['GW', 'GSW'],
        'filter': {'gwportprefix__isnull': False}
    },
    'switch-port-counters': {
        'dirname': 'switch-ports',
        'categories': ['SW', 'GSW'],
        'filter': {'baseport__isnull': False}
    }
}

def make_config(config):
    """Make interface config"""

    try:
        configfile = config.get('mcc', 'configfile')
        configroot = utils.get_configroot(configfile)
    except utils.NoConfigRootException:
        LOGGER.error("Could not find configroot in %s, exiting."
        % config.get('mcc', 'configfile'))
        return False

    results = []
    for module in CONFIG:
        LOGGER.info("Starting module %s" % module)
        results.append(start_config_creation(module, configroot))

    return all(results)


def start_config_creation(module, configroot):
    """Start config creation for this config directory"""

    config = CONFIG[module]
    dirname = config['dirname']
    rrdconfigpath = join(configroot, dirname)

    if not isdir(rrdconfigpath):
        LOGGER.error("%s does not exist, please create it" % rrdconfigpath)
        return False

    rrddatadir = join(utils.get_datadir(configroot), dirname)

    LOGGER.info("Creating config for %s in %s" % (dirname, rrdconfigpath))

    # Find datasources for the predefined target-types
    datasources = get_interface_datasources(configroot)
    if not datasources:
        return False

    configdirs = []  # The directories we have created config in
    netboxes = Netbox.objects.filter(category__in=config['categories'])
    containers = []  # containers are objects used for database storage
    for netbox in netboxes:
        # Special handling of IPV6 module
        if module == IPV6MODULE:
            try:
                netbox.netboxsnmpoid_set.get(
                    snmp_oid__oid_key='ipIfStatsHCInOctets.ipv6')
            except NetboxSnmpOid.DoesNotExist:
                continue

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
            netbox, targetdir, module, datasources))

    dbutils.updatedb(rrddatadir, containers)
    utils.find_and_remove_old_config(rrdconfigpath, configdirs)

    return True


def create_interface_config(netbox, targetdir, module, datasources):
    """Create config for this netbox and store it in targetdir

    returns: a list of containers
    """
    LOGGER.info("Creating config for %s" % targetdir)

    config = CONFIG[module]
    interfaces = netbox.interface_set.filter(
        **config['filter']).distinct().order_by('ifindex')
    if 'extra' in config:
        interfaces = interfaces.extra(**config['extra'])

    reversecounter = interfaces.count()
    snmp_version = format_snmp_version(netbox)
    stringbuilder = []

    if interfaces.count() <= 0:
        LOGGER.info("No interfaces found for %s" % netbox.sysname)
        return []

    # Create default target config for this netbox
    stringbuilder.extend(create_default_target(netbox, snmp_version, module))

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

        containers.append(create_rrd_container(datasources, interface,
                                               targetname, module))

    # Make a target for all graphs, put it on top with order
    stringbuilder.extend(create_all_target(targets, interfaces.count()))

    # Write targets to file
    if write_to_file(targetdir, stringbuilder):
        return containers
    else:
        return []


def create_default_target(netbox, snmp_version, module):
    """Create common config for this netbox"""

    strings = ["target --default--\n",
               "\tsnmp-host\t= %s\n" % netbox.ip,
               "\tsnmp-version\t= %s\n" % snmp_version]

    if module == IPV6MODULE:
        strings.append("\ttarget-type\t= ipv6-interface\n")
    elif snmp_version == '2c':
        strings.append("\ttarget-type\t= snmpv2-interface\n")
    strings.append("\tsnmp-community\t= %s\n\n" % netbox.read_only)

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


def format_snmp_version(netbox):
    """Convert snmp-version from int to string"""
    if netbox.snmp_version == 2:
        return '2c'
    else:
        return str(netbox.snmp_version)


def create_rrd_container(datasources, interface, targetname, module):
    """Create the container used for db-storage"""

    netbox = interface.netbox
    container = utils.RRDcontainer(
        targetname + ".rrd", netbox.id, netbox.sysname, 'interface',
        interface.id, speed=interface.speed, category=module)
    snmp_version = format_snmp_version(netbox)
    for index, datasource in enumerate(datasources[snmp_version]):
        container.datasources.append(
            utils.Datasource('ds' + str(index), datasource, 'DERIVE',
                             get_unit(datasource)))
    return container


def get_unit(oid_key):
    """Get unit for this oid_key from database"""
    try:
        return SnmpOid.objects.get(oid_key=oid_key).unit
    except SnmpOid.DoesNotExist:
        return ''


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

    matchv1 = re.compile(r"targettype\s+standard-interface", re.I)
    matchv2 = re.compile(r"targettype\s+snmpv2-interface", re.I)
    dsmatch = re.compile(r"ds\s+=\s+\"(.+)\"")

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
