"""
database

$Author: erikgors $
$Id: database.py,v 1.4 2002/06/13 15:04:21 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/Attic/database.py,v $
"""
import thread
from psycopg import connect
from job import Event,jobmap
from Queue import Queue

db = None

queue = Queue()

def startup(dsn):
	global db
	db = connect(dsn)
	thread.start_new_thread(run,())
def run():
	c = db.cursor()
	while 1:
		statement = queue.get()
		c.execute(statement)
def newEvent(event):
	print 'new event:',event.id,event.status,event.info
def newVersion(id,version):
	statement = "UPDATE service SET version = '%s' where id = %i" % (id,version)
	queue.put(statement)
def getJobs():
	c = db.cursor()
	query = """SELECT serviceid, property, value
	FROM serviceproperty
	order by serviceid"""
	c.execute(query)
	property = {}
	for id,prop,value in c.fetchall():
		if id not in property:
			property[id] = {}
		property[id][prop] = value

	query = 'SELECT serviceid, handler, version, ip FROM service NATURAL JOIN boks order by serviceid'
	c.execute(query)
	jobs = []
	for id,handler,version,ip in c.fetchall():
		job = jobmap.get(handler,'')
		if not job:
			print 'no such handler:',handler
		newJob = job(id,ip,property.get(id,{}),version)
		jobs += [newJob]
	return jobs


if __name__ == '__main__':
	startup('host = localhost user = manage dbname = manage password = eganam')
	jobs = getJobs()
	for i in jobs:
		print jobs
