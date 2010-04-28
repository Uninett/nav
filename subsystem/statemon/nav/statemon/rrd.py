# -*- coding: ISO8859-1 -*-
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
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Erik Gorset  <erikgors@stud.ntnu.no>
#
"""
Module for creating and updating rrd-objects
"""
import os
import event
from debug import debug
import rrdtool as rrd
import db
import config

try:
    import nav.path
    RRDDIR = nav.path.localstatedir + '/rrd'
except:
    # Not properly installed
    RRDDIR = '/var/rrd'
database = db.db()

def create(filename, netboxid, serviceid=None, handler=""):
    step = 300
    
    if RRDDIR and not os.path.exists(RRDDIR):
        os.mkdir(RRDDIR)
    tupleFromHell = (str(os.path.join(RRDDIR,filename)),
             '-s %s' % step,
             'DS:STATUS:GAUGE:600:0:1',
             'DS:RESPONSETIME:GAUGE:600:0:300',
             'RRA:AVERAGE:0.5:1:288',
             'RRA:AVERAGE:0.5:6:336',
             'RRA:AVERAGE:0.5:12:720',
             'RRA:MAX:0.5:12:720',
             'RRA:AVERAGE:0.5:288:365',
             'RRA:MAX:0.5:288:365',
             'RRA:AVERAGE:0.5:288:1095',
             'RRA:MAX:0.5:288:1095')
    rrd.create(*tupleFromHell)
    debug("Created rrd file %s" % filename)

    # a bit ugly...
    if serviceid:
        key="serviceid"
        val=serviceid
        subsystem = "serviceping"
        statusdescr = "%s availability" % handler
        responsedescr = "%s responsetime" % handler
        unit = '-100%'
    else:
        key=""
        val=""
        subsystem= "pping"
        statusdescr = "Packet loss"
        responsedescr = "Roundtrip time"
        unit = '100%'
    rrd_fileid = database.registerRrd(RRDDIR, filename, step, netboxid,
                      subsystem, key, val)
    database.registerDS(rrd_fileid, "RESPONSETIME",
                responsedescr, "GAUGE", "s")

    database.registerDS(rrd_fileid, "STATUS", statusdescr, "GAUGE", unit)

def update(netboxid,sysname,time,status,responsetime,serviceid=None,handler=""):
    """
    time: 'N' or time.time()
    status: 'UP' or 'DOWN' (from Event.status)
    responsetime: 0-300 or '' (undef)
    """
    if serviceid:
        filename = '%s.%s.rrd' % (sysname, serviceid)
        # typically ludvig.ntnu.no.54.rrd
    else:
        filename = '%s.rrd' % (sysname)
        # typically ludvig.ntnu.no.rrd
    
    os.path.exists(os.path.join(RRDDIR, filename)) or \
               create(filename, netboxid, serviceid,handler)
    if status == event.Event.UP:
        rrdstatus = 0
    else:
        rrdstatus = 1
    
    rrdParam = (str(os.path.join(RRDDIR,filename)),
            '%s:%i:%s' % (time, rrdstatus, responsetime))
    rrd.update(*rrdParam)
    debug("Updated %s" % filename, 7)
