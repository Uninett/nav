"""
$Id: db.py,v 1.5 2002/07/25 16:53:39 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/db.py,v $

This class is an abstraction of the database operations needed
by the service monitor.

It implements the singleton pattern, ensuring only one instance
is used at a time.
"""
import threading, jobmap, psycopg, Queue, job, debug
from setup import Service


def db(conf):
	if _db._instance is None:
		_db._instance=_db(conf)

	return _db._instance

class _db(threading.Thread):
	_instance=None
	def __init__(self, conf):
		threading.Thread.__init__(self)
		self.mapper=jobmap.jobmap()
		self.debug=debug.debug()
		self.db=psycopg.connect("host = %s user = %s dbname = %s password = %s" % (conf["dbhost"],"manage",conf["db_nav"],conf["userpw_manage"]))
		self.db.autocommit(1)
		self.cursor=self.db.cursor()
		self.sysboks()
		self.setDaemon(1)
		self.queue = Queue.Queue()

	def run(self):
		while 1:
			event = self.queue.get()
			self.commitEvent(event)

        def sysboks(self):
		s = self.query('select sysname,boksid from boks')
		self.boks = dict(s)
						
	def query(self, statement):
		try:
			self.cursor.execute(statement)
			return self.cursor.fetchall()
		except psycopg.DatabaseError, psycopg.InterfaceError:
			self.debug.log("Could not execute query: %s" % statement, 2)
			return []

	def execute(self, statement):
		try:
			self.cursor.execute(statement)
		except psycopg.DatabaseError, psycopg.InterfaceError:
			self.debug.log("Could not execute statement: %s" % statement, 2)

	def newEvent(self, event):
		self.queue.put(event)

	def commitEvent(self, event):
		if event.status == event.UP:
			value = 100
			state = 'e'
		elif event.status == event.DOWN:
			value = 1
			state = 's'
		else:
			pass

		nextid = self.query("SELECT nextval('eventq_eventqid_seq')")[0][0]

		statement = "INSERT INTO eventq (eventqid, subid, boksid, eventtypeid, state, value, source, target) values (%i, %i, %i, '%s','%s', %i, '%s','%s' )" % (nextid, event.serviceid, event.boksid, event.TYPE, state, value,"serviceping","eventEngine")
		self.execute(statement)
		statement = "INSERT INTO eventqvar (eventqid, var, val) values (%i, '%s', '%s')" % (nextid, 'descr',event.info.replace("'","\\'"))
		self.execute(statement)


	def pingEvent(self, host, state):
		query = "SELECT boksid FROM boks WHERE ip='%s'"%host
		boksid=self.query(query)[0][0]

		if state == 'UP':
			state = 'e'
			value = 100
		else:
			state = 's'
			value = 0

		statement = "INSERT INTO eventq (boksid, eventtypeid, state, value, source, target) values (%i, '%s','%s', %i, '%s','%s' )" % (boksid, "boxState", state, value,"pping","eventEngine")
		self.execute(statement)

	def newVersion(self, serviceid, version):
		print "New version. Id: %i Version: %s" % (serviceid,version)
		statement = "UPDATE service SET version = '%s' where serviceid = %i" % (version,serviceid)
		self.execute(statement)
		self.db.commit()
		self.db.autocommit(1)

	def hostsToPing(self):
		query="""SELECT ip FROM boks WHERE active='t' """
		return self.query(query)

	def getJobs(self, onlyactive = 1):
		query = """SELECT serviceid, property, value
		FROM serviceproperty
		order by serviceid"""
		
		property = {}
		for serviceid,prop,value in self.query(query):
			if serviceid not in property:
				property[serviceid] = {}
			property[serviceid][prop] = value

		query = """SELECT serviceid ,service.boksid, service.active, handler, version, ip
		FROM service JOIN boks ON (service.boksid=boks.boksid) order by serviceid"""

		jobs = []
		for serviceid,boksid,active,handler,version,ip in self.query(query):
			job = self.mapper.get(handler)
			if not job:
				print 'no such handler:',handler
			newJob = job(serviceid,boksid,ip,property.get(serviceid,{}),version)
			if onlyactive and not active:
				continue
			else:
				setattr(newJob,'active',active)

			jobs += [newJob]

		return jobs


	def getServices(self):
		services = []
		
		for i in self.getJobs(0):
			serviceid = i.getServiceid()
			active = (i.active and 'true') or 'false'
			boksid = i.getBoksid()
			for j in self.boks:
				if self.boks[j] == boksid:
					sysname = j
					break
			handler = i.getType()
			args = i.getArgs()
			
			new = Service(sysname, handler, args, serviceid)
			services += [new]
		services.sort()
		return services
			

	def deleteService(self,service):
		print "serviceid: %s" % service
		self.execute("DELETE FROM service WHERE serviceid = '%s'" % service.id)

	def insertService(self,service):
		next = self.query("select nextval('service_serviceid_seq')")[0][0]
		self.execute("INSERT INTO service (serviceid,boksid,handler) VALUES (%s,%s,'%s')" % (next, self.boks[service.sysname], service.handler))
		service.id = next
		self.insertServiceArgs(service)						
        def insertServiceArgs(self,service):
		self.execute('DELETE FROM serviceproperty WHERE serviceid = %s' % service.id)
		for prop,value in service.args.items():
			self.execute("INSERT INTO serviceproperty (serviceid,property,value) values (%s,'%s','%s')" % (service.id,prop,value))
										
