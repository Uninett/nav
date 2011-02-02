#!/usr/bin/env python

import os
import re
import rrdtool
from subprocess import Popen, PIPE
from xml.dom import minidom

from nav import natsort
from nav.errors import GeneralException

TMPPATH = '/tmp' # Path for storing temporary files

__author__ = "John-Magne Bredal <john.m.bredal@ntnu.no>"


class FileNotFoundError(GeneralException):
    "File not found"
    pass


class FileNotWritableError(GeneralException):
    "File not writable"
    pass


class FileNotRRDError(GeneralException):
    "File does not seem to be an rrd-file"
    pass


def add_datasource(rrdfile):
    """ Takes as input the full path to an rrdfile and tries to add a
    datasource to that file. The default values of the heartbeat, type and so
    on are used.

    Returns output from rrdrestore.

    NB: Works for RRDtool 1.2.x up to 1.3.1
    """

    if not os.path.isfile(rrdfile):
        raise FileNotFoundError(rrdfile)

    if not os.access(rrdfile, os.W_OK):
        raise FileNotWritableError(rrdfile)

    def addOneToMatch(obj):
        """ Add one to a regexp match object """
        return str(int(obj.group()) + 1)

    # Get headerinfo for the datasources. We assume every option except the
    # type and name is the same for the new one.
    try:
        rrdheader = rrdtool.info(rrdfile)
    except Exception, e:
        raise FileNotRRDError(rrdfile)
    
    rrddsinfo = rrdheader['ds']['ds0']

    # Find last datasource in file to set correct name for the new one. A bit
    # cricket-specific as we assume the ds_name is equal to ds<number>
    lastdatasource = sorted(rrdheader['ds'].keys(), natsort.natcmp)[-1]
    newdatasource = re.sub('(\d+)', addOneToMatch, lastdatasource)

    # We have all the data we are to insert, lets parse the xml and insert new
    # data.
    xmlfile = dump_rrd_to_xml(rrdfile)
    xml = minidom.parseString(xmlfile)

    # Find all ds-elements, effectively saving the last one
    lastds = [n for n in xml.documentElement.childNodes
              if n.nodeType == n.ELEMENT_NODE and n.nodeName == 'ds'][-1]

    # If we have a last ds-element, use that to create a clone, replace values
    # in the clone and insert it into the xml document
    if lastds:
        # clone this element, replace values in clone with the ones we want
        clone = lastds.cloneNode(deep=True)

        for e in clone.childNodes:
            if e.nodeType == e.ELEMENT_NODE:
                if e.nodeName == 'name':
                    text = xml.createTextNode(newdatasource)
                    e.replaceChild(text, e.firstChild)
                elif e.nodeName == 'value':
                    text = xml.createTextNode('0.0000000000e+00')
                    e.replaceChild(text, e.firstChild)
                elif e.nodeName == 'last_ds':
                    text = xml.createTextNode('UNKN')
                    e.replaceChild(text, e.firstChild)
                elif e.nodeName == 'unknown_sec':
                    text = xml.createTextNode('0')
                    e.replaceChild(text, e.firstChild)

        # find next sibling, insert clone before next sibling
        nextsibling = lastds.nextSibling
        xml.documentElement.insertBefore(clone, nextsibling)

    # Find all cdp_prep elements and add childelement to them
    for element in xml.getElementsByTagName('cdp_prep'):
        ds = xml.createElement('ds')

        pvalue = xml.createElement('primary_value')
        pvalue.appendChild(xml.createTextNode('0.0000000000e+00'))

        svalue = xml.createElement('secondary_value')
        svalue.appendChild(xml.createTextNode('0.0000000000e+00'))

        value = xml.createElement('value')
        value.appendChild(xml.createTextNode('NaN'))

        unknown = xml.createElement('unknown_datapoints')
        unknown.appendChild(xml.createTextNode('0'))

        ds.appendChild(pvalue)
        ds.appendChild(svalue)
        ds.appendChild(value)
        ds.appendChild(unknown)

        element.appendChild(ds)

    # Append a value-node to each row-node
    for element in xml.getElementsByTagName('row'):
        value = xml.createElement('v')
        value.appendChild(xml.createTextNode('NaN'))
        element.appendChild(value)

    # Write xmlfile to disk as rrdrestore demands a file
    tmppath = os.path.join(TMPPATH, 'adddatasource.xml')
    f = open(tmppath, 'w')
    f.write(xml.toxml())
    f.close()

    output = rrd_restore(tmppath, rrdfile)

    return output


def dump_rrd_to_xml(file):
    """ Try to dump the file given to xml using rrddump """

    output = Popen(["rrdtool", "dump", file], stdout=PIPE).communicate()[0]

    return output


def rrd_restore(xmlfile, rrdfile):
    """ Try to restore xmlfile to rrdfile using rrdrestore.

    NB: This will overwrite the existing RRD file!"""

    output = Popen(['rrdtool', 'restore', xmlfile, rrdfile, '-f'],
                   stdout=PIPE).communicate()[0]

    return output
