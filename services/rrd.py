"""
create and update rrd-objects

$Authour$
$Id: rrd.py,v 1.2 2002/06/18 15:07:54 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/rrd.py,v $
"""
from RRDtool import RRDtool
from job import Event
rrd = RRDtool()
def create(serviceid):
	rrd.create(('%i.rrd' % (serviceid),'-s 300','DS:STATUS:GAUGE:600:0:1','DS:REPONSETIME:GAUGE:600:0:300','RRA:AVERAGE:0.5:1:288','RRA:AVERAGE:0.5:6:336','RRA:AVERAGE:0.5:12:720','RRA:MAX:0.5:12:720','RRA:AVERAGE:0.5:288:365','RRA:MAX:0.5:288:365','RRA:AVERAGE:0.5:288:1095','RRA:MAX:0.5:288:1095'))
def update(serviceid,time,status,responsetime):
	if status == Event.UP:
		status = 0
		responsetime = str(responsetime)
	else:
		status = 1
		responsetime = ''
	rrd.update(('%i.rrd' % (serviceid),'%s:%i:%s' % (str(time), status, responsetime)))
