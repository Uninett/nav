"""
database

$Author: erikgors $
$Id: database.py,v 1.2 2002/06/13 13:04:01 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/database.py,v $
"""
from psycopg import connect
from job import Event

db = None


def startup(dsn):
	global db
	db = connect(dsn)
def newEvent(event):
	print 'new event:',event.id,event.status,event.info
def newVersion(id,version):
	print 'new version:',id,version
def getJobs():
	query = 'SELECT serviceid, handler, version, ip FROM service NATURAL JOIN boks order by serviceid'
	c = db.cursor()
	c.execute(query)
	for i in c.getall():
		print i
if __name__ == '__main__':
	startup('host = localhost user = jee dbname = weather password = oops')
	getJobs()
