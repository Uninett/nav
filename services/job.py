"""
Overvåker

$Author: erikgors $
$Id: job.py,v 1.10 2002/06/13 13:08:03 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/job.py,v $
"""
import time,socket,sys,types
from select import select
from errno import errorcode

class Timeout(Exception):
	pass
class Event:
	UP = 'UP'
	DOWN = 'DOWN'
	def __init__(self,id,status,info):
		self.status = status
		self.id = id
		self.info = info

import database
class Socket:
	def __init__(self,timeout=5):
		self.timeout = timeout
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def connect(self,address):
		self.s.setblocking(0)
		try:

			self.s.connect(address)
		except socket.error, (number,info):
			if not errorcode[number] == 'EINPROGRESS':
				raise
		self.s.setblocking(1)
		r,w,e = select([],[self],[],self.timeout)
		if not w:
			raise Timeout('Timeout in connect')
	def recv(self,*args):
		r,w,e = select([self.s],[],[],self.timeout)
		if not r:
			raise Timeout('Timeout in recv')
		return self.s.recv(*args)
	def readline(self):
		line = ''
		while 1:
			line += self.recv(1024)
			if '\n' in line or not line:
				return line
	def send(self,*args):
		r,w,e = select([],[self.s],[],self.timeout)
		if not w:
			raise Timeout('Timeout in write')
		self.s.send(*args)
	
	def write(self,line):
		if line[-1] != '\n':
			line += '\n'
		self.send(line)
	def close(self):
		self.s.close()
	def makefile(self,*args):
		return self.s.makefile(*args)
	def fileno(self):
		return self.s.fileno()
	def sendall(self,*args):
		return self.s.sendall(*args)
	


class JobHandler:
	def __init__(self,type,id,address,args,version = '',status = Event.UP):
		self.setId(id)
		self.setType(type)
		self.setAddress(address)
		self.setStatus(status)
		self.setTimestamp(0)
		self.setArgs(args)
		self.setVersion(version)
	def run(self):
		start = time.time()
		version = self.getVersion()
		try:
			status,info = self.execute()
		except Exception,info:
			status = 'DOWN'
			info = str(info)
		self.setUsage(time.time()-start)
		
		if status != self.getStatus():
			database.newEvent(Event(self.getId(),status,info))
			self.setStatus(status)
		elif version != self.getVersion():
			database.newVersion(self.getId(),self.getVersion())
		self.setTimestamp()
	def setId(self,id):
		self._id = id
	def getId(self):
		return self._id
	def getUsage(self):
		return self._usage
	def setUsage(self,usage):
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
		if type(obj) in [str,types.IntType]:
			return self.getId() == int(obj)
		return self.getId() == obj.getId()
	def __cmp__(self,obj):
		return self.getTimestamp().__cmp__(obj.getTimestamp())
	def __hash__(self):
		return self.getId()
	def __repr__(self):
		s = '%i: %s %s' % (self.getId(),self.getType(),str(self.getAddress()))
		return s.ljust(40) + self.getStatus()
class PortHandler(JobHandler):
	def __init__(self,*args):
		JobHandler.__init__(self,'port',*args)
	def execute(self):
		s = Socket()
		s.connect(self.getAddress())
		r,w,x = select([s],[],[],0.1)
		if r:
			s.readline()
		status = Event.UP
		txt = 'Alive'
		s.close()

		return status,txt
class DummyHandler(JobHandler):
	def __init__(self,*args):
		JobHandler.__init__(self,'dummy',*args)
	def execute(self):
		import random
		time.sleep(random.random()*10)
		return Event.UP,'OK'

import httplib
class HTTPConnection(httplib.HTTPConnection):
	def __init__(self,host,port=None):
		httplib.HTTPConnection.__init__(self,host,port)
	def connect(self):
		self.sock = Socket()
		self.sock.connect((self.host,self.port))
class HttpHandler(JobHandler):
	def __init__(self,id,address,args,version):
		JobHandler.__init__(self,'http',id,address,args,version)
	def execute(self):
		i = HTTPConnection(*self.getAddress())
		path = self.getArgs().get('path','/')
		url = 'http://%s:%i%s' % (self.getAddress()[0],self.getAddress()[1],path)
		print url
		i.putrequest('GET',url)
		i.endheaders()
		response = i.getresponse()
		if response.status >= 200 and response.status < 300:
			status = Event.UP
			version = response.getheader('SERVER')
			self.setVersion(version)
			info= 'OK (' + str(response.status) + ')'
		else:
			status = Event.DOWN
			info = 'ERROR (' +  str(response.status) + ')'
		return status,info
import ftplib
class FTP(ftplib.FTP):
	def __init__(self):
		ftplib.FTP.__init__(self)
	def connect(self, host = '', port = 0):
		'''Connect to host.  Arguments are:
		- host: hostname to connect to (string, default previous host)
		- port: port to connect to (integer, default previous port)'''
		if host: self.host = host
		if port: self.port = port
		msg = "getaddrinfo returns an empty list"
		for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
			af, socktype, proto, canonname, sa = res
			try:
				self.sock = Socket()
				self.sock.connect(sa)
			except socket.error, msg:
				if self.sock:
					self.sock.close()
				self.sock = None
				continue
			break
		if not self.sock:
			raise socket.error, msg
		self.af = af
		self.file = self.sock.makefile('rb')
		self.welcome = self.getresp()
		return self.welcome
