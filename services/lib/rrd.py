"""
create and update rrd-objects

$Id: rrd.py,v 1.6 2002/11/28 22:07:34 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/rrd.py,v $
"""
import os
from RRDtool import RRDtool
from job import Event
rrd = RRDtool()
RRDDIR = 'rrd'
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
	#print "rrdfil: %s %i" % (filename, os.path.exists(filename))
	#print "Box: %s responsetime: %s" % (serviceid,responsetime)
	os.path.exists(filename) or create(serviceid)
	if status == Event.UP:
		rrdstatus=0
	else:
		rrdstatus = 1
		
	rrd.update((filename,'%s:%i:%s' % (time, rrdstatus, responsetime)))
