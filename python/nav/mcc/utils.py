"""
Contains help functions for the various config creation modules.
"""
from functools import wraps
from time import time
import re
import sys
import logging
import os
from collections import namedtuple
from nav.errors import GeneralException
from os.path import join, abspath
from subprocess import Popen, PIPE
from IPy import IP

from nav import path
from nav.db import getConnection
from nav.models.oid import SnmpOid
from django.db.models import Q

LOGGER = logging.getLogger(__name__)
TARGETFILENAME = 'navTargets'


class NoConfigRootException(GeneralException):
    "Could not find Crickets configroot ($gConfigRoot in cricket-conf.pl)"


class Memoize(object):
    """Basic memoization"""
    def __init__(self, function):
        self.function = function
        self.memoized = {}

    def __call__(self, *args):
        try:
            return self.memoized[args]
        except KeyError:
            self.memoized[args] = self.function(*args)
            return self.memoized[args]


def timed(f):
    """Decorator to time execution of functions"""
    @wraps(f)
    def wrapper(*args, **kwds):
        """Decorator"""
        start = time()
        result = f(*args, **kwds)
        elapsed = time() - start
        LOGGER.debug("%s took %f seconds to finish" % (f.__name__, elapsed))
        return result
    return wrapper


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
    perl = Popen(("/usr/bin/env", "perl"), stdin=PIPE, stdout=PIPE, close_fds=True)

    perl.stdin.write(cricket_config)
    perl.stdin.write("""\nprint "$gConfigRoot\\n";\n""")
    perl.stdin.close()

    configroot = perl.stdout.readline().strip()
    perl.wait()

    if not configroot:
        raise NoConfigRootException

    LOGGER.debug("Found configroot to be %s", configroot)
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
    except IOError, error:
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
    except IOError, error:
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


def check_file_existence(datadir, sysname):
    """
    Check if rrd-file exists. If not, delete tuple from database.
    """

    sysname = sysname.lower()
    if not sysname.endswith('.rrd'):
        sysname = sysname + '.rrd'
    filename = join(datadir, sysname)

    if not os.path.exists(filename):
        LOGGER.info("File %s does not exist, deleting tuple from database"
                    % filename)

        conn = getConnection('default')
        cur = conn.cursor()
        sql = """DELETE FROM rrd_file
                WHERE path = %s AND
                lower(filename) = %s """
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

    replacements = {
        "\"": "&quot;",
        "{": "&#123;",
        "}": "&#125;",
        "\n": " "
    }

    for key, value in replacements.items():
        string = string.replace(key, value)

    return string


def find_and_remove_old_config(configpath, dirs):
    """Find dirs in configpath not in dirs and remove config from them"""
    subdirs = find_subdirs(configpath)
    remove_old_config(list(set(subdirs) - set(dirs)))


def find_subdirs(fullpath):
    """Find sub directories in path"""
    subdirs = []
    for directory in os.listdir(fullpath):
        subdir = join(fullpath, directory)
        if os.path.isdir(subdir):
            subdirs.append(subdir)

    return subdirs


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
            except IOError, error:
                LOGGER.error("Could not remove %s: %s" % (directory, error))
        else:
            LOGGER.info("%s is not empty, leaving it alone." % directory)


def find_target_oids(netbox, oidlist):
    """ Find the oids this netbox answers to that also exist in the
        cricket config files. """
    return SnmpOid.objects.filter(netboxsnmpoid__netbox=netbox).filter(
        Q(oid_source='Cricket') | Q(oid_key__iexact='sysuptime')).filter(
        snmp_oid__in=oidlist).order_by('oid_key')


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


def format_ip_address(ip):
    """Return ip-address as string to be used as snmp-host argument"""
    try:
        address = IP(ip)
        if address.version() == 6:
            return "[%s]" % ip
        else:
            return str(ip)
    except ValueError, error:
        LOGGER.error("Error formatting %s: %s" % (ip, error))
        return ip


class RRDcontainer:
    """
    path: if config is located lower than module
    filename: name of target rrd-file
    netboxid: id of netbox in database
    """

    def __init__(self, filename, netboxid, path="", key=None, value=None,
                 step=300, speed=None, category=None):
        self.filename = filename.lower()
        self.netboxid = netboxid
        self.path = path
        self.key = key
        self.value = value
        self.step = step
        self.datasources = []
        self.speed = speed
        self.category = category

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


# pylint: disable=C0103
Datasource = namedtuple('Datasource', 'name descr dstype unit')
