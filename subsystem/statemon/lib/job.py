"""
$Id: job.py,v 1.6 2003/06/15 11:28:56 magnun Exp $                                                                                                                              
This file is part of the NAV project.                                                                                             
                                                                                                                                 
Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Magnus Nordseth <magnun@stud.ntnu.no>
        Erik Gorset     <erikgors@stud.ntnu.no>
"""
import time,socket,sys,types,config,debug,mailAlert, RunQueue
import event
import db
import rrd
from select import select
from errno import errorcode
from Socket import Socket

TIMEOUT = 5 #default, hardcoded timeout :)
DEBUG=0

class JobHandler:
	def __init__(self,type,service,status=event.Event.UP):
		self._conf=config.serviceconf()
		self.setType(type)
		self.setServiceid(service['id'])
		self.setIp(service['ip'])
		self.setNetboxid(service['netboxid'])
		self.setArgs(service['args'])
		self.setVersion(service['version'])
		self.setSysname(service['sysname'])
		# This is (and should be) used by all subclasses
		self.setPort(int(service['args'].get('port', 0)))
		self.setStatus(status)
		self.setTimestamp(0)
		timeout = self.getArgs().get('timeout', self._conf.get("%s timeout" % self.getType(), self._conf.get('timeout',TIMEOUT)))
		self.setTimeout(int(timeout))
		self.db=db.db(config.dbconf())
		self.debug=debug.debug()
		self.alerter=mailAlert.mailAlert()
		self.debug.log("New job instance for %s:%s " % (self.getSysname(), self.getType()),6)
		self.runcount=0
		self.rq=RunQueue.RunQueue()
		
	def run(self):
		"""
		Calls executeTest(). If the status has changed it schedules a new
		test. If the service has been unavailable for more than self.runcount
		times, it marks the service as down.
		"""
		version = self.getVersion()
		status, info = self.executeTest()
		service="%s:%s" % (self.getSysname(), self.getType())
		self.debug.log("%-20s -> %s" % (service, info), 6)

		if status != self.getStatus() and self.runcount < int(self._conf.get('retry',3)):
			delay = int(self._conf.get('retry delay',5))
			self.runcount+=1
			self.debug.log("%-20s -> State changed. Scheduling new check in %i sec..." % (service, delay))
			# Updates rrd every time to get proper 'uptime' for the service
			try:
				rrd.update(self.getServiceid(),'N',self.getStatus(),self.getResponsetime())
			except Exception,e:
				self.debug.log("rrd update failed for %s [%s]" % (service,e),3)
			priority=delay+time.time()
			# Queue ourself
			self.rq.enq((priority,self))
			return

		if status != self.getStatus():
			self.debug.log("%-20s -> %s, %s" % (service, status, info),1)
			newEvent=event.Event(self.getServiceid(),self.getNetboxid(),self.getType(),status,info)
			newEvent.setSysname(self.getSysname())
			# Post to the NAV alertq
			self.db.newEvent(newEvent)

			# Send an mail while we are waiting for the
			# NAV alertengine to function properly
			self.alerter.put(newEvent)
			self.setStatus(status)
		
		if version != self.getVersion() and self.getStatus() == Event.UP:
			newEvent=event.Event(self.getServiceid(),self.getNetboxid(),
					     self.getType(), status, info,
					     eventtype="version", version=self.getVersion())
			self.db.newEvent(newEvent)

		try:
			rrd.update(self.getServiceid(),'N',self.getStatus(),self.getResponsetime())
		except Exception,e:
			self.debug.log("rrd update failed for %s [%s]" % (service,e),3)
		self.setTimestamp()
		self.runcount=0


	def executeTest(self):
		"""
		Executes and times the test.
		Calls self.execute() which should be overridden
		by each subclass.
		"""
		start = time.time()
		try:
			status,info = self.execute()
		except Exception,info:
			status = event.Event.DOWN
			info = str(info)
		self.setResponsetime(time.time()-start)
		return status, info

	def setServiceid(self,serviceid):
		"""Sets the serviceid according to the database"""
		self._serviceid = serviceid
	def getServiceid(self):
		"""Returns the serviceid """
		return self._serviceid
	def setNetboxid(self,boksid):
		"""Sets the netboxid according to the database """
		self._boksid = boksid
	def getNetboxid(self):
		"""Returns the netboxid """
		return self._boksid
	def getResponsetime(self):
		"""Returns the responsetime of this service """
		return self._usage
	def setSysname(self, sysname):
		"""Sets the sysname """
		self._sysname=sysname
	def getSysname(self):
		"""Returns the sysname of which this service is running on.
		If no sysname is specified, the ip address is returned."""
		if self._sysname:
			return self._sysname
		else:
			return self.geIp()
	def setResponsetime(self,usage):
		"""Sets the responsetime of this service. Is updated by self.run() """
		self._usage = usage
	def getStatus(self):
		"""Returns the current status of this service. Typically
		Event.UP or Event.DOWN"""
		return self._status
	def setStatus(self,status):
		"""Sets the current status. Is updated by self.run() """
		self._status = status
	def getTimestamp(self):
		"""Returns the time of last check. """
		return self._timestamp
	def setTimestamp(self,when = -1):
		"""Updates the time of last check. If no argument is
		supplied, it defaults to time.time()"""
		if when == -1:
			when = time.time()
		self._timestamp= when
	def setTimeout(self,value):
		"""Sets the timeout value for this service. """
		self._timeout = value
	def getTimeout(self):
		"""Returns the timeout value for this service. """
		return self._timeout
	def setArgs(self,args):
		self._args = args
	def getArgs(self):
		"""Returns a dict containing all (nonstandard) arguments passed
		in to this handler. This could be port, username, password or any
		other argument a handler might need."""
		return self._args
	def setType(self,type):
		"""Sets the name of the handler. This is used by the
		constructor."""
		self._type = type
	def getType(self):
		"""Returns the name of the handler. """
		return self._type
	def setIp(self, ip):
		"""Sets the ip address to connect to """
		self._ip = ip
	def getIp(self):
		"""Returns the ipå address to connect to """
		return self._ip
	def setPort(self, port):
		"""Sets the port number to connect to. The constructor
		parses the arguments (self.getArgs()) and gets the port
		argument. If no port argument is specified, it sets the port
		to 0."""
		self._port = port
	def getPort(self):
		"""Returns the port supplied as an argument to
		the test. If no argument is supplied, this function
		returns 0.
		This allows you to do (and i encourage you to)
		self.setPort(self.getPort() or DEFAULT_PORT_FOR_SERVICE)
		in your subclass."""
		return self._port
	def getAddress(self):
		"""Returns a tuple (ip, port) """
		return (self._ip, self._port)
	def setAddress(self,address):
		"""This should not be used. Set the ip address and port independently
		instead."""
		self._address = address
	def setVersion(self,version):
		"""Sets the version of the service. Updateded by self.run() """
		self._version = version
	def getVersion(self):
		"""Returns the current version of the service."""
		return self._version
	def __eq__(self,obj):
		return self.getServiceid() == obj.getServiceid() and self.getArgs() == obj.getArgs() and self.getAddress() == obj.getAddress()
	def __cmp__(self,obj):
		return self.getTimestamp().__cmp__(obj.getTimestamp())
	def __hash__(self):
		value = self.getServiceid() + self.getArgs().__str__().__hash__() + self.getAddress().__hash__()
		value = value % 2**31
		return int(value)
	def __repr__(self):
		s = '%i: %s %s %s' % (self.getServiceid(),self.getType(),str(self.getAddress()),str(self.getArgs()))
		return s.ljust(60) + self.getStatus()


