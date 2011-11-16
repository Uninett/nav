#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2010 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
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
RRD_STEP = 300
database = db.db()

def create(filename, netboxid, serviceid=None, handler=""):
    if RRDDIR and not os.path.exists(RRDDIR):
        os.mkdir(RRDDIR)
    tupleFromHell = (str(os.path.join(RRDDIR, filename)),
             '-s %s' % RRD_STEP,
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
    verify_rrd_registry(filename, netboxid, serviceid, handler)

def register_rrd(filename, netboxid, serviceid=None, handler=""):
    """Registers an RRD file in the db registry."""
    if serviceid:
        key = "serviceid"
        val = serviceid
        subsystem = "serviceping"
        statusdescr = "%s availability" % handler
        responsedescr = "%s responsetime" % handler
        unit = '-100%'
    else:
        key = ""
        val = ""
        subsystem = "pping"
        statusdescr = "Packet loss"
        responsedescr = "Roundtrip time"
        unit = '100%'
    rrd_fileid = database.registerRrd(RRDDIR, filename, RRD_STEP, netboxid,
                      subsystem, key, val)
    database.registerDS(rrd_fileid, "RESPONSETIME",
                responsedescr, "GAUGE", "s")

    database.registerDS(rrd_fileid, "STATUS", statusdescr, "GAUGE", unit)

def verify_rrd_registry(filename, netboxid, serviceid=None, handler=""):
    """Verifies that an RRD file is known in the RRD registry.

    If the file is known, but disconnected, it will be reconnected.  If the
    file is unknown, it will be registered from scratch.

    """
    try:
        registered_netboxid = database.verify_rrd(RRDDIR, filename)
    except db.UnknownRRDFileError, e:
        register_rrd(filename, netboxid, serviceid, handler)
    else:
        if registered_netboxid is None:
            database.reconnect_rrd(RRDDIR, filename, netboxid)
        # We don't handle the unusual case where a netboxid in the db differs
        # from the one we are working with
    return True


def update(netboxid, sysname, time, status, responsetime, serviceid=None,
           handler=""):
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

    if os.path.exists(os.path.join(RRDDIR, filename)):
        verify_rrd_registry(filename, netboxid, serviceid, handler)
    else:
        create(filename, netboxid, serviceid, handler)
    if status == event.Event.UP:
        rrdstatus = 0
    else:
        rrdstatus = 1

    rrdParam = (str(os.path.join(RRDDIR, filename)),
            '%s:%i:%s' % (time, rrdstatus, responsetime))
    try:
        rrd.update(*rrdParam)
    except Exception, e:
        debug("Failed to update %s" % filename, 7)
        debug("Exception: %s" % e)
    else:
        debug("Updated %s" % filename, 7)
