#!/usr/bin/env python
# -*- coding: ISO8859-1 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Authors: John Magne Bredal <john.m.bredal@ntnu.no>
#
"""
The NEW way to make cricket-config.
"""

import threading
import Queue
import os
import re
import nav.db
import sys # temp
import time
import psycopg2.extras

starttime = time.time()

def findCricketdirs (path):
    """
    This method finds all directories located in the cricket-config
    directory and returns an array with paths to directories.  The
    point is that every thread grabs a directory and starts working
    with it.
    """

    pool = []

    dirs = os.listdir(path)
    for dir in dirs:
        if os.path.isdir(path + dir):
            print "Found directory %s" %(path + dir)
            totalpath = path + dir + "/"
            pool.append(totalpath)

    return pool
    

def parseViewConfig (path):
    """
    Parse the viewconfig-file and put the data in a dict for easy
    access.
    """
    # view cpu: cpu1min cpu5min hpcpu
    viewfile = path + "view-groups"
    try:
        f = open(viewfile)
        for line in f.readlines():
            mo = re.match('view (.*):\s*(.*)$',line)
            if mo:
                view = mo.groups()[0]
                values = mo.groups()[1].split(' ')
                for key in values:
                    views[key] = view
                
    except IOError, (errno, errstr):
        print "Could not open %s because %s" %(viewfile, errstr)



def makeOIDhash (path, parent=''):
    """
    A method to parse all cricket-config-files and fill the global
    dict 'oids' with all the oids that we find.
    """

    oids[path] = {}
    children = [] # our subdirectories

    # if we have a parent, copy all oids from the parent
    if parent:
        #print "Copying list from parent"
        #print "Parent has key value-pairs like this:"
        for value in oids[parent].keys():
            #print "%s -> %s" %(value, oids[parent][value])
            oids[path][value] = oids[parent][value]
        
    # Get all entries from the directory
    files = os.listdir(path)

    # For each entry check if it is a file. If so, look in file for oids
    for readfile in files:
        if os.path.isfile(path + readfile):
            f = open(path + readfile)
            lines = f.readlines()
            for line in lines:
                matchobject = re.match('(?i)oid\s+(\w+)\s+([0-9.]+)',line)
                if matchobject:
                    oid = matchobject.groups()[1]
                    text = matchobject.groups()[0]
                    #print "Found oid %s %s" %(oid, text)
                    # Add it to the oids global dict
                    oids[path][oid] = text
            f.close
        elif os.path.isdir(path + readfile):
            newpath = path + readfile + "/"
            # Add directory for later processing
            children.append(newpath)

    # If we have any children, look there aswell
    for child in children:
        makeOIDhash(child, path)
            

class makeCricketConfig (threading.Thread):
    """
    This class reads the information in the nav-configfiles and
    creates targets for Cricket based on that.
    """

    def __init__(self, id, q):
        threading.Thread.__init__(self)
        self.id = id
        self.q = q
        self.starttime = time.time()

    def run(self):
        # Get an object from the Queue
        while not q.empty():
            try:
                thispath = q.get(0)                
                print "T%s: Got %s from queue" %(self.id, thispath)

                editfile = thispath + "/" + configfile
                if os.path.exists(editfile):
                    print "T%s: Found makeconfigfile, parsing it." %(self.id)
                    try:
                        f = open(editfile,'r')

                        # Delete all previous NAVconfig
                        navfile = thispath + "/" + targetfile
                        ttfile = thispath + "/" + targettypesfile
                        if os.path.exists(navfile):
                            try:
                                print "T%s: Removing existing config-file %s" %(self.id, navfile)
                                os.remove(navfile)
                            except IOError, (errno, errstr):
                                print "T%s: Could not remove %s - %s" %(self.id, navfile, errstr)

                        if os.path.exists(ttfile):
                            try:
                                print "T%s: Removing existing config-file %s" %(self.id, ttfile)
                                os.remove(ttfile)
                            except IOError, (errno, errstr):
                                print "T%s: Could not remove %s - %s" %(self.id, ttfile, errstr)

                        # Parse file and create config
                        targetq = ""
                        targett = ""
                        interfaceq = ""
                        for line in f:
                            # Ok we have a file with information about how to make config to cricket
                            # What we are looking for is A target-tag. The sql after this tag should
                            # return the targets and the description for the targets.
                            s = re.split("=",line,1)
                            if s[0] == "target":
                                print "T%s: Setting targetquery to: %s" %(self.id, s[1])
                                targetq = s[1]
                            elif s[0] == "interface":
                                print "T%s: Setting interfacequery to: %s" %(self.id, s[1])
                                interfaceq = s[1]
                            elif s[0] == "target-type":
                                targett = s[1].rstrip()
                            elif re.match('^##.*', line):
                                # Do query, 
                                if interfaceq:
                                    self.createInterfaces(thispath, interfaceq)
                                    interfaceq = ""
                                if targetq:
                                    targets = self.createTargets(thispath, targetq, targett)
                                    self.fillRRDdatabase(thispath, targets)
                                    targetq = ""

                                targett = ""
                                    

                        f.close()

                    except IOError, (errno, errstr):
                        print "T%s: Could not open %s - %s" %(self.id, editfile, errstr)

            except Queue.Empty:
                print "T%s: Could not get item from queue" %(self.id)
                continue

        print "T%s: I am done (used %.2f seconds)" %(self.id, time.time() - self.starttime)


    def createTargets(self, thispath, query, targett):
        """
        Creates and fills the NAVtargets-file based on the query and
        places it in path. This method should only be executed with
        normal targets - no interfaces.
        """
        navfile = thispath + "/" + targetfile
        print "T%s: Making file %s" %(self.id, navfile)

        targetlist = {}

        try: 
            t = open(navfile, 'a')
            t.write(disclaimer)
            
            c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            c.execute(query)
            print "T%s: Executing %s" %(self.id, query)
            # We expect the query to return these values. We must handle errors here.
            # netboxid - id of netbox
            # target - sysname of netbox
            # ip - ip of netbox
            # ro - read only community (or read write - who cares?)
            # descr - description
            # targetname is optional
            for row in c.fetchall():
                print "T%s: Writing target for %s (%s)" %(self.id, row['target'], row['netboxid'])
                t.write("target \"" + row['target'] + "\"\n")
                if row.has_key('displayname'):
                    t.write("\tdisplay-name" + row['targetname'] + "\n")
                t.write("\tsnmp-host\t=\t" + row['ip'] + "\n")
                t.write("\tsnmp-community\t=\t" + row['ro'] + "\n")
                if targett:
                    t.write("\ttarget-type\t=\t" + targett + "\n")
                else:
                    t.write("\ttarget-type\t=\t" + row['target'] + "\n")
                t.write("\tshort-desc\t=\t\"" + row['descr'] + "\"\n\n")

                targetlist[row['netboxid']] = row['target']

            t.close()


        except IOError, (errno, errstr):
            print "T%s: Could not open %s - %s" %(self.id, navfile, errstr)

        print "T%s: Done making targets" %self.id

        if not targett:
            print "T%s: Starting createTargettypes" %self.id
            targetmapping = self.createTargettypes(thispath, targetlist)

        return [targetlist, targetmapping]
        

    def createInterfaces(self, thispath, query):
        """
        Creates and fills the NAVtargets-file based on the query and
        places it in thispath. This method should only be executed
        with interfaces
        """

        print "T%s: Running createInterfaces" %(self.id)
        
        # Execute query from user
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        c.execute(query)

        for row in c.fetchall():
            checkdir = thispath + "/" + row['sysname']
            if os.path.isdir(checkdir):
                navfile = checkdir + "/" + targetfile
                try:
                    print "T%s: Removing existing config-file %s" %(self.id, navfile)
                    os.remove(navfile)
                    os.rmdir(checkdir)
                except IOError, (errno, errstr):
                    print "T%s: Could not remove %s - %s" %(self.id, navfile, errstr)


        # We need the following rows:
        # sysname of device with interfaces
        # ip - ip of netbox (for snmp-query)
        # ro - read only community (or read write - who cares?)
        # target - filename of rrd-file
        # targetname is optional - but is link shown on webpage
        # descr - description

        c.execute(query)

        navfile = ""
        currenttarget = ""
        workingdir = ""

        for row in c.fetchall():
            # for each row, check if this is another sysname than the previous one
            if currenttarget != row['sysname']:
                print "T%s: Target changed from %s to %s." %(self.id, currenttarget, row['sysname'])
                currenttarget = row['sysname']
                workingdir = thispath + "/" + row['sysname']
                
                # If it is, make new directory...
                if not os.path.isdir(workingdir):
                    os.mkdir(workingdir)
                    print "T%s: Made directory %s (I think)" %(self.id, workingdir)

                # Open new file.
                navfile = workingdir + "/" + targetfile
                try:
                    t = open(navfile, 'a')

                    print "T%s: Made %s. Quite certain." %(self.id, navfile)
                    
                    # Print ip and ro at the top of the file.
                    t.write("target --default--\n")
                    t.write("\tsnmp-host\t= " + row['ip'] + "\n")
                    t.write("\tsnmp-community\t= " + row['ro'] + "\n\n")
                    
                except IOError, (errno, errstr):
                    print "T%s: Could not open %s - %s" %(self.id, navfile, errstr)                    
                    continue

            # IF not, continue writing this row as an interface in the current device.
            if row['target']:
                row['target'] = re.sub("/","_",row['target'])
                descr = row['descr'] or ''
                t.write("target \"" + row['target'] + "\"\n")
                t.write("\tinterface-index\t= " + str(row['ifindex']) + "\n")
                t.write("\tshort-desc\t= \"" + descr + "\"\n\n")
            else:
                print "T%s: Could not find target %s" %(self.id, row['target'])
                continue

        # I wonder if we should have an "all"-target. It may be implemented here. Use an
        # array to keep all targets and loop it here. 

        t.close()
        

    def createTargettypes(self, thispath, targetlist):
        """
        Makes target-types based on the snmpoid-table for the netboxes
        in the targetlist.
        """

        # Temporar variable
        interface = False

        # Hash with mapping from target to ds'
        targetmapping = {}

        ttfile = thispath + "/" + targettypesfile
        try:
            t = open(ttfile, 'a')
            c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            print "T%s: Opened file %s successfully for writing." %(self.id, ttfile)
            t.write(disclaimer)

            print "T%s: Got the following targetlist:\n%s" %(self.id, targetlist)

            # For each entry in the targetlist, find oids in the database that it responds to.
            # Check with the oids in cricket-config (oids-dict) to see if we may add them, if
            # so make a targetType and ds-entry
            for entry in targetlist.keys():
                q = "SELECT * FROM netboxsnmpoid LEFT JOIN snmpoid USING (snmpoidid) WHERE netboxid = " + str(entry) + " AND (oidsource = 'Cricket' OR oidsource = 'mib-II')"
                if not interface:
                    q += " AND oidkey NOT LIKE 'if%' AND snmpoid NOT LIKE '1.3.6.1.2.1.%'"
                c.execute(q)

                targetmapping[targetlist[entry]] = []

                if c.rowcount > 0:
                    print "T%s: Writing targettype = %s" %(self.id, targetlist[entry])
                    t.write("targetType " + targetlist[entry] + "\n")

                    dss = []
                    for row in c.fetchall():
                        dboid = row['snmpoid']
                        #print "T%s: Got %s from database." %(self.id, dboid)

                        # If this oid was in the cricket-configfiles add it.
                        if oids[thispath].has_key(dboid):
                            #print "T%s: Adding %s (= %s) to %s" %(self.id, row['oidkey'], oids[thispath][dboid], targetlist[entry])
                            dss.append(row['oidkey'])
                            targetmapping[targetlist[entry]].append(row['oidkey'])
                        else:
                            #print "T%s: Could not find %s in the cricket-config" %(self.id, dboid)
                            pass

                    # Now we have all targettypes in the dss-array. Lets make a view based on that and the config-file "view-groups" in
                    # cricket-config/cricket/ directory.

                    d = {}
                    for o in dss:
                        v = views[o]
                        if d.has_key(v):
                            d[v].append(o)
                        else:
                            d[v] = []
                            d[v].append(o)
                    
                    t.write("\tds\t= \"" + ", ".join(dss) + "\"\n")
                    stringarr = []
                    for key in d.keys():
                        # Prints for instance 'cpu: cpu1min cpu5min'
                        stringarr.append(key + ": " + " ".join(d[key]))

                    # Joins all the strings into a view
                    t.write("\tview\t= \"" + ", ".join(stringarr) + "\"\n\n")

            t.close()
                
        except IOError, (errno, errstr):
            print "T%s: Could not open %s - %s" %(self.id, ttfile, errstr)

        return targetmapping
        

    def fillRRDdatabase (self, path, targets):
        """
        Fills the rrd-database based on the targets we have created.
        """

        (targetlist, targetmapping) = targets

        # TODO: Must use variable for cricket-data directory here
        path = path.replace("cricket-config", "cricket-data")

        c = conn.cursor()

        # rrd_file looks like this:
        # key, path, filename, step, subsystem, netboxid, key, value
        for entry in targetlist:
            filename = targetlist[entry] + ".rrd"

            # Check if this exists already
            q = "SELECT * FROM rrd_file WHERE path='%s' AND filename='%s'" %(path, filename)
            c.execute(q)

            if c.rowcount == 0:
                query = "INSERT INTO rrd_file (path, filename, step, subsystem, netboxid) VALUES "
                query += "('%s', '%s', 300, 'cricket', %s)" %(path, filename, entry)
                print query

                try: 
                    c.execute(query)
                except psycopg2.ProgrammingError, e:
                    print "ProgrammingError %s" %(e)

                # Get id of newly inserted tuple
                getid = "SELECT last_value FROM rrd_file_rrd_fileid_seq";
                c.execute(getid)
                dbid = c.fetchone()[0]

                conn.commit()
                
                print "Insert got id %s" %(dbid)

                # Insert the datasources for this target.
                number = 0
                for ds in targetmapping[targetlist[entry]]:
                    # rrd_datasource looks like this:
                    # name, descr, dstype, units, threshold, max, delimiter, thresholdstate
                    dsq = "INSERT INTO rrd_datasource (rrd_fileid, name, descr, dstype) VALUES "
                    dsq += "(%s, '%s', '%s', 'DERIVE')" %(dbid, 'ds' + str(number), ds)

                    print dsq

                    try:
                        c.execute(dsq)
                    except psycopg2.ProgrammingError, e:
                        print "ProgrammingError %s" %(e)

                    conn.commit()

                    # Cricket names each datasource ds0...dsx. Funny.
                    number += 1
                
            else:
                print "%s already exists in the database" %(targetlist[entry])

                

# Disclaimer to put in autogenerated files.
# TODO: Make sure disclaimer is only put once (and on the top) of a file.
disclaimer = "# This file is autogenerated by NAV. Any changes you do here will be\n# deleted when NAV autogenerates this file. If you want to add targets,\n# targettypes or any other Cricket-configuration, do it in some other\n# file. Remember that Cricket parses any file it finds except those\n# starting with ~ and . \n\n"


#Connecting to db
conn = nav.db.getConnection('default')

# path to cricket-config directory
# TODO: Use variables from the cricket-conf.pl file.
cricketpath = "/usr/local/nav/cricket/"
mainpath = cricketpath + "cricket/"
configpath = cricketpath + "cricket-config/"
configfile = ".makecc"
targetfile = "NAVconfig"
targettypesfile = "NAVtargettypes"
pool = findCricketdirs(configpath);

# Find all oids in the config-files, make a dict with them.
# oids[pathtodir][oid] = textoid
oids = {}
makeOIDhash(configpath)

views = {}
parseViewConfig(mainpath)
print "Made following views: %s" %(views)

print "\nDone finding directories, making & starting threads...\n"

# threadparameters
numthreads = 3
threads = [] # the thread-objects are put here

# Make and fill queue
q = Queue.Queue()
for item in pool:
    q.put(item)

# Start threads
for i in range(numthreads):
    print "Starting thread %s" %i
    t = makeCricketConfig(i, q)
    threads.append(t)
    t.start()

# Wait for threads to finish
for thread in threads:
    thread.join()

print "All threads done (used %.2f seconds)!" %(time.time() - starttime)
