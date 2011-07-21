"""
Contains help functions for the various config creation modules.
"""
import ConfigParser
import re
import sys
import logging
import os
from nav.errors import GeneralException
from os.path import join, abspath
from shutil import move
from subprocess import Popen, PIPE

from nav import path
from nav.db import getConnection

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


def updatedb(datadir, containers):
    """
    Update database with information given from a module in form of a list of
    objects containing information about each rrd file.
    """
    conn = getConnection('default')
    c = conn.cursor()
    octet_counters = ['ifHCInOctets', 'ifHCOutOctets', 'ifInOctets',
                      'ifOutOctets']

    def is_octet_counter(ds):
        return ds in octet_counters

    def insert_datasources(container, rrd_fileid):
        LOGGER.debug("Inserting datasources for %s" % container.filename)
        for datasource in container.datasources:
            # TODO: Make a general way of adding units and max
            units = None
            speed = None

            dssql = """
            INSERT INTO rrd_datasource
            (rrd_fileid, name, descr, dstype, units, max)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            # If this is an octet counter on an interface,
            # set max value
            if is_octet_counter(datasource[1]) and container.speed > 0:
                units = "bytes"
                speed = str(convert_Mbit_to_bytes(container.speed))

            c.execute(dssql, (rrd_fileid, datasource[0], datasource[1],
                              datasource[2], units, speed))

    def update_datasource_metainfo(container, rrd_fileid):
        LOGGER.debug("Updating datasource for %s" % container.filename)
        counter_sources = [ds[1] for ds in container.datasources
                           if is_octet_counter(ds[1]) and container.speed > 0]

        if counter_sources:
            c.execute(
                """UPDATE rrd_datasource
                   SET units = %(units)s, max = %(max_speed)s
                   WHERE rrd_fileid = %(rrd_fileid)s
                     AND descr IN %(octet_counters)s
                     AND (units <> %(units)s OR max <> %(max_speed)s)""",
                {'units': 'bytes',
                 'max_speed': str(convert_Mbit_to_bytes(container.speed)),
                 'rrd_fileid': rrd_fileid,
                 'octet_counters': tuple(octet_counters),
                 })


    for container in containers:
        datapath = datadir
        if container.path:
            datapath = join(datapath, container.path)

        filename = container.filename
        if not filename.endswith('.rrd'):
            filename = filename + '.rrd'

        # If key attribute is set, use those. Else fill in blanks.
        if hasattr(container, 'key'):
            key = container.key
            value = container.value
        else:
            key = None
            value = None

        # Check for new filename:
        # 1. If target (path + filename) exists, then update tuple.
        # 2. If target does not exist and we have a key/value pair,
        #    check if key/value pair exists in database
        # 2.1 If it does, update path and filename with new values on id where
        #     key/value pair exists. Move rrd-file to new path and filename in
        #     filesystem (keep a copy?).
        # 2.2 If it does not exist, insert new data.
        # 3. If target does not exist and we do not have a key/value pair,
        #    insert new data.

        # Check if this target already exists
        verify = """
        SELECT * FROM rrd_file WHERE path = %s AND filename = %s
        """
        c.execute(verify, (datapath, filename))
        if c.rowcount > 0:
            # This target already exists, update it.
            LOGGER.debug("Target %s exists in database."
                        % join(datapath, filename))
            rrd_fileid = c.fetchone()[0]

            sql = """
            UPDATE rrd_file
            SET netboxid = %s, key = %s, value = %s
            WHERE rrd_fileid = %s
            """

            LOGGER.debug(sql % (container.netboxid, key, value, rrd_fileid))
            c.execute(sql, (container.netboxid, key, value, rrd_fileid))

            # We don't update the datasources as the database is the source of
            # the datasources. Somewhere in the future there will exist an
            # option to expand the rrd-files with more datasources
            # However, we update the threshold metainfo
            update_datasource_metainfo(container, rrd_fileid)

            # Special case: if the number of datasources is 0, we insert
            # what we have.
            sql = """
            SELECT * FROM rrd_datasource WHERE rrd_fileid = %s
            """
            c.execute(sql, (rrd_fileid, ))

            if c.rowcount == 0:
                insert_datasources(container, rrd_fileid)


        elif key and value:
            # Check for key/value pair
            keyvalueq = """
            SELECT rrd_fileid, path, filename
            FROM rrd_file
            WHERE key=%s AND value=%s"""

            c.execute(keyvalueq, (key, str(value)))
            if c.rowcount > 0:
                rrd_fileid, dbpath, dbfilename = c.fetchone()

                # Move file to new place. If it does not exist, we assume it's
                # ok and keep the change in the database
                try:
                    LOGGER.info("Renaming %s to %s" % (
                        join(dbpath, dbfilename), join(datapath, filename)))
                    move(join(dbpath, dbfilename),
                         join(datapath, filename))
                except IOError, ioerror:
                    # If file did not exist, accept that and continue
                    if ioerror.errno == 2:
                        LOGGER.info("%s did not exist.",
                                    join(dbpath, dbfilename))
                    else:
                        LOGGER.error("Exception when moving file %s: %s" \
                                         % (join(dbpath, dbfilename), ioerror))
                        continue
                except Exception, e:
                    LOGGER.error("Exception when moving file %s: %s" \
                                     % (join(dbpath, dbfilename), e))
                    continue


                sql = """
                UPDATE rrd_file
                SET netboxid = %s, path = %s, filename = %s
                WHERE rrd_fileid = %s
                """
                c.execute(sql, (container.netboxid, datapath, filename,
                                rrd_fileid))

                # Special case: if the number of datasources is 0, we insert
                # what we have.
                sql = """
                SELECT * FROM rrd_datasource WHERE rrd_fileid = %s
                """
                c.execute(sql, (rrd_fileid, ))

                if c.rowcount == 0:
                    insert_datasources(container, rrd_fileid)

            else:
                # Target did not exist in database. Insert file and
                # datasources.  Get nextval primary key
                LOGGER.info("Inserting target %s in database"
                            % (join(datapath, filename)))
                nextvalq = "SELECT nextval('rrd_file_rrd_fileid_seq')"
                c.execute(nextvalq)
                nextval = c.fetchone()[0]

                sql = """
                INSERT INTO rrd_file
                (rrd_fileid, path, filename, step, subsystem, netboxid, key,
                value)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                c.execute(sql, (nextval, datapath, filename, container.step,
                            'cricket', container.netboxid, key, value))

                # Each containter contains a list of tuples of
                # datasources. It's up to each module to ensure that these are
                # correct.
                insert_datasources(container, nextval)

        else:
            # Target did not exist in database. Insert file and datasources.
            # Get nextval primary key
            LOGGER.info("Inserting target %s in database"
                        % (join(datapath, filename)))
            nextvalq = "SELECT nextval('rrd_file_rrd_fileid_seq')"
            c.execute(nextvalq)
            nextval = c.fetchone()[0]

            sql = """
            INSERT INTO rrd_file
            (rrd_fileid, path, filename, step, subsystem, netboxid, key, value)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            c.execute(sql, (nextval, datapath, filename, container.step,
                            'cricket', container.netboxid, key, value))

            # Each container contains a list of tuples of datasources. It's up
            # to each module to ensure that these are correct.
            insert_datasources(container, nextval)

        conn.commit()


def compare_datasources(path, filename, targetoids):
    """
    Compare the datasources from the database with the ones found in file
    (targetoids). If the number in database is larger than or equal to the
    number in file, use database as source for the datasources. Else expand
    rrd-file and update database (not implemented)
    """

    oids = targetoids

    conn = getConnection('default')
    c = conn.cursor()

    if not filename.endswith('.rrd'):
        filename = filename + '.rrd'

    numdsq = """SELECT name, descr FROM rrd_file
    JOIN rrd_datasource USING (rrd_fileid)
    WHERE path = %s AND filename = %s
    ORDER BY name
    """
    c.execute(numdsq, (path, filename))
    if c.rowcount > 0:
        LOGGER.debug("Found %s datasources in database (%s in file)" \
                     % (c.rowcount, len(targetoids)))
        if c.rowcount >= len(targetoids):
            LOGGER.debug(">= Using database as base for targetoids")
            # There are more or equal number of datasources in the database
            # Reset targetoids and fill it from database
            oids = []
            for name, descr in c.fetchall():
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
        c = conn.cursor()
        sql = """DELETE FROM rrd_file WHERE path = %s AND filename = %s """
        c.execute(sql, (datadir, sysname))

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
    except Exception, e:
        LOGGER.error("Could not encode %s to latin-1: %s" % (unicode_object,
                                                             e))
        return unicode_object

    return encoded_string


def encode_and_escape(input):
    """
    Encode and escape object to make it presentable for
    the Cricket webpage.
    """
    if isinstance(input, unicode):
        input = convert_unicode_to_latin1(input)
    input = input.replace("\"", "&quot;")

    return input


def remove_old_config(dirs):
    """
    Input is a list of directories. Remove those if they contain nothing but
    the mccTargets file. If they contain more, remove only the mccTargets file.
    """

    for dir in dirs:
        LOGGER.debug("Checking %s for removal." % dir)
        files = os.listdir(dir)
        try:
            files.remove(TARGETFILENAME)
            os.remove(join(dir, TARGETFILENAME))
        except ValueError, e:
            LOGGER.error("Could not find %s in %s" % (TARGETFILENAME, dir))

        if not len(files):
            # Remove dir if it is empty
            try:
                os.rmdir(dir)
                LOGGER.info("%s removed." % dir)
            except Exception, e:
                LOGGER.error("Could not remove %s: %s" % (dir, e))
        else:
            LOGGER.info("%s is not empty, leaving it alone." % dir)


def convert_Mbit_to_bytes(mbit):
    return int((1024 ** 2) * mbit / 8)


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
