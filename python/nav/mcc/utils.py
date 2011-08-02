"""
Contains help functions for the various config creation modules.
"""
import re
import sys
import logging
import os
from nav.errors import GeneralException
from os.path import join, abspath
from subprocess import Popen, PIPE

from nav import path
from nav.db import getConnection
from nav.models.oid import NetboxSnmpOid
from django.db.models import Q

LOGGER = logging.getLogger(__name__)
TARGETFILENAME = 'navTargets'


class NoConfigRootException(GeneralException):
    "Could not find Crickets configroot ($gConfigRoot in cricket-conf.pl)"


def start_config_creation(modules, config):
    """
    Start modules. Check if directory exists, if not create it.
    Pass control to module
    """

    for module in modules:
        LOGGER.info("Starting module %s" % module)
        mod = __import__(module, globals(), locals(), ['make_config'])
        result = mod.make_config(config)
        if not result:
            LOGGER.error("Module %s reports error creating config." % module)
        else:
            LOGGER.info("Module %s successfully done." % module)

    LOGGER.info("Done creating config")


def get_configroot(configfile):
    """Get path for configroot from cricket-conf.pl"""
    cricket_config = _get_as_file(configfile).read()
    perl = Popen("perl", stdin=PIPE, stdout=PIPE, close_fds=True)

    perl.stdin.write(cricket_config)
    perl.stdin.write("""\nprint "$gConfigRoot\\n";\n""")
    perl.stdin.close()

    configroot = perl.stdout.readline().strip()
    perl.wait()

    if not configroot:
        raise NoConfigRootException

    LOGGER.info("Found configroot to be %s", configroot)
    return configroot


def _get_as_file(thing):
    """ Get thing as file """
    if hasattr(thing, 'read'):
        return thing
    else:
        return file(thing, 'r')


def parse_views():
    """ Parse configuration file with view definitions """
    views = {}

    # Fail early if no views exist
    handle = open(join(path.sysconfdir, "cricket-views.conf"))

    for line in handle:
        if line.startswith("view"):
            key, value = line.split(':')
            key = re.sub("view\s+", "", key)
            values = [x.strip() for x in value.split()]
            LOGGER.debug("view: %s -> %s" % (key, values))
            views[key] = values

    return views


def get_toplevel_oids(filepath):
    """ Search all files in path for oids regarding Cricket-configuration """
    oidlist = []
    match = re.compile("OID\s+(\w+)\s+(\S+)")

    try:
        handle = open(join(filepath, 'Defaults'), 'r')
    except Exception, error:
        LOGGER.error(error)
        sys.exit()

    for line in handle:
        matchobject = match.search(line)
        if matchobject:
            LOGGER.debug("Found oid %s - %s"
                         % (matchobject.groups()[0], matchobject.groups()[1]))
            oidlist.append(matchobject.groups()[1])

    return set(oidlist)


def get_datadir(filepath):
    """
    The datadir contains information about where the rrd-files are stored. This
    information must be available in the cricket-config/Defaults file.
    """
    match = re.compile("datadir\s+=\s+(\S+)", re.I)
    filename = "Defaults"
    datadir = ""

    try:
        handle = open(join(filepath, filename), 'r')
    except Exception, error:
        LOGGER.error("Error opening %s: %s" % (join(filepath, filename),
                                               error[1]))
        sys.exit()

    for line in handle:
        mat = match.search(line)
        if mat:
            datadir = mat.groups()[0]
            #-----------------------------------------------------------------
            # %auto-base% is used in Cricket as a variable pointing to the
            # base directory for the cricket-config
            datadir = re.sub("%auto-base%", filepath, datadir)
            datadir = re.sub("%.*%", "", datadir)
            datadir = abspath(datadir)
            break

    return datadir


def compare_datasources(path_to_config, filename, targetoids):
    """
    Compare the datasources from the database with the ones found in file
    (targetoids). If the number in database is larger than or equal to the
    number in file, use database as source for the datasources. Else expand
    rrd-file and update database (not implemented)
    """

    oids = targetoids

    conn = getConnection('default')
    cur = conn.cursor()

    if not filename.endswith('.rrd'):
        filename = filename + '.rrd'

    numdsq = """SELECT name, descr FROM rrd_file
    JOIN rrd_datasource USING (rrd_fileid)
    WHERE path = %s AND filename = %s
    ORDER BY name
    """
    cur.execute(numdsq, (path_to_config, filename))
    if cur.rowcount > 0:
        LOGGER.debug("Found %s datasources in database (%s in file)" \
                     % (cur.rowcount, len(targetoids)))
        if cur.rowcount >= len(targetoids):
            LOGGER.debug(">= Using database as base for targetoids")
            # There are more or equal number of datasources in the database
            # Reset targetoids and fill it from database
            oids = []
            for name, descr in cur.fetchall():
                LOGGER.debug("Appending %s as %s" % (descr, name))
                oids.append(descr)
        else:
            # There are less datasources in the database
            # Find a way to expand the file with the missing datasources...
            LOGGER.debug("< Must expand rrd-file (not implemented)")

    return oids


def check_file_existence(datadir, sysname):
    """
    Check if rrd-file exists. If not, delete tuple from database.
    """

    if not sysname.endswith('.rrd'):
        sysname = sysname + '.rrd'
    filename = join(datadir, sysname)

    if not os.path.exists(filename):
        LOGGER.info("File %s does not exist, deleting tuple from database" \
                    % filename)

        conn = getConnection('default')
        cur = conn.cursor()
        sql = """DELETE FROM rrd_file WHERE path = %s AND filename = %s """
        cur.execute(sql, (datadir, sysname))

        conn.commit()
        return False

    LOGGER.info('file %s existed' % filename)
    return True


def create_target_name(name):
    """
    Remove and replace certain characters from the string to make sure it is
    suitable as a filename.
    """
    name = re.sub('\W', '_', name)
    name = name.lower()

    return name


def convert_unicode_to_latin1(unicode_object):
    """
    Encode a unicode object to a latin-1 string
    """
    # Cricket always displays latin-1. Database returns data as unicode
    # objects. Encode it to display correctly.
    try:
        encoded_string = unicode_object.encode('latin-1', 'ignore')
    except Exception, error:
        LOGGER.error("Could not encode %s to latin-1: %s" % (unicode_object,
                                                             error))
        return unicode_object

    return encoded_string


def encode_and_escape(string):
    """
    Encode and escape object to make it presentable for
    the Cricket webpage.
    """
    if isinstance(string, unicode):
        string = convert_unicode_to_latin1(string)
    string = string.replace("\"", "&quot;")

    return string


def remove_old_config(dirs):
    """
    Input is a list of directories. Remove those if they contain nothing but
    the mccTargets file. If they contain more, remove only the mccTargets file.
    """

    for directory in dirs:
        LOGGER.debug("Checking %s for removal." % directory)
        files = os.listdir(directory)
        try:
            files.remove(TARGETFILENAME)
            os.remove(join(directory, TARGETFILENAME))
        except ValueError:
            LOGGER.error("Could not find %s in %s" % (TARGETFILENAME,
                                                      directory))

        if not len(files):
            # Remove dir if it is empty
            try:
                os.rmdir(directory)
                LOGGER.info("%s removed." % directory)
            except Exception, error:
                LOGGER.error("Could not remove %s: %s" % (directory, error))
        else:
            LOGGER.info("%s is not empty, leaving it alone." % directory)


def find_target_oids(netbox, oidlist):
    """ Find the oids this netbox answers to that also exist in the
        cricket config files. """
    snmpoids = NetboxSnmpOid.objects.filter(netbox=netbox).filter(
                      Q(snmp_oid__oid_source='Cricket') |
                      Q(snmp_oid__oid_key__iexact='sysuptime'))
    targetoids = []
    for snmpoid in snmpoids:
        if snmpoid.snmp_oid.snmp_oid in oidlist:
            targetoids.append(snmpoid.snmp_oid.oid_key)

    targetoids.sort()
    return targetoids


def check_database_sanity(path_to_rrd, netbox, targetoids):
    """ Check if rrd-file exists. If not the database tuple regarding this
        file is deleted """
    if check_file_existence(path_to_rrd, netbox.sysname):
        # Compare datasources we found with the ones in the database, if
        # any.
        targetoids = compare_datasources(path_to_rrd, netbox.sysname,
                                         targetoids)

    return targetoids


def find_oids(path_to_config):
    """ Search all files in path for oids regarding Cricket-configuration """

    oidlist = []
    match = re.compile("OID\s+(\w+)\s+(\S+)")

    files = os.listdir(path_to_config)
    for entry in files:
        fullpath = join(path_to_config, entry)
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


def create_targettype_config(netbox, targetoids, views):
    """ Create target type config for this router """
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
    displayname = convert_unicode_to_latin1(netbox.sysname)
    if netbox.room.description:
        typename = encode_and_escape(netbox.type.name)
        descr = encode_and_escape(netbox.room.description)
        shortdesc = ", ".join([typename, descr])
    else:
        shortdesc = encode_and_escape(netbox.type.name)

    LOGGER.info("Writing target %s" % netbox.sysname)
    config = ""
    config = config + "target \"%s\"\n" % netbox.sysname
    config = config + "\tdisplay-name\t = \"%s\"\n" % displayname
    config = config + "\tsnmp-host\t= %s\n" % netbox.ip
    config = config + "\tsnmp-community\t= %s\n" % netbox.read_only
    config = config + "\ttarget-type\t= %s\n" % netbox.sysname
    config = config + "\tshort-desc\t= \"%s\"\n\n" % shortdesc

    return config


def create_container(netbox, targetoids):
    """ Create container object and fill it """
    container = RRDcontainer(netbox.sysname, netbox.id)
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
    filehandle = open(join(path_to_config, TARGETFILENAME), 'w')
    filehandle.write("\n".join(targets))
    filehandle.close()


class RRDcontainer:
    """
    path: if config is located lower than module
    filename: name of target rrd-file
    netboxid: id of netbox in database
    """

    def __init__(self, filename, netboxid, path="", key=None, value=None,
                 step=300, speed=None):
        self.filename = filename
        self.netboxid = netboxid
        self.path = path
        self.key = key
        self.value = value
        self.step = step
        self.datasources = []
        self.speed = speed
