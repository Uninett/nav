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
Author: John-Magne Bredal <john.m.bredal@ntnu.no>

TODO:
- Able to remove more than one datasource.
- Able to add more than one datasource.
- Able to work with datasources based on name.
"""

class FileDoesNotExistException(Exception):
    def __init__(self, filename):
        self.filename = filename
    def __str__(self):
        return "%s does not exist." % self.filename

class FileNotWritableException(Exception):
    def __init__(self, filename):
        self.filename = filename
    def __str__(self):
        return "%s is not writable." % self.filename

class InvalidDatasourceNameException(Exception):
    def __init__(self, dsname):
        self.dsname = dsname
    def __str__(self):
        return "%s is not a valid datasourcename." % self.dsname

class OutofBoundsException(Exception):
    def __init__(self, dsname, numds):
        self.dsname = dsname
        self.numds = numds
    def __str__(self):
        return "Datasource %s is out of bounds. File has only %s datasources \
(0-%s)." \
            % (self.dsname, self.numds, self.numds - 1)

class CannotWriteToTmpException(Exception):
    def __init__(self, restorefile):
        self.restorefile = restorefile
    def __str__(self):
        return "Cannot write to /tmp - this is needed to restore the rrd file."

class ErrorRunningRRDToolException(Exception):
    def __init__(self, errormessage):
        self.errormessage = errormessage
    def __str__(self):
        return "Error running rrdtool: %s" %self.errormessage


def main(options, args):
    """
    Handle the options.
    """
    if not options.rrdfile:
        print "You must specify a rrdfile."
        return

    rrdfile = options.rrdfile

    if options.info:
        rrd_info(rrdfile)
    elif options.removeds:
        try:
            edit_datasource(rrdfile, options.removeds, 'remove')
        except Exception, e:
            print e
    elif options.add:
        try:
            edit_datasource(rrdfile, options.add, 'add')
        except Exception, e:
            print e        
    else:
        print "You need to specify what to do with the file (-h)."
        
    
def rrd_info(rrdfile, raw=False):
    """ 
    Intended use is from shell. If you want the whole dict returned by
    rrdtool.info, set raw to true.
    """
    fileinfo = rrdtool.info(rrdfile)
    
    if raw: 
        return fileinfo
    
    if not fileinfo.has_key('ds'):
        #=======================================================================
        # In version 1.3 the output from info is totally different. We just 
        # print a key/value output.
        #=======================================================================
        for key in sorted(fileinfo.keys()):
            print "%s: %s" % (key, fileinfo[key])
        return

    print "%s last updated %s" % (fileinfo['filename'],
                                 time.ctime(fileinfo['last_update']))
    print "Datasources (datasource: datasourcename):"
    for ds in sorted(fileinfo['ds'].items()):
        print "  %s: %s" % (ds[0], ds[1]['ds_name'])

    print "RRA's (Step = %s):" % (fileinfo['step'])

    for rra in fileinfo['rra']:
        print "  %s: %s/%s" % (rra['cf'], rra['pdp_per_row'], rra['rows'])


def edit_datasource(rrdfile, name, action):
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

    tempdir = tempfile.gettempdir()
    restorefile = join(tempdir, 'rrdtool_utils_restore.xml')

    # Check if file exists
    if not os.access(rrdfile, os.F_OK):
        raise FileDoesNotExistException(rrdfile)
    
    # Check if file is writable
    if not os.access(rrdfile, os.W_OK):
        raise FileNotWritableException(rrdfile)

    # Check if we can write to /tmp
    try:
        f = open(restorefile, 'w')
    except Exception, e:
        raise CannotWriteToTmpException(restorefile)

    # Dump rrd to xml
    try:
        output = Popen(['rrdtool', 'dump', rrdfile], 
                       stdout=PIPE).communicate()[0]
    except OSError, oserror:
        raise ErrorRunningRRDToolException(oserror)

    # Read xml-file
    xmlfile = parseString(output)
    
    # Find index of datasource
    m = re.search('ds(\d+)', name)
    if m:
        dsvalue = int(m.groups()[0])
    else:
        raise InvalidDatasourceNameException(name)

    # Add or delete datasource based on input parameter
    if action == 'add':
        xmlfile = add_datasource(xmlfile, dsvalue)
    elif action == 'remove':
        xmlfile = remove_datasource(xmlfile, dsvalue)

    # rrdtool restore needs a file to restore from
    f = open(restorefile, 'w')
    xmlfile.writexml(f)
    f.close()

    # Create backup file before restoring
    output = Popen(['cp', '-b', rrdfile, rrdfile + '.bak'], stdout=PIPE).communicate()[0]

    # Restore xml-file to rrd (force overwrite)
    output = Popen(['rrdtool', 'restore', restorefile, rrdfile, '-f'], stdout=PIPE).communicate()[0]

    # Remove restore file
    os.remove(restorefile)


def add_datasource(xmlfile, dsvalue):
    # I do quite some prettymaking here with the textnodes. It is not
    # certain that this is needed, and it clutters the code a bit.

    # Find first available datasource, clone and modify it.
    for element in xmlfile.documentElement.childNodes:
        if element.nodeName == 'ds':
            dsclone = element.cloneNode(True)
            dsclone.getElementsByTagName('name')[0].firstChild.data = ' ds%s ' % dsvalue
            dsclone.getElementsByTagName('min')[0].firstChild.data = ' NaN '
            dsclone.getElementsByTagName('max')[0].firstChild.data = ' NaN '
            dsclone.getElementsByTagName('last_ds')[0].firstChild.data = ' NaN '
            dsclone.getElementsByTagName('value')[0].firstChild.data = ' NaN '
            dsclone.getElementsByTagName('unknown_sec')[0].firstChild.data = ' 0 '
            break

    # Set dsvalue to max allowed value if it to be appended
    datasources = find_number_of_datasources(xmlfile)
    if dsvalue >= datasources:
        # We cannot use append as this is not the last element (and
        # rrdrestore slapped me hard for saying it didn't matter).
        # Walk through all ds-elements and insert after the last one.
        dsvalue = datasources # max value
        dsclone.getElementsByTagName('name')[0].firstChild.data = ' ds%s ' % dsvalue
        counter = 0
        for e in xmlfile.documentElement.childNodes:
            if e.nodeName == 'ds':
                counter += 1
                continue
            if counter == dsvalue:
                textnode = xmlfile.createTextNode('\n\n\t')
                xmlfile.documentElement.insertBefore(dsclone, e)
                xmlfile.documentElement.insertBefore(textnode, dsclone)
                break
    else: 
        # Insert the datasource before the original datasource with
        # the same name, effectively skewing all the others one up.
        inserted = False
        for element in xmlfile.documentElement.childNodes:
            if element.nodeName == 'ds':
                dsname = element.getElementsByTagName('name')[0].firstChild.data
                currentvalue = int(re.search('ds(\d+)', dsname).groups()[0])
                # Check if this is the datasource to be replaced.
                if currentvalue == dsvalue and not inserted:
                    textnode = xmlfile.createTextNode('\n\n\t')
                    xmlfile.documentElement.insertBefore(textnode, element)
                    xmlfile.documentElement.insertBefore(dsclone, textnode)
                    inserted = True
                    continue
                # Increment the rest of the datasources by one.
                if currentvalue >= dsvalue:
                    element.getElementsByTagName('name')[0].firstChild.data = \
                        " ds%s " % (currentvalue + 1)
                    
    # Add cdp_prep
    for cdp in xmlfile.getElementsByTagName('cdp_prep'):
        # Clone first element, modify clone
        dsclone = cdp.getElementsByTagName('ds')[0].cloneNode(True)
        dsclone.getElementsByTagName('primary_value')[0].firstChild.data = ' NaN '
        dsclone.getElementsByTagName('secondary_value')[0].firstChild.data = ' NaN '
        dsclone.getElementsByTagName('value')[0].firstChild.data = ' NaN '
        dsclone.getElementsByTagName('unknown_datapoints')[0].firstChild.data = ' 0 '
        
        if dsvalue >= datasources:
            # Modify last textnode for prettymaking
            cdp.lastChild.data = "\n\t\t\t"
            textnode = xmlfile.createTextNode('\n\t\t')
            cdp.appendChild(dsclone)
            cdp.appendChild(textnode)
        else:
            textnode = xmlfile.createTextNode('\n\t\t\t')
            cdp.insertBefore(textnode, cdp.getElementsByTagName('ds')[dsvalue])
            cdp.insertBefore(dsclone, textnode)

    # Add columns for all rows in each database
    for row in xmlfile.getElementsByTagName('row'):
        # Clone first element, modify clone
        vclone = row.getElementsByTagName('v')[0].cloneNode(True)
        vclone.firstChild.data = ' NaN '
        if dsvalue >= datasources:
            row.appendChild(vclone)
        else:
            row.insertBefore(vclone, row.getElementsByTagName('v')[dsvalue])

    return xmlfile


def remove_datasource(xmlfile, dsvalue):
    """
    Edit xml-file to remove all elements regarding the datasource
    value given as input.
    """
    # Check if index is out of bounds
    datasources = find_number_of_datasources(xmlfile)
    if dsvalue >= datasources:
        raise OutofBoundsException(dsvalue, datasources)

    # Remove datasource element
    xmlfile.documentElement.removeChild(
        xmlfile.documentElement.getElementsByTagName('ds')[dsvalue])

    # Rename the other datasource elements to match sequence
    for node in xmlfile.documentElement.childNodes:
        if node.nodeName == 'ds':
            dsname = node.getElementsByTagName('name')[0].firstChild.data
            dsnumber = int(re.search("(\d+)", dsname).groups()[0])
            if dsnumber >= dsvalue:
                # Subtract one and pray.
                dsnumber -= 1
                node.getElementsByTagName('name')[0].firstChild.data = " ds%s " % dsnumber
            
    # Remove all ds-elements from all cdp-preps
    for cdp in xmlfile.getElementsByTagName('cdp_prep'):
        cdp.removeChild(cdp.getElementsByTagName('ds')[dsvalue])

    # Remove v-element from all rows in all database-elements
    for db in xmlfile.getElementsByTagName('database'):
        for row in db.getElementsByTagName('row'):
            row.removeChild(row.getElementsByTagName('v')[dsvalue])

    return xmlfile


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
