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
            key, value, category = get_key_value(container)
            if key and value and category:
                try:
                    # 2.1
                    rrdfile = RrdFile.objects.get(key=key, value=value,
                                                  category=category)
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
        filename += '.rrd'

    return filename


def update_rrdfile(rrdfile, netbox, path_to_rrd, container):
    """ Update database with new info """
    key, value, category = get_key_value(container)

    rrdfile.path = path_to_rrd
    rrdfile.filename = fix_filename(container.filename)
    rrdfile.netbox = netbox
    rrdfile.key = key
    rrdfile.value = value
    rrdfile.category = category

    update_maxspeed(container, rrdfile)
    update_datasources(container, rrdfile)

    # Special case: if the number of datasources is 0, we insert
    # what we have.
    if not rrdfile.rrddatasource_set.all():
        insert_datasources(container, rrdfile)

    rrdfile.save()


def insert_rrdfile(datapath, filename, container, netbox):
    """ Create a new tuple in the database """
    subsystem = Subsystem.objects.get(name='cricket')
    key, value, category = get_key_value(container)

    LOGGER.info("Inserting target %s in database", join(datapath, filename))
    rrdfile = RrdFile(
        path=datapath,
        filename=filename,
        step=container.step,
        subsystem=subsystem,
        netbox=netbox,
        key=key,
        value=value,
        category=category)

    rrdfile.save()
    insert_datasources(container, rrdfile)


def get_key_value(container):
    """ Return key/value and category as a tuple """
    key = None
    value = None
    category = None

    if hasattr(container, 'key'):
        key = container.key
        value = container.value
        category = container.category

    return key, str(value), category


def is_octet_counter(datasource):
    """ Is the datasource an octet counter """
    return datasource in OCTET_COUNTERS


def insert_datasources(container, rrdfile):
    """ Insert this datasource in the database """
    LOGGER.debug("Inserting datasources for %s" % container.filename)
    for datasource in container.datasources:
        speed = None

        # If this is an octet counter on an interface,
        # set max value
        if is_octet_counter(datasource.descr) and container.speed > 0:
            speed = str(convert_megabit_to_bytes(container.speed))

        create_datasource(datasource, rrdfile, speed)


def update_datasources(container, rrdfile):
    """Update datasources based on container data

    For each datasource we
    - Update database if datasource with same name exists
    - Insert new if datasource name does not exist
    Finally we remove those who did not exist on the container
    """
    def is_equal(rrdds, datasource):
        """Is the rrd_datasource equal to container datasource?"""
        return rrdds.units == datasource.unit and \
            rrdds.type == datasource.dstype and \
            rrdds.description == datasource.descr


    existing = []
    for datasource in container.datasources:
        try:
            rrdds = rrdfile.rrddatasource_set.get(name=datasource.name)
            if not is_equal(rrdds, datasource):
                rrdds.units = datasource.unit
                rrdds.type = datasource.dstype
                rrdds.description = datasource.descr
                rrdds.save()
                LOGGER.debug(
                    'Updating datasource %s for %s' % (datasource.name,
                        container.filename))
            existing.append(rrdds)
        except RrdDataSource.DoesNotExist:
            existing.append(
                create_datasource(datasource, rrdfile, container.speed))

    rrds_to_delete = rrdfile.rrddatasource_set.exclude(
        id__in=[x.id for x in existing])

    if len(rrds_to_delete) > 0:
        LOGGER.info('Deleting %s' % (rrds_to_delete))
        rrds_to_delete.delete()


def create_datasource(datasource, rrdfile, speed):
    """Create a new rrd_datasource tuple"""

    LOGGER.info('Creating new datasource for %s - %s:%s' % (
        rrdfile, datasource.name, datasource.descr))
    rrdds = RrdDataSource(rrd_file=rrdfile, name=datasource.name,
                               description=datasource.descr,
                               type=datasource.dstype,
                               units=datasource.unit, max=speed,
                               threshold_state=None,
                               delimiter=None)
    rrdds.save()
    return rrdds


def update_maxspeed(container, rrdfile):
    """ Update datasourcetuple regarding this container """
    if not container.speed > 0:
        return

    LOGGER.debug("Updating maxspeed for %s" % container.filename)
    has_counter_sources = any(is_octet_counter(ds.descr)
                              for ds in container.datasources)

    if has_counter_sources:
        maxspeed = str(convert_megabit_to_bytes(container.speed))
        sources = rrdfile.rrddatasource_set.filter(
            description__in=OCTET_COUNTERS)
        needs_update = sources.exclude(max__isnull=False, max=maxspeed)
        needs_update.update(max=maxspeed)


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
            LOGGER.info("File %s did not exist.", source)
        else:
            LOGGER.error("Exception when moving file %s: %s" \
                         % (source, ioerror))
    except Exception, error:
        LOGGER.error("Exception when moving file %s: %s" % (source, error))


def convert_megabit_to_bytes(mbit):
    """ Convert mbit to bytes """
    return int((1024 ** 2) * mbit / 8)
