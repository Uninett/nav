"""
Contains help functions for the various config creation modules.
"""
import ConfigParser
import re
import sys
import logging
import os
from os.path import join, abspath

from nav import path
from nav.db import getConnection

logger = logging.getLogger(__name__)
TARGETFILENAME = 'navTargets'

def start_config_creation(modules, config):    
    # Start modules
    # Check if directory exists, if not create it.
    # Pass control to module

    for module in modules:
        logger.info("Starting module %s" % module)
        mod = __import__(module, globals(), locals(), ['make_config'])
        result = mod.make_config(config)
        if not result:
            logger.error("Module %s reports error creating config." % module)
        else:
            logger.info("Module %s successfully done." % module)

    logger.info("Done creating config")


def get_configroot(configfile):
    """ Get path for configroot from cricket-conf.pl """
    comment = re.compile('#')
    match = re.compile('gconfigroot\s*=\s*"(.*)"', re.I)
    
    f = open(configfile, 'r')
    for line in f:
        if comment.match(line):
            continue
        m = match.search(line)
        if m:
            logger.info("Found configroot to be %s" % m.groups()[0])
            return m.groups()[0]

    return False

def parse_views():
    """ Parse configuration file with view definitions """
    views = {}
    
    try:
        f = open(join(path.sysconfdir, "cricket-views.conf"))
    except Exception, e:
        logger.error(e)
        return False

    for line in f:
        if line.startswith("view"):
            key, value = line.split(':')
            key = re.sub("view\s+", "", key)
            values = [x.strip() for x in value.split()]
            logger.debug("view: %s -> %s" % (key, values))
            views[key] = values

    return views

def get_toplevel_oids(path):
    """ Search all files in path for oids regarding Cricket-configuration """
    oidlist = []
    match = re.compile("OID\s+(\w+)\s+(\S+)")

    try:
        f = open(join(path, 'Defaults'), 'r')
    except Exception, e:
        logger.error(e)
        sys.exit()
                
    for line in f:
        m = match.search(line)
        if m:
            logger.debug("Found oid %s - %s"
                        % (m.groups()[0], m.groups()[1]))
            oidlist.append(m.groups()[1])

    return set(oidlist)

    
def get_datadir(path):
    """
    The datadir contains information about where the rrd-files are stored. This
    information must be available in the cricket-config/Defaults file.
    """
    match = re.compile("datadir\s+=\s+(\S+)", re.I)
    filename = "Defaults"
    datadir = ""
    
    try:
        f = open(join(path, filename), 'r')
    except Exception, e:
        logger.error("Error opening %s: %s" % (join(path, filename), e[1]))
        sys.exit()
                
    for line in f:
        m = match.search(line)
        if m:
            datadir = m.groups()[0]
            #----------------------------------------------------------------- 
            # %auto-base% is used in Cricket as a variable pointing to the 
            # base directory for the cricket-config
            datadir = re.sub("%auto-base%", path, datadir)
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
            logger.debug("Target %s exists in database."
                        % join(datapath, filename))
            rrd_fileid = c.fetchone()[0]
            
            sql = """
            UPDATE rrd_file
            SET netboxid = %s, key = %s, value = %s
            WHERE rrd_fileid = %s
            """

            logger.debug(sql % (container.netboxid, key, value, rrd_fileid))
            c.execute(sql, (container.netboxid, key, value, rrd_fileid))

            # We don't update the datasources as the database is the source of
            # the datasources. Somewhere in the future there will exist an
            # option to expand the rrd-files with more datasources

        elif key and value:
            # Check for key/value pair
            keyvalueq = """
            SELECT rrd_fileid, path, filename
            FROM rrd_file
            WHERE key=%s AND value=%s"""

            c.execute(keyvalueq, (key, str(value)))
            if c.rowcount > 0:
                rrd_fileid, dbpath, dbfilename = c.fetchone()
                
                sql = """
                UPDATE rrd_file
                SET netboxid = %s, path = %s, filename = %s
                WHERE rrd_fileid = %s
                """
                c.execute(sql, (container.netboxid, datapath, filename,
                                rrd_fileid))

                # Move file to new place. If it does not exist, we assume it's
                # ok and keep the change in the database
                try:
                    logger.info("Renaming %s to %s" % (
                        join(dbpath, dbfilename), join(datapath, filename)))
                    os.rename(join(dbpath, dbfilename),
                              join(datapath, filename))
                except Exception, e:
                    logger.error("Exception when moving file %s: %s" \
                          % (join(dbpath, dbfilename), e))
                    
            else:
                # Target did not exist in database. Insert file and
                # datasources.  Get nextval primary key
                logger.info("Inserting target %s in database"
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
                for datasource in container.datasources:
                    dssql = """
                    INSERT INTO rrd_datasource
                    (rrd_fileid, name, descr, dstype)
                    VALUES (%s, %s, %s, %s)
                    """

                    c.execute(dssql, (nextval, datasource[0], datasource[1],
                                      datasource[2]))

        else:
            # Target did not exist in database. Insert file and datasources.
            # Get nextval primary key
            logger.info("Inserting target %s in database"
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
            for datasource in container.datasources:
                dssql = """
                INSERT INTO rrd_datasource
                (rrd_fileid, name, descr, dstype)
                VALUES (%s, %s, %s, %s)
                """

                c.execute(dssql, (nextval, datasource[0], datasource[1],
                                  datasource[2]))

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
        logger.debug("Found %s datasources in database (%s in file)" \
                     % (c.rowcount, len(targetoids)))
        if c.rowcount >= len(targetoids):
            logger.debug(">= Using database as base for targetoids")
            # There are more or equal number of datasources in the database
            # Reset targetoids and fill it from database
            oids = []
            for name, descr in c.fetchall():
                logger.debug("Appending %s as %s" % (descr, name))
                oids.append(descr)
        else:
            # There are less datasources in the database
            # Find a way to expand the file with the missing datasources...
            logger.debug("< Must expand rrd-file (not implemented)")

    return oids
            

def check_file_existence(datadir, sysname):
    """
    Check if rrd-file exists. If not, delete tuple from database.
    """

    if not sysname.endswith('.rrd'):
        sysname = sysname + '.rrd'
    filename = join(datadir, sysname)

    if not os.path.exists(filename):
        logger.info("File %s does not exist, deleting tuple from database" \
                    % filename)

        conn = getConnection('default')
        c = conn.cursor()
        sql = """DELETE FROM rrd_file WHERE path = %s AND filename = %s """
        c.execute(sql, (datadir, sysname))

        conn.commit()
        return False

    logger.info('file %s existed' % filename)
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
    Decode a unicode object to a latin-1 string  
    """
    
    # Cricket always displays latin-1. Database returns data as unicode objects. 
    # Encode it to display correctly.
    try:
        encoded_string = unicode_object.encode('latin-1')
    except Exception, e:
        logger.error("Could not encode %s to latin-1: %s" % (unicode_object, e))
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
    input = re.escape(input)
    
    return input


def remove_old_config(dirs):
    """
    Input is a list of directories. Remove those if they contain nothing but
    the mccTargets file. If they contain more, remove only the mccTargets file.
    """

    for dir in dirs:
        logger.debug("Checking %s for removal." % dir)
        files = os.listdir(dir)
        try:
            files.remove(TARGETFILENAME)
            os.remove(join(dir, TARGETFILENAME))
        except ValueError, e:
            logger.error("Could not find %s in %s" % (TARGETFILENAME, dir))

        if not len(files):
            # Remove dir if it is empty
            try:
                os.rmdir(dir)
                logger.info("%s removed." % dir)
            except Exception, e:
                logger.error("Could not remove %s: %s" % (dir, e))
        else:
            logger.info("%s is not empty, leaving it alone." % dir)


class RRDcontainer:
    """
    path: if config is located lower than module
    filename: name of target rrd-file
    netboxid: id of netbox in database
    """
    def __init__(self, filename, netboxid, path="", key=None, value=None,
                 step=300):
        self.filename = filename
        self.netboxid = netboxid
        self.path = path
        self.key = key
        self.value = value
        self.step = step
        self.datasources = []
    
