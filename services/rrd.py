"""
create and update rrd-objects

$Authour$
$Id: rrd.py,v 1.3 2002/06/19 10:35:15 erikgors Exp $
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
	if status == Event.UP:
		status = 0
		responsetime = str(responsetime)
	else:
		status = 1
		responsetime = ''
	if not os.path.exists('%s/%i.rrd' % (RRDDIR,serviceid)):
		create(serviceid)
	rrd.update(('%s/%i.rrd' % (RRDDIR,serviceid),'%s:%i:%s' % (str(time), status, responsetime)))
