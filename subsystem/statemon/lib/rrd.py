"""
$Id: rrd.py,v 1.5 2003/06/25 15:04:44 magnun Exp $                                                                                                                              
This file is part of the NAV project.

Module for creating and updating rrd-objects

Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Erik Gorset	<erikgors@stud.ntnu.no>
"""


import os
import event
from debug import debug
import rrdtool as rrd
import db
import config

RRDDIR = '/var/rrd'
database = db.db(config.dbconf())

def create(filename, netboxid, serviceid=None, handler=""):
	step = 300
	
	if RRDDIR and not os.path.exists(RRDDIR):
		os.mkdir(RRDDIR)
	tupleFromHell = ('%s' % (os.path.join(RRDDIR,filename)),
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
		unit = '-%'
	else:
		key=""
		val=""
		subsystem= "pping"
		statusdescr = "Packet loss"
		responsedescr = "Roundtrip time"
		unit = '%'
	rrd_fileid = database.registerRrd(RRDDIR, filename, step, netboxid, subsystem, key, val)
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

	os.path.exists(os.path.join(RRDDIR, filename)) or create(filename, netboxid, serviceid,handler)
	if status == event.Event.UP:
		rrdstatus = 0
	else:
		rrdstatus = 1
	
	rrdParam = (os.path.join(RRDDIR,filename),'%s:%i:%s' % (time, rrdstatus, responsetime))
	rrd.update(*rrdParam)
	debug("Updated %s" % filename, 7)
