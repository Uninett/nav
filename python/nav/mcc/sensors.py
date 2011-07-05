"""
Creates config for all netbox sensors
"""

import logging
import os

from nav.models.manage import Netbox
from nav.mcc import utils
from os.path import join, isdir

LOGGER = logging.getLogger('mcc.sensors')


def make_config(globalconfig):
    """
    This method is required and is run by mcc
    """

    dirname = "sensors"

    # Get path to cricket-config
    configfile = globalconfig.get('mcc', 'configfile')
    configroot = utils.get_configroot(configfile)
    if not configroot:
        LOGGER.error("Could not find configroot in %s, exiting."
                     % globalconfig.get('mcc', 'configfile'))
        return False

    path_to_directory = join(configroot, dirname)
    LOGGER.info("Creating config for %s in %s" % (dirname, path_to_directory))

    for netbox in Netbox.objects.all():
        containers = create_netbox_config(netbox, path_to_directory)
        if containers:
            utils.updatedb(path_to_directory, containers)

    return True


def create_netbox_config(netbox, path_to_directory):
    """
    Create config for a netbox
    """

    sensors = netbox.get_sensors()
    if not sensors:
        return

    LOGGER.info("Creating config for %s" % netbox.sysname)

    config = "target --default--\n"
    config += "\tsnmp-host\t= %s\n" % netbox.ip
    config += "\tsnmp-community\t= %s\n" % netbox.read_only
    config += "\ttarget-type\t= sensor\n\n"

    sensors = sorted(sensors, key=lambda sensor: sensor.internal_name)
    counter = len(sensors)
    containers = []

    for sensor in sensors:
        config += create_sensor_config(sensor, counter)
        counter = counter - 1
        containers.append(create_container(sensor))

    path_to_config = join(path_to_directory, netbox.sysname)
    write_config_to_file(path_to_config, config)

    return containers


def create_sensor_config(sensor, counter):
    """ Create config for a sensor """

    fmt = "\t%s\t= \"%s\"\t\n"

    sensorconfig = "target \"%s\"\n" % sensor.id
    sensorconfig += fmt % ("display-name", sensor.internal_name)
    sensorconfig += fmt % ("oid", sensor.oid)
    sensorconfig += fmt % ("legend", sensor.name)
    sensorconfig += fmt % ("short-desc", sensor.human_readable)
    sensorconfig += fmt % ("yaxis", format_yaxis(sensor))
    sensorconfig += fmt % ("order", counter)
    sensorconfig += "\n"

    return sensorconfig


def create_container(sensor):
    """ Create container for storing in database """
    container = utils.RRDcontainer(str(sensor.id) + ".rrd", sensor.netbox.id,
                                   sensor.netbox.sysname)
    container.datasources = [("ds0", "sensor", "GAUGE")]
    return container


def format_yaxis(sensor):
    """ Format yaxis description """

    if sensor.data_scale:
        return "%s%s" % (sensor.data_scale, sensor.unit_of_measurement)
    else:
        return sensor.unit_of_measurement


def write_config_to_file(path, config):
    """ Write output to file """

    if not isdir(path):
        try:
            os.mkdir(path, 0755)
        except OSError, error:
            LOGGER.error(error)

    try:
        targetfile = open(join(path, "navTargets"), 'w')
        targetfile.write(config)
        targetfile.close()
    except IOError, error:
        LOGGER.error("Could not write to file: %s" % error)
