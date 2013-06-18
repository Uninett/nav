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
from django.db.models import Q

LOGGER = logging.getLogger(__name__)

IPV6MODULE = 'ipv6-counters'

CONFIG = {
    IPV6MODULE: {
        'dirname': 'ipv6-interfaces',
        'categories': ['GW', 'GSW'],
        'filter': Q(gwportprefix__isnull=False),
        'extra': {'where': ['family(gwip)=6']}
    },
    'port-counters': {
        'dirname': 'ports',
        'filter': (Q(gwportprefix__isnull=False) |
                   Q(baseport__isnull=False) |
                   Q(ifconnectorpresent=True)),
    },
}

DATASOURCES = {}


@utils.timed
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


@utils.timed
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
    global DATASOURCES
    DATASOURCES = get_interface_datasources(configroot)
    if not DATASOURCES:
        return False

    configdirs = []  # The directories we have created config in
    query = Q(interface__isnull=False)
    if 'categories' in config:
        query = query & Q(category__in=config['categories'])
    netboxes = Netbox.objects.filter(query).distinct()
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

        containers.extend(create_interface_config(netbox, targetdir, module))
        LOGGER.debug('Done with %s' % netbox)

    LOGGER.debug('Created %s targets in %s' % (len(containers), dirname))
    LOGGER.debug('Starting to update database')
    dbutils.updatedb(rrddatadir, containers)

    LOGGER.debug('Looking for old config')
    utils.find_and_remove_old_config(rrdconfigpath, configdirs)

    return True


@utils.timed
def create_interface_config(netbox, targetdir, module):
    """Create config for this netbox and store it in targetdir

    returns: a list of containers
    """
    LOGGER.info("Creating config for %s" % targetdir)

    config = CONFIG[module]
    interfaces = netbox.interface_set.select_related('netbox').filter(
        config['filter']).distinct().order_by('ifindex')
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

        containers.append(create_rrd_container(interface, targetname, module))

    # Make a target for all graphs, put it on top with order
    stringbuilder.extend(create_all_target(targets, interfaces.count()))

    # Write targets to file
    if write_to_file(targetdir, stringbuilder):
        return containers
    else:
        return []


@utils.timed
def create_default_target(netbox, snmp_version, module):
    """Create common config for this netbox"""

    strings = ["target --default--\n",
               "\tsnmp-host\t= %s\n" % utils.format_ip_address(netbox.ip),
               "\tsnmp-version\t= %s\n" % snmp_version]

    if module == IPV6MODULE:
        strings.append("\ttarget-type\t= ipv6-interface\n")
    elif snmp_version == '2c':
        strings.append("\ttarget-type\t= snmpv2-interface\n")
    strings.append("\tsnmp-community\t= %s\n\n" % netbox.read_only)

    return strings


@utils.timed
def create_target(interface, targetname, reversecounter):
    """Create config for interface"""

    ifalias = interface.ifalias or '-'
    displayname = utils.encode_and_escape(interface.ifname)
    shortdesc = utils.encode_and_escape(ifalias)

    LOGGER.debug('Creating target %s (%s)' % (targetname, displayname))

    strings = ["target \"%s\"\n" % targetname,
               "\tdisplay-name = \"%s\"\n" % displayname,
               "\tinterface-index = %s\n" % interface.ifindex,
               "\tshort-desc = \"%s\"\n" % shortdesc,
               "\tifname = \"%s\"\n" % interface.ifname,
               "\torder = %s\n\n" % reversecounter]

    return strings


@utils.timed
def create_all_target(targets, count):
    """Create all-target to display all graphs on one page"""

    strings = ["target \"all\"\n",
               "\ttargets = \"%s\"\n" % ";".join(targets),
               "\torder = %s\n" % (count + 1)]

    return strings


@utils.timed
def format_snmp_version(netbox):
    """Convert snmp-version from int to string"""
    if netbox.snmp_version == 2:
        return '2c'
    else:
        return str(netbox.snmp_version)


@utils.timed
def create_rrd_container(interface, targetname, module):
    """Create the container used for db-storage"""

    netbox = interface.netbox
    container = utils.RRDcontainer(
        targetname + ".rrd", netbox.id, netbox.sysname, 'interface',
        interface.id, speed=interface.speed, category=module)
    snmp_version = format_snmp_version(netbox)
    container.datasources = get_datasources(snmp_version)

    return container


@utils.Memoize
def get_datasources(snmp_version):
    """Return list of datasources for this snmp_version"""
    datasources = []
    for index, datasource in enumerate(DATASOURCES[snmp_version]):
        datasources.append(utils.Datasource('ds' + str(index), datasource,
                                            'DERIVE', get_unit(datasource)))
    return datasources


@utils.timed
def get_unit(oid_key):
    """Get unit for this oid_key from database"""
    try:
        return SnmpOid.objects.get(oid_key=oid_key).unit
    except SnmpOid.DoesNotExist:
        return ''


@utils.timed
def write_to_file(targetdir, strings):
    """Write all targets to file

    returns: boolean indicating success
    """
    try:
        targetfile = join(targetdir, utils.TARGETFILENAME)
        LOGGER.debug('Writing config to %s' % targetfile)
        handle = open(targetfile, 'w')
    except IOError, error:
        LOGGER.error("Could not open targetsfile for writing: %s" % error)
        return False
    else:
        handle.writelines(strings)
        handle.close()
        return True


@utils.timed
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


@utils.timed
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
