"""
create and update rrd-objects

$Id: rrd.py,v 1.5 2002/06/21 09:25:05 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/rrd.py,v $
"""
import os
from RRDtool import RRDtool
from job import Event
rrd = RRDtool()
RRDDIR = 'rrd'
def create(serviceid):
	if RRDDIR and not os.path.exists(RRDDIR):
		os.mkdir(RRDDIR)
	rrd.create(('%s/%i.rrd' % (RRDDIR,serviceid),'-s 300','DS:STATUS:GAUGE:600:0:1','DS:REPONSETIME:GAUGE:600:0:300','RRA:AVERAGE:0.5:1:288','RRA:AVERAGE:0.5:6:336','RRA:AVERAGE:0.5:12:720','RRA:MAX:0.5:12:720','RRA:AVERAGE:0.5:288:365','RRA:MAX:0.5:288:365','RRA:AVERAGE:0.5:288:1095','RRA:MAX:0.5:288:1095'))
def update(serviceid,time,status,responsetime):
	"""
	time: 'N' or time.time()
	status: 'UP' or 'DOWN' (from Event.status)
	responsetime: 0-300 or '' (undef)
	"""
	filename = '%s/%i.rrd' % (RRDDIR,serviceid)
	os.path.exists(filename) or create(serviceid)
	rrd.update((filename,'%s:%i:%s' % (time, status == Event.UP and 100, responsetime)))
