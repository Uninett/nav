"""
$Id: db.py,v 1.13 2003/01/03 19:19:55 magnun Exp $                                                                                                                              
This file is part of the NAV project.

This class is an abstraction of the database operations needed
by the service monitor.

It implements the singleton pattern, ensuring only one instance
is used at a time.

Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Magnus Nordseth <magnun@stud.ntnu.no>
	Erik Gorset	<erikgors@stud.ntnu.no>
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
		self.sysnetbox()
		self.setDaemon(1)
		self.queue = Queue.Queue()

	def run(self):
		while 1:
			event = self.queue.get()
			self.commitEvent(event)

        def sysnetbox(self):
		"""
		sysname -> netboxid mapping
		"""
		s = self.query('select sysname,netboxid from netbox')
		self.netbox = dict(s)

	def getnetboxid(self):
		"""
		netboxid -> sysname mapping
		"""
		s = self.query('select netboxid, sysname from netbox')
		self.netboxid = dict(s)
		
	def query(self, statement):
		try:
			cursor=self.db.cursor()
			self.debug.log("Executeing: %s" % statement,7)
			cursor.execute(statement)
			return cursor.fetchall()
		except psycopg.DatabaseError, psycopg.InterfaceError:
			self.debug.log("Could not execute query: %s" % statement, 2)
			return []

	def execute(self, statement):
		try:
			cursor=self.db.cursor()
			self.debug.log("Executeing: %s" % statement,7)
			cursor.execute(statement)
		except psycopg.DatabaseError, psycopg.InterfaceError:
			self.debug.log("Could not execute statement: %s" % statement, 2)

	def newEvent(self, event):
		self.queue.put(event)

	def commitEvent(self, event):
		if event.eventtype == "version":
			statement = "UPDATE service SET version = '%s' where serviceid = %i" % (event.version, event.serviceid)
			self.execute(statement)
			return
		
		if event.status == event.UP:
			value = 100
			state = 'e'
		elif event.status == event.DOWN:
			value = 1
			state = 's'
		else:
			pass

		query = "SELECT deviceid FROM netbox WHERE netboxid='%s' "%event.netboxid
		deviceid=self.query(query)[0][0]
		
		nextid = self.query("SELECT nextval('eventq_eventqid_seq')")[0][0]
		if not event.netboxid:
			statement = """INSERT INTO eventq
(eventqid, subid, netboxid, deviceid, eventtypeid, state, value, source, target)
values (%i, %i, %s, %i, '%s','%s', %i, '%s','%s' )""" % (nextid, event.serviceid, 'NULL', deviceid, event.eventtype, state, value,  "serviceping","eventEngine")
		else:
			statement = """INSERT INTO eventq
(eventqid, subid, netboxid, deviceid, eventtypeid, state, value, source, target)
values (%i, %i, %i,%i, '%s','%s', %i, '%s','%s' )""" % (nextid, event.serviceid, event.netboxid, deviceid, event.eventtype, state, value,  "serviceping","eventEngine")
		self.execute(statement)
		statement = "INSERT INTO eventqvar (eventqid, var, val) values (%i, '%s', '%s')" % (nextid, 'descr',event.info.replace("'","\\'"))
		self.execute(statement)


	def pingEvent(self, host, state):
		query = "SELECT netboxid, deviceid FROM netbox WHERE ip='%s'"%host
		netboxid, deviceid=self.query(query)[0][0:2]
		self.debug.log("Found netboxid=%s, deviceid=%s from ip=%s"%(netboxid,deviceid,host),7)

		if state == 'UP':
			state = 'e'
			value = 100
		else:
			state = 's'
			value = 0

		statement = "INSERT INTO eventq (netboxid, deviceid, eventtypeid, state, value, source, target) values (%i, %i, '%s','%s', %i, '%s','%s' )" % (netboxid, deviceid, "boxState", state, value,"pping","eventEngine")
		self.execute(statement)

	def newVersion(self, serviceid, version):
		self.debug.log( "New version. Id: %i Version: %s" % (serviceid,version))
		statement = "UPDATE service SET version = '%s' where serviceid = %i" % (version,serviceid)

	def hostsToPing(self):
		query="""SELECT DISTINCT ip FROM netbox """
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

		fromdb = []
		query = """SELECT serviceid ,service.netboxid, service.active,
		handler, version, ip, sysname FROM service JOIN netbox ON
		(service.netboxid=netbox.netboxid) order by serviceid"""
		map(fromdb.append, self.query(query))
		
		jobs = []
		for each in fromdb:
			if len(each) == 7:
				serviceid,netboxid,active,handler,version,ip,sysname = each
			else:
				self.debug("Invalid job: %s" % each,2)
				continue
			job = self.mapper.get(handler)
			if not job:
				self.debug("no such handler: %s",handler,2)
				continue
			service={'id':serviceid,
				 'netboxid':netboxid,
				 'ip':ip,
				 'sysname':sysname,
				 'args':property.get(serviceid,{}),
				 'version':version
				 }
			newJob = job(service)
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
			netboxid = i.getBoksid()
			if not netboxid:
				sysname='None'
			else:
				for j in self.netbox:
					if self.netbox[j] == netboxid:
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
		if service.sysname == "None":
			netboxid="NULL"
		else:
			try:
				netboxid=self.netbox[service.sysname]
			except KeyError:
				print "%s is not defined in the NAV database" % service.sysname
				return
		
		self.execute("INSERT INTO service (serviceid,netboxid,handler) VALUES (%s,%s,'%s')" % (next, netboxid, service.handler))
			
		service.id = next
		self.insertServiceArgs(service)						
        def insertServiceArgs(self,service):
		self.execute('DELETE FROM serviceproperty WHERE serviceid = %s' % service.id)
		for prop,value in service.args.items():
			self.execute("INSERT INTO serviceproperty (serviceid,property,value) values (%s,'%s','%s')" % (service.id,prop,value))
										
