"""
Creates config for all netbox sensors
"""

import logging
import os

from nav.models.manage import Netbox
from nav.mcc import utils
from os.path import join, isdir

LOGGER = logging.getLogger('mcc.sensors')


def make_config(config):
    """
    This method is required and is run by mcc
    """

    dirname = "sensors"

    # Get path to cricket-config
    configfile = config.get('mcc', 'configfile')
    configroot = utils.get_configroot(configfile)
    if not configroot:
        LOGGER.error("Could not find configroot in %s, exiting."
                     % config.get('mcc', 'configfile'))
        return False

    fullpath = join(configroot, dirname)
    LOGGER.info("Creating config for %s in %s" % (dirname, fullpath))

    for netbox in Netbox.objects.all():
        path = join(fullpath, netbox.sysname)
        output = create_config_string(netbox)
        if output:
            write_output_to_file(path, output)

    return True


def create_config_string(netbox):
    """
    Create sensor config for a netbox and return it as a string
    """

    sensors = netbox.get_sensors()
    if not sensors:
        return

    sensors = sorted(sensors, key=lambda sensor: sensor.internal_name)
    counter = len(sensors)

    LOGGER.info("Creating config for %s" % netbox.sysname)

    output = "target --default--\n"
    output += "\tsnmp-host\t= %s\n" % netbox.ip
    output += "\tsnmp-community\t= %s\n" % netbox.read_only
    output += "\ttarget-type\t= sensor\n\n"

    fmt = "\t%s\t= \"%s\"\t\n"

    for sensor in sensors:
        output += "target \"%s\"\n" % sensor.id
        output += fmt % ("display-name", sensor.internal_name)
        output += fmt % ("oid", sensor.oid)
        output += fmt % ("legend", sensor.name)
        output += fmt % ("short-desc", sensor.human_readable)
        output += fmt % ("yaxis", format_yaxis(sensor))
        output += fmt % ("order", counter)
        output += "\n"

        counter = counter - 1

    return output


def format_yaxis(sensor):
    """ Format yaxis description """

    if sensor.data_scale:
        return "%s%s" % (sensor.data_scale, sensor.unit_of_measurement)
    else:
        return sensor.unit_of_measurement


def write_output_to_file(path, output):
    """ Write output to file """

    if not isdir(path):
        try:
            os.mkdir(path, 0755)
        except OSError, error:
            LOGGER.error(error)

    try:
        targetfile = open(join(path, "navTargets"), 'w')
        targetfile.write(output)
        targetfile.close()
    except IOError, error:
        LOGGER.error("Could not write to file: %s" % error)
