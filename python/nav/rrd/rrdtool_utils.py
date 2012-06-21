#!/usr/bin/env python

import rrdtool
import time
import re
import os
import tempfile
from os.path import join
from optparse import OptionParser
from subprocess import Popen, PIPE
from xml.dom.minidom import parseString

"""
Heavily depending on that the datasources are named ds0, ds1 and so forth.
Supports rrdtool up to and including version 1.3.

TODO:
- Able to remove more than one datasource.
- Able to add more than one datasource.
- Able to work with datasources based on name.
"""

class FileDoesNotExistException(Exception):
    """ File does not exist exception """

    def __init__(self, filename):
        self.filename = filename
    def __str__(self):
        return "%s does not exist." % self.filename

class FileNotWritableException(Exception):
    """ File not writable exception """

    def __init__(self, filename):
        self.filename = filename
    def __str__(self):
        return "%s is not writable." % self.filename

class InvalidDatasourceNameException(Exception):
    """ Invalid data source name exception """

    def __init__(self, datasource_name):
        self.datasource_name = datasource_name
    def __str__(self):
        return "%s is not a valid datasourcename." % self.datasource_name

class OutofBoundsException(Exception):
    """ Out of bounds exception """

    def __init__(self, datasource_name, number_datasources):
        self.datasource_name = datasource_name
        self.number_datasources = number_datasources
    def __str__(self):
        return ("Datasource %s is out of bounds. File has only %s datasources "
                "(0-%s)." % (self.datasource_name, self.number_datasources,
                             self.number_datasources - 1))

class CannotWriteToTmpException(Exception):
    """ Cannot write to tmp exception """

    def __init__(self, restore_file):
        self.restorefile = restore_file
    def __str__(self):
        return "Cannot write to /tmp - this is needed to restore the rrd file."

class ErrorRunningRRDToolException(Exception):
    """ Error running RRDTool exception """

    def __init__(self, error_message):
        self.errormessage = error_message
    def __str__(self):
        return "Error running rrdtool: %s" % self.errormessage


def main(options, args):
    """
    Handle the options.
    """
    if not options.rrdfile:
        print "You must specify a rrd_file."
        return

    rrd_file = options.rrdfile

    if options.info:
        rrd_info(rrd_file)
    elif options.removeds:
        try:
            edit_datasource(rrd_file, options.removeds, 'remove')
        except Exception, e:
            print e
    elif options.add:
        try:
            edit_datasource(rrd_file, options.add, 'add')
        except Exception, e:
            print e        
    else:
        print "You need to specify what to do with the file (-h)."
        
    
def rrd_info(rrd_file, raw=False):
    """ 
    Intended use is from shell. If you want the whole dict returned by
    rrdtool.info, set raw to true.
    """
    file_info = rrdtool.info(rrd_file)
    
    if raw: 
        return file_info
    
    if not file_info.has_key('ds'):
        #=======================================================================
        # In version 1.3 the output from info is totally different. We just 
        # print a key/value output.
        #=======================================================================
        for key in sorted(file_info.keys()):
            print "%s: %s" % (key, file_info[key])
        return

    print "%s last updated %s" % (file_info['filename'],
                                 time.ctime(file_info['last_update']))
    print "Datasources (datasource: datasourcename):"
    for datasource in sorted(file_info['ds'].items()):
        print "  %s: %s" % (datasource[0], datasource[1]['ds_name'])

    print "RRA's (Step = %s):" % (file_info['step'])

    for rra in file_info['rra']:
        print "  %s: %s/%s" % (rra['cf'], rra['pdp_per_row'], rra['rows'])


def edit_datasource(rrd_file, name, action):
    """
    Attempt to add or remove a datasource by dumping the rrdfile to
    xml and adding or removing the elements matching the datasource
    name for all elements.

    Is dependant on:
    - Writing to /tmp (for restoring the rrdfile)
    - Being able to read and write to the file given as input.
    - The datasource name given must be given on the format dsx where
      x is a number.
    """

    temp_dir = tempfile.gettempdir()
    restore_file = join(temp_dir, 'rrdtool_utils_restore.xml')

    # Check if file exists
    if not os.access(rrd_file, os.F_OK):
        raise FileDoesNotExistException(rrd_file)
    
    # Check if file is writable
    if not os.access(rrd_file, os.W_OK):
        raise FileNotWritableException(rrd_file)

    # Check if we can write to /tmp
    try:
        filehandle = open(restore_file, 'w')
    except Exception:
        raise CannotWriteToTmpException(restore_file)

    # Dump rrd to xml
    try:
        output = Popen(['rrdtool', 'dump', rrd_file],
                       stdout=PIPE).communicate()[0]
    except OSError, oserror:
        raise ErrorRunningRRDToolException(oserror)

    # Read xml-file
    xml_file = parseString(output)
    
    # Find index of datasource
    is_match = re.search('ds(\d+)', name)
    if is_match:
        rrd_datasource_value = int(is_match.groups()[0])
    else:
        raise InvalidDatasourceNameException(name)

    # Add or delete datasource based on input parameter
    if action == 'add':
        xml_file = add_datasource(xml_file, rrd_datasource_value)
    elif action == 'remove':
        xml_file = remove_datasource(xml_file, rrd_datasource_value)

    # rrdtool restore needs a file to restore from
    filehandle = open(restore_file, 'w')
    xml_file.writexml(filehandle)
    filehandle.close()

    # Create backup file before restoring
    output = Popen(['cp', '-b', rrd_file, rrd_file + '.bak'],
                   stdout=PIPE).communicate()[0]

    # Restore xml-file to rrd (force overwrite)
    output = Popen(['rrdtool', 'restore', restore_file, rrd_file, '-f'],
                   stdout=PIPE).communicate()[0]

    # Remove restore file
    os.remove(restore_file)


def add_datasource(xml_file, datasource_value):
    # I do quite some prettymaking here with the textnodes. It is not
    # certain that this is needed, and it clutters the code a bit.

    # Find first available datasource, clone and modify it.
    for element in xml_file.documentElement.childNodes:
        if element.nodeName == 'ds':
            datasource_clone = element.cloneNode(True)
            datasource_clone.getElementsByTagName(
                'name')[0].firstChild.data = ' ds%s ' % datasource_value
            datasource_clone.getElementsByTagName('min')[
            0].firstChild.data = ' NaN '
            datasource_clone.getElementsByTagName('max')[
            0].firstChild.data = ' NaN '
            datasource_clone.getElementsByTagName('last_ds')[
            0].firstChild.data = ' NaN '
            datasource_clone.getElementsByTagName('value')[
            0].firstChild.data = ' NaN '
            datasource_clone.getElementsByTagName(
                'unknown_sec')[0].firstChild.data = ' 0 '
            break

    # Set dsvalue to max allowed value if it to be appended
    datasources = find_number_of_datasources(xml_file)
    if datasource_value >= datasources:
        # We cannot use append as this is not the last element (and
        # rrdrestore slapped me hard for saying it didn't matter).
        # Walk through all ds-elements and insert after the last one.
        datasource_value = datasources # max value
        datasource_clone.getElementsByTagName(
            'name')[0].firstChild.data = ' ds%s ' % datasource_value
        counter = 0
        for node in xml_file.documentElement.childNodes:
            if node.nodeName == 'ds':
                counter += 1
                continue
            if counter == datasource_value:
                text_node = xml_file.createTextNode('\n\n\t')
                xml_file.documentElement.insertBefore(datasource_clone, node)
                xml_file.documentElement.insertBefore(text_node,
                    datasource_clone)
                break
    else: 
        # Insert the datasource before the original datasource with
        # the same name, effectively skewing all the others one up.
        inserted = False
        for element in xml_file.documentElement.childNodes:
            if element.nodeName == 'ds':
                rrd_datasource_name = element.getElementsByTagName('name')[
                                      0].firstChild.data
                current_value = int(
                    re.search('ds(\d+)', rrd_datasource_name).groups()[0])
                # Check if this is the datasource to be replaced.
                if current_value == datasource_value and not inserted:
                    text_node = xml_file.createTextNode('\n\n\t')
                    xml_file.documentElement.insertBefore(text_node, element)
                    xml_file.documentElement.insertBefore(datasource_clone,
                        text_node)
                    inserted = True
                    continue
                # Increment the rest of the datasources by one.
                if current_value >= datasource_value:
                    element.getElementsByTagName('name')[0].firstChild.data = \
                        " ds%s " % (current_value + 1)
                    
    # Add cdp_prep
    for cdp in xml_file.getElementsByTagName('cdp_prep'):
        # Clone first element, modify clone
        datasource_clone = cdp.getElementsByTagName('ds')[0].cloneNode(True)
        datasource_clone.getElementsByTagName(
            'primary_value')[0].firstChild.data = ' NaN '
        datasource_clone.getElementsByTagName(
            'secondary_value')[0].firstChild.data = ' NaN '
        datasource_clone.getElementsByTagName('value')[
        0].firstChild.data = ' NaN '
        datasource_clone.getElementsByTagName(
            'unknown_datapoints')[0].firstChild.data = ' 0 '
        
        if datasource_value >= datasources:
            # Modify last textnode for prettymaking
            cdp.lastChild.data = "\n\t\t\t"
            text_node = xml_file.createTextNode('\n\t\t')
            cdp.appendChild(datasource_clone)
            cdp.appendChild(text_node)
        else:
            text_node = xml_file.createTextNode('\n\t\t\t')
            cdp.insertBefore(text_node,
                cdp.getElementsByTagName('ds')[datasource_value])
            cdp.insertBefore(datasource_clone, text_node)

    # Add columns for all rows in each database
    for row in xml_file.getElementsByTagName('row'):
        # Clone first element, modify clone
        vclone = row.getElementsByTagName('v')[0].cloneNode(True)
        vclone.firstChild.data = ' NaN '
        if datasource_value >= datasources:
            row.appendChild(vclone)
        else:
            row.insertBefore(vclone,
                row.getElementsByTagName('v')[datasource_value])

    return xml_file


def remove_datasource(xml_file, datasource_value):
    """
    Edit xml-file to remove all elements regarding the datasource
    value given as input.
    """
    # Check if index is out of bounds
    datasources = find_number_of_datasources(xml_file)
    if datasource_value >= datasources:
        raise OutofBoundsException(datasource_value, datasources)

    # Remove datasource element
    xml_file.documentElement.removeChild(
        xml_file.documentElement.getElementsByTagName('ds')[datasource_value])

    # Rename the other datasource elements to match sequence
    for node in xml_file.documentElement.childNodes:
        if node.nodeName == 'ds':
            datasource_name = node.getElementsByTagName('name')[
                              0].firstChild.data
            datasource_number = int(
                re.search("(\d+)", datasource_name).groups()[0])
            if datasource_number >= datasource_value:
                # Subtract one and pray.
                datasource_number -= 1
                node.getElementsByTagName(
                    'name')[0].firstChild.data = " ds%s " % datasource_number
            
    # Remove all ds-elements from all cdp-preps
    for cdp in xml_file.getElementsByTagName('cdp_prep'):
        cdp.removeChild(cdp.getElementsByTagName('ds')[datasource_value])

    # Remove v-element from all rows in all database-elements
    for database in xml_file.getElementsByTagName('database'):
        for row in database.getElementsByTagName('row'):
            row.removeChild(row.getElementsByTagName('v')[datasource_value])

    return xml_file


def find_number_of_datasources(xmlfile):
    """
    Count the number of datasource nodes in the xmlfile.  
    """
    number_of_datasources = 0
    for node in xmlfile.documentElement.childNodes:
        if node.nodeName == 'ds':
            number_of_datasources += 1

    return number_of_datasources
    

if __name__ == '__main__':
    """
    Support command line arguments for use in shell.
    """

    parser = OptionParser()
    parser.add_option("-f", "--file", dest="rrdfile", help="File to work with")
    parser.add_option("-i", action="store_true", dest="info",
                      help="Print information about the file.")
    parser.add_option("-r", "--remove_datasource", dest="removeds",
                      help="Specify datasource for removal (ds0, ds1 etc).")
    parser.add_option("-a", "--add_datasource", dest="add",
                      help="Specify datasource for addition (ds0, ds1 etc).")
    options, args = parser.parse_args()

    main(options, args)
