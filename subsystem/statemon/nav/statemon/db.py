"""
$Id: db.py,v 1.8 2003/06/25 15:04:44 magnun Exp $
This file is part of the NAV project.

This class is an abstraction of the database operations needed
by the service monitor.

It implements the singleton pattern, ensuring only one instance
is used at a time.

Copyright (c) 2002 by NTNU, ITEA nettgruppen                               
Author: Magnus Nordseth <magnun@stud.ntnu.no>
	Erik Gorset	<erikgors@stud.ntnu.no>
"""

import threading, checkermap, psycopg, Queue,  time
from event import Event
from service import Service
from debug import debug


def db(conf):
	if _db._instance is None:
		_db._instance=_db(conf)

	return _db._instance

class _db(threading.Thread):
	_instance=None
	def __init__(self, conf):
		threading.Thread.__init__(self)
		self.conf = conf
		self.connect()
		self.db.autocommit(0)
		self.sysnetbox()
		self.setDaemon(1)
		self.queue = Queue.Queue()
	def connect(self):
		try:
			self.db = psycopg.connect("host = %s user = %s dbname = %s password = %s"
						  % (self.conf["dbhost"],
						     "manage"
						     ,self.conf["db_nav"],
						     self.conf["userpw_manage"]))
		except Exception, e:
			debug("Couldn't connect to db.", 2)
			debug(str(e),2)
			self.db=None
	
	def cursor(self):
		cursor = self.db.cursor()
		try:
			# this is a very dirty workaround...
			cursor.execute('SELECT 1')
		except:
			debug("Could not get cursor. Trying to reconnect...", 2)
			self.connect()
			cursor = self.db.cursor()
		return cursor

	def run(self):
		while 1:
			event = self.queue.get()
			self.commitEvent(event)
			self.db.commit()

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
		
	def query(self, statement, commit=1):
		try:
			cursor=self.cursor()
			debug("Executeing: %s" % statement,7)
			cursor.execute(statement)
			if commit:
				self.db.commit()
			return cursor.fetchall()
		except psycopg.DatabaseError, e:
			debug("Could not execute query: %s" % statement, 2)
			debug(str(e))
			if commit:
				self.db.rollback()
			return []
		except psycopg.InterfaceError, e:
			debug("Could not execute query: %s" % statement, 2)
			debug(str(e))
			if commit:
				self.db.rollback()
			return []
	def execute(self, statement, commit=1):
		try:
			cursor=self.cursor()
			debug("Executeing: %s" % statement,7)
			cursor.execute(statement)
			if commit:
				self.db.commit()
		except psycopg.DatabaseError, e:
			debug("Could not execute statement: %s" % statement, 2)
			debug(str(e))
			if commit:
				self.db.rollback()
		except psycopg.InterfaceError, e:
			debug("Could not execute statement: %s" % statement, 2)
			debug(str(e))
			if commit:
				self.db.rollback()

	def newEvent(self, event):
		self.queue.put(event)

	def commitEvent(self, event):
		if event.eventtype == "version":
			statement = "UPDATE service SET version = '%s' where serviceid = %i" % (event.version, event.serviceid)
			self.execute(statement)
			return
		
		if event.status == Event.UP:
			value = 100
			state = 'e'
		elif event.status == Event.DOWN:
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
		debug("Executed: %s" % statement)

	def pingEvent(self, host, state):
		if state == 'UP':
			state = 'e'
			value = 100
		else:
			state = 's'
			value = 0

		statement = "INSERT INTO eventq (netboxid, deviceid, eventtypeid, state, value, source, target) values (%i, %i, '%s','%s', %i, '%s','%s' )" % (host.netboxid, host.deviceid, "boxState", state, value,"pping","eventEngine")
		self.execute(statement)
		

	def newVersion(self, serviceid, version):
		debug( "New version. Id: %i Version: %s" % (serviceid,version))
		statement = "UPDATE service SET version = '%s' where serviceid = %i" % (version,serviceid)

	def hostsToPing(self):
		#query="""SELECT ip,sysname FROM netbox """
		query = """SELECT netboxid, deviceid, sysname, ip, up FROM netbox """
		return self.query(query)

	def getCheckers(self, useDbStatus, onlyactive = 1):
		query = """SELECT serviceid, property, value
		FROM serviceproperty
		order by serviceid"""
		
		property = {}
		for serviceid,prop,value in self.query(query):
			if serviceid not in property:
				property[serviceid] = {}
			if value:
				property[serviceid][prop] = value

		fromdb = []
		query = """SELECT serviceid ,service.netboxid, service.active,
		handler, version, ip, sysname, service.up FROM service JOIN netbox ON
		(service.netboxid=netbox.netboxid) order by serviceid"""
		map(fromdb.append, self.query(query))
		
		checkers = []
		for each in fromdb:
			if len(each) == 8:
				serviceid,netboxid,active,handler,version,ip,sysname,up = each
			else:
				debug("Invalid checker: %s" % each,2)
				continue
			checker = checkermap.get(handler)
			if not checker:
				debug("no such checker: %s" % handler,2)
				continue
			service={'id':serviceid,
				 'netboxid':netboxid,
				 'ip':ip,
				 'sysname':sysname,
				 'args':property.get(serviceid,{}),
				 'version':version
				 }
			if useDbStatus:
				if up == 'y':
					up=Event.UP
				else:
					up=Event.DOWN
				newChecker = checker(service, status=up)
			else:
				newChecker = checker(service)
			if onlyactive and not active:
				continue
			else:
				setattr(newChecker,'active',active)

			checkers += [newChecker]

		return checkers


	def getServices(self):
		services = []
		
		for i in self.getCheckers(0):
			serviceid = i.getServiceid()
			active = (i.active and 'true') or 'false'
			netboxid = i.getNetboxid()
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
			
	def registerRrd(self, path, filename, step, netboxid, subsystem, key="",val=""):
		rrdid = self.query("SELECT nextval('rrd_file_rrd_fileid_seq')")[0][0]
		if key and val:
			statement = """INSERT INTO rrd_file
			(rrd_fileid, path, filename, step, netboxid, key, value, subsystem) values
			(%s, '%s','%s',%s,%s,'%s',%s,'%s')""" %	(rrdid, path, filename,
								 step, netboxid, key, val, subsystem)
		else:
			statement = """INSERT INTO rrd_file
			(rrd_fileid, path, filename, step, netboxid, subsystem) VALUES
			(%s,'%s','%s',%s,%s,'%s')""" %(rrdid, path, filename,
						       step, netboxid, subsystem)
		self.execute(statement)
		return rrdid
	def registerDS(self, rrd_fileid, name, descr, dstype, unit):
		statement = """INSERT INTO rrd_datasource
		(rrd_fileid, name, descr, dstype, units) VALUES
		(%s, '%s', '%s', '%s', '%s')""" % (rrd_fileid, name, descr, dstype, unit)
		self.execute(statement)
		
		
	def deleteService(self,service):
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
										
