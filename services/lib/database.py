"""
database

$Author: erikgors $
$Id: database.py,v 1.1 2002/06/13 09:57:58 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/Attic/database.py,v $
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
