"""
database

$Id: database.py,v 1.18 2002/07/02 18:44:33 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/Attic/database.py,v $
"""
import thread, jobmap
from psycopg import connect
from job import Event
from Queue import Queue

db = None

queue = Queue()
global mapper
mapper=jobmap.jobmap()

def startup(dsn):
	global db
	db = connect(dsn)
	db.autocommit(1)
	thread.start_new_thread(run,())
def run():
	c = db.cursor()
	while 1:
		statement = queue.get()
		c.execute(statement)
def newEvent(event):
	if event.status == event.UP:
		value = 100
	elif event.status == event.DOWN:
		value = 0
	else:
		raise "RealityError. Value should be Event.UP or Event.DOWN"
	
	statement = "INSERT INTO eventq (deviceid, boksid, eventtypeid, statefull, value, descr) values (%i, %i, '%s','t', %i, '%s' )" % (event.serviceid, event.boksid, event.TYPE, value, event.info.replace("'","\\'") )
	queue.put(statement)


def newVersion(serviceid,version):
	print "New version. Id: %i Version: %s" % (serviceid,version)
	statement = "UPDATE service SET version = '%s' where serviceid = %i" % (version,serviceid)
	queue.put(statement)
def getJobs(onlyactive = 1):
	c = db.cursor()
	query = """SELECT serviceid, property, value
	FROM serviceproperty
	order by serviceid"""
	c.execute(query)

	property = {}
	for serviceid,prop,value in c.fetchall():
		if serviceid not in property:
			property[serviceid] = {}
		property[serviceid][prop] = value

	query = """SELECT serviceid ,service.boksid, service.active, handler, version, ip
	FROM service JOIN boks ON (service.boksid=boks.boksid) order by serviceid"""
	c.execute(query)
	jobs = []
	for serviceid,boksid,active,handler,version,ip in c.fetchall():
		job = mapper.get(handler)
		if not job:
			print 'no such handler:',handler
		newJob = job(serviceid,boksid,ip,property.get(serviceid,{}),version)
		if onlyactive and not active:
			continue
		else:
			setattr(newJob,'active',active)

		jobs += [newJob]
	db.commit()
	return jobs

