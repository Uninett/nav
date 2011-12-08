""" Helper functions for handling database actions """
import logging

from os.path import join
from shutil import move

from nav.models.manage import Netbox
from nav.models.rrd import RrdFile, RrdDataSource
from nav.models.event import Subsystem

from django.db import transaction

OCTET_COUNTERS = ['ifHCInOctets', 'ifHCOutOctets', 'ifInOctets', 'ifOutOctets']
LOGGER = logging.getLogger(__name__)

@transaction.commit_on_success
def updatedb(datadir, containers):
    """
    Update database with information given from a module in form of a list of
    objects containing information about each rrd file.
    """

    for container in containers:
        datapath = datadir
        if container.path:
            datapath = join(datapath, container.path)

        filename = fix_filename(container.filename)
        path_to_file = join(datapath, filename)
        netbox = Netbox.objects.get(id=container.netboxid)

        # Check for new filename:
        # 1. If target (path + filename) exists, then update database.
        # 2. If target does not exist and we have a key/value pair,
        #    check if key/value pair exists in database
        # 2.1 If it does, update path and filename with new values on id where
        #     key/value pair exists. Move rrd-file to new path and filename in
        #     filesystem (keep a copy?).
        # 2.2 If it does not exist, insert new data.
        # 3. If target does not exist and we do not have a key/value pair,
        #    insert new data.

        # 1
        try:
            rrdfile = RrdFile.objects.get(path=datapath, filename=filename)
            LOGGER.debug("Target %s exists in database." % path_to_file)
            update_rrdfile(rrdfile, netbox, datapath, container)

        except RrdFile.DoesNotExist:
            # 2
            key, value = get_key_value(container)
            if key and value:
                try:
                    # 2.1
                    rrdfile = RrdFile.objects.get(key=key, value=value)
                    move_file(join(rrdfile.path, rrdfile.filename),
                              path_to_file)
                    update_rrdfile(rrdfile, netbox, datapath, container)
                except RrdFile.DoesNotExist:
                    # 2.2
                    insert_rrdfile(datapath, filename, container, netbox)

            else:
                # 3
                insert_rrdfile(datapath, filename, container, netbox)


def fix_filename(filename):
    """ Make sure filename is correct  """
    if not filename.endswith('.rrd'):
        filename = filename + '.rrd'

    return filename


def update_rrdfile(rrdfile, netbox, path_to_rrd, container):
    """ Update database with new info """
    key, value = get_key_value(container)

    rrdfile.path = path_to_rrd
    rrdfile.filename = fix_filename(container.filename)
    rrdfile.netbox = netbox
    rrdfile.key = key
    rrdfile.value = value

    # We don't update the datasources as the database is the source of
    # the datasources. Somewhere in the future there will exist an
    # option to expand the rrd-files with more datasources
    # However, we update the threshold metainfo
    update_datasource_metainfo(container, rrdfile)

    # Special case: if the number of datasources is 0, we insert
    # what we have.
    if not rrdfile.rrddatasource_set.all():
        insert_datasources(container, rrdfile)

    rrdfile.save()


def insert_rrdfile(datapath, filename, container, netbox):
    """ Create a new tuple in the database """
    subsystem = Subsystem.objects.get(name='cricket')
    key, value = get_key_value(container)

    LOGGER.info("Inserting target %s in database", join(datapath, filename))
    rrdfile = RrdFile(
        path=datapath,
        filename=filename,
        step=container.step,
        subsystem=subsystem,
        netbox=netbox,
        key=key,
        value=value)

    rrdfile.save()
    insert_datasources(container, rrdfile)


def get_key_value(container):
    """ Return key/value as a tuple """
    key = None
    value = None

    if hasattr(container, 'key'):
        key = container.key
        value = container.value

    return (key, str(value))


def is_octet_counter(datasource):
    """ Is the datasource an octet counter """
    return datasource in OCTET_COUNTERS


def insert_datasources(container, rrdfile):
    """ Insert this datasource in the database """
    LOGGER.debug("Inserting datasources for %s" % container.filename)
    for datasource in container.datasources:
        units = None
        speed = None

        # If this is an octet counter on an interface,
        # set max value
        if is_octet_counter(datasource[1]) and container.speed > 0:
            units = "bytes"
            speed = str(convert_megabit_to_bytes(container.speed))

        datasource = RrdDataSource(rrd_file=rrdfile, name=datasource[0],
                                   description=datasource[1],
                                   type=datasource[2],
                                   units=units, max=speed,
                                   threshold_state=None,
                                   delimiter=None)
        datasource.save()


def update_datasource_metainfo(container, rrdfile):
    """ Update datasourcetuple regarding this container """
    if not container.speed > 0:
        return

    LOGGER.debug("Updating datasource for %s" % container.filename)
    has_counter_sources = any(is_octet_counter(descr)
                              for name, descr, dstype in container.datasources)

    if has_counter_sources:
        maxspeed = str(convert_megabit_to_bytes(container.speed))
        sources = rrdfile.rrddatasource_set.filter(
            description__in=OCTET_COUNTERS)
        needs_update = sources.exclude(units__isnull=False, units='bytes',
                                       max__isnull=False, max=maxspeed)
        needs_update.update(units='bytes', max=maxspeed)


def move_file(source, destination):
    """
    Move file to new place. If it does not exist, we assume it's ok and
    keep the change in the database
    """
    try:
        LOGGER.info("Renaming %s to %s" % (source, destination))
        move(source, destination)
    except IOError, ioerror:
        # If file did not exist, accept that and continue
        if ioerror.errno == 2:
            LOGGER.info("%s did not exist.", source)
        else:
            LOGGER.error("Exception when moving file %s: %s" \
                         % (source, ioerror))
    except Exception, error:
        LOGGER.error("Exception when moving file %s: %s" % (source, error))


def convert_megabit_to_bytes(mbit):
    """ Convert mbit to bytes """
    return int((1024 ** 2) * mbit / 8)
