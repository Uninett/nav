"""
Overvåkeren

$Id: job.py,v 1.8 2002/07/15 23:01:45 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/job.py,v $
"""
import time,socket,sys,types,config
from select import select
from errno import errorcode
from Socket import Socket

TIMEOUT = 7 #default timeout
DEBUG=1
class Event:
	UP = 'UP'
	DOWN = 'DOWN'
	TYPE = 'serviceState'    # reflects the value type in the evenq table
	def __init__(self,serviceid,boksid,type,status,info):
		self.serviceid = serviceid
		self.boksid = boksid
		self.type = type
		self.status = status
		self.info = info


class JobHandler:
	def __init__(self,type,serviceid,boksid,address,args,version,status = Event.UP):
		import db
		self.setServiceid(serviceid)
		self.setBoksid(boksid)
		self.setType(type)
		self.setAddress(address)
		self.setStatus(status)
		self.setTimestamp(0)
		self.setArgs(args)
		self.setVersion(version)
		self.setTimeout(args.get('timeout',TIMEOUT))
		self.db=db.db(config.config())
		
	def run(self):
		import rrd,db

		version = self.getVersion()
		status, info = self.executeTest()

		if DEBUG:
			import socket
			host=self.getAddress()
			if type(host)==type(()):
				host=host[0]
			host = socket.getfqdn(host)
			print "Info:  %-25s %-5s -> %s" % (host, self.getType(),info)
			
		runcount = 0
		while status != self.getStatus() and runcount < 3:
			if DEBUG:
				print "Info:  %-25s %-5s -> State changed. Trying again in 5 sec..." % (host, self.getType())
			time.sleep(5)
			status, info = self.executeTest()
			runcount += 1

		if status != self.getStatus():
			self.db.newEvent(Event(self.getServiceid(),self.getBoksid(),self.getType(),status,info))
			self.setStatus(status)
			if DEBUG:
				print "Event: %-25s %-5s -> %s, %s" % (host, self.getType(), status, info)

		
		if version != self.getVersion() and self.getStatus() == Event.UP:
			self.db.newVersion(self.getServiceid(),self.getVersion())
		rrd.update(self.getServiceid(),'N',self.getStatus(),self.getResponsetime())
		self.setTimestamp()


	def executeTest(self):
		start = time.time()
		try:
			status,info = self.execute()
		except Exception,info:
			status = Event.DOWN
			info = str(info)
		self.setResponsetime(time.time()-start)
		return status, info



	def setServiceid(self,serviceid):
		self._serviceid = serviceid
	def getServiceid(self):
		return self._serviceid
	def setBoksid(self,boksid):
		self._boksid = boksid
	def getBoksid(self):
		return self._boksid
	def getResponsetime(self):
		return self._usage
	def setResponsetime(self,usage):
		self._usage = usage
	def getStatus(self):
		return self._status
	def setStatus(self,status):
		self._status = status
	def getTimestamp(self):
		return self._timestamp
	def setTimestamp(self,when = -1):
		if when == -1:
			when = time.time()
		self._timestamp= when
	def setTimeout(self,value):
		self._timeout = value
	def getTimeout(self):
		return self._timeout
	def setArgs(self,args):
		self._args = args
	def getArgs(self):
		return self._args
	def setType(self,type):
		self._type = type
	def getType(self):
		return self._type
	def getAddress(self):
		return self._address
	def setAddress(self,address):
		self._address = address
	def setVersion(self,version):
		self._version = version
	def getVersion(self):
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


