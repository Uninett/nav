"""
database

$Id: database.py,v 1.19 2002/07/04 14:57:12 magnun Exp $
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
		state = 'f'
	elif event.status == event.DOWN:
		value = 0
		state = 'f'
	else:
		pass

	s = db.cursor()
	s.execute("SELECT nextval('eventq_eventqid_seq')")
	nextid = s.fetchall()[0][0]
	print "Nextid: ", nextid
	statement = "INSERT INTO eventq (eventqid, subid, boksid, eventtypeid, state, value) values (%i, %i, %i, '%s','%s', %i )" % (nextid, event.serviceid, event.boksid, event.TYPE, state, value)
	#queue.put(statement)
	s.execute(statement)
	statement = "INSERT INTO eventqvar (eventqid, var, value) values (%i, '%s', '%s')" % (nextid, 'descr',event.info.replace("'","\\'"))
	s.execute(statement)
											     


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

