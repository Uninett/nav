"""
$Id: rrd.py,v 1.1 2003/03/26 16:01:44 magnun Exp $                                                                                                                              
This file is part of the NAV project.

Module for creating and updating rrd-objects

Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Erik Gorset	<erikgors@stud.ntnu.no>
"""


import os
from RRDtool import RRDtool
from job import Event
rrd = RRDtool()
RRDDIR = '/var/rrd'
def create(serviceid):
	if RRDDIR and not os.path.exists(RRDDIR):
		os.mkdir(RRDDIR)
	rrd.create(('%s/%s.rrd' % (RRDDIR,serviceid),'-s 300','DS:STATUS:GAUGE:600:0:1','DS:RESPONSETIME:GAUGE:600:0:300','RRA:AVERAGE:0.5:1:288','RRA:AVERAGE:0.5:6:336','RRA:AVERAGE:0.5:12:720','RRA:MAX:0.5:12:720','RRA:AVERAGE:0.5:288:365','RRA:MAX:0.5:288:365','RRA:AVERAGE:0.5:288:1095','RRA:MAX:0.5:288:1095'))

def update(serviceid,time,status,responsetime):
	"""
	time: 'N' or time.time()
	status: 'UP' or 'DOWN' (from Event.status)
	responsetime: 0-300 or '' (undef)
	"""
	filename = '%s/%s.rrd' % (RRDDIR,serviceid)
	os.path.exists(filename) or create(serviceid)
	if status == Event.UP:
		rrdstatus=0
	else:
		rrdstatus = 1
		
	rrd.update((filename,'%s:%i:%s' % (time, rrdstatus, responsetime)))
