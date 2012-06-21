#!/usr/bin/env python
# pylint: disable=C0111

import os
import re
import rrdtool
from subprocess import Popen, PIPE
from xml.dom import minidom

from nav import natsort
from nav.errors import GeneralException


TMPPATH = '/tmp' # Path for storing temporary files



class FileNotFoundError(GeneralException):
    "File not found"
    pass


class FileNotWritableError(GeneralException):
    "File not writable"
    pass


class FileNotRRDError(GeneralException):
    "File does not seem to be an rrd-file"
    pass


# pylint: disable=R0912,R0914,W0612
def add_datasource(rrd_file):
    """ Takes as input the full path to an rrdfile and tries to add a
    datasource to that file. The default values of the heartbeat, type and so
    on are used.

    Returns output from rrdrestore.

    NB: Works for RRDtool 1.2.x up to 1.3.1
    """

    if not os.path.isfile(rrd_file):
        raise FileNotFoundError(rrd_file)

    if not os.access(rrd_file, os.W_OK):
        raise FileNotWritableError(rrd_file)

    def add_one_to_match(obj):
        """ Add one to a regexp match object """
        return str(int(obj.group()) + 1)

    # Get headerinfo for the datasources. We assume every option except the
    # type and name is the same for the new one.
    try:
        rrd_header = rrdtool.info(rrd_file)
    except Exception:
        raise FileNotRRDError(rrd_file)
    
    rrd_datasource_info = rrd_header['ds']['ds0']

    # Find last datasource in file to set correct name for the new one. A bit
    # cricket-specific as we assume the ds_name is equal to ds<number>
    last_datasource = sorted(rrd_header['ds'].keys(), natsort.natcmp)[-1]
    new_datasource = re.sub('(\d+)', add_one_to_match, last_datasource)

    # We have all the data we are to insert, lets parse the xml and insert new
    # data.
    xml_file = dump_rrd_to_xml(rrd_file)
    xml = minidom.parseString(xml_file)

    # Find all ds-elements, effectively saving the last one
    last_datasource_in_rrd = [n for n in xml.documentElement.childNodes
              if n.nodeType == n.ELEMENT_NODE and n.nodeName == 'ds'][-1]

    # If we have a last ds-element, use that to create a clone, replace values
    # in the clone and insert it into the xml document
    if last_datasource_in_rrd:
        # clone this element, replace values in clone with the ones we want
        clone = last_datasource_in_rrd.cloneNode(deep=True)

        for node in clone.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                if node.nodeName == 'name':
                    text = xml.createTextNode(new_datasource)
                    node.replaceChild(text, node.firstChild)
                elif node.nodeName == 'value':
                    text = xml.createTextNode('0.0000000000e+00')
                    node.replaceChild(text, node.firstChild)
                elif node.nodeName == 'last_ds':
                    text = xml.createTextNode('UNKN')
                    node.replaceChild(text, node.firstChild)
                elif node.nodeName == 'unknown_sec':
                    text = xml.createTextNode('0')
                    node.replaceChild(text, node.firstChild)

        # find next sibling, insert clone before next sibling
        next_sibling = last_datasource_in_rrd.nextSibling
        xml.documentElement.insertBefore(clone, next_sibling)

    # Find all cdp_prep elements and add childelement to them
    for element in xml.getElementsByTagName('cdp_prep'):
        rrd_datasource = xml.createElement('ds')

        pvalue = xml.createElement('primary_value')
        pvalue.appendChild(xml.createTextNode('0.0000000000e+00'))

        svalue = xml.createElement('secondary_value')
        svalue.appendChild(xml.createTextNode('0.0000000000e+00'))

        value = xml.createElement('value')
        value.appendChild(xml.createTextNode('NaN'))

        unknown = xml.createElement('unknown_datapoints')
        unknown.appendChild(xml.createTextNode('0'))

        rrd_datasource.appendChild(pvalue)
        rrd_datasource.appendChild(svalue)
        rrd_datasource.appendChild(value)
        rrd_datasource.appendChild(unknown)

        element.appendChild(rrd_datasource)

    # Append a value-node to each row-node
    for element in xml.getElementsByTagName('row'):
        value = xml.createElement('v')
        value.appendChild(xml.createTextNode('NaN'))
        element.appendChild(value)

    # Write xml_file to disk as rrdrestore demands a file
    tmp_path = os.path.join(TMPPATH, 'adddatasource.xml')
    filehandle = open(tmp_path, 'w')
    filehandle.write(xml.toxml())
    filehandle.close()

    output = rrd_restore(tmp_path, rrd_file)

    return output


def dump_rrd_to_xml(filename):
    """ Try to dump the file given to xml using rrddump """

    output = Popen(["rrdtool", "dump", filename], stdout=PIPE).communicate()[0]

    return output


def rrd_restore(xmlfile, rrdfile):
    """ Try to restore xmlfile to rrdfile using rrdrestore.

    NB: This will overwrite the existing RRD file!"""

    output = Popen(['rrdtool', 'restore', xmlfile, rrdfile, '-f'],
                   stdout=PIPE).communicate()[0]

    return output
