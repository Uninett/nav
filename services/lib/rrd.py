"""
create and update rrd-objects

$Authour$
$Id: rrd.py,v 1.1 2002/06/17 16:25:47 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/rrd.py,v $
"""
from RRDtool import RRDtool
rrd = RRDtool()
def create(serviceid):
	rrd.create(('%i.rrd' % (serviceid),'-s 300','DS:STATUS:GAUGE:600:0:1','DS:REPONSETIME:GAUGE:600:0:300','RRA:AVERAGE:0.5:1:288','RRA:AVERAGE:0.5:6:336','RRA:AVERAGE:0.5:12:720','RRA:MAX:0.5:12:720','RRA:AVERAGE:0.5:288:365','RRA:MAX:0.5:288:365','RRA:AVERAGE:0.5:288:1095','RRA:MAX:0.5:288:1095'))
def update(serviceid,time,status,responsetime):
	rrd.update(('%i.rrd' % (serviceid),str(time) + ':' + str(status) + ':' + str(responsetime)))
