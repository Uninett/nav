
"""
Overvåker

$Author: magnun $
$Id: job.py,v 1.19 2002/06/18 14:15:48 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/job.py,v $
"""
import time,socket,sys,types
from select import select
from errno import errorcode

TIMEOUT = 5 #default timeout
class Timeout(Exception):
	pass
class Event:
	UP = 'UP'
	DOWN = 'DOWN'
	def __init__(self,id,status,info):
		self.status = status
		self.id = id
		self.info = info

class Socket:
	def __init__(self,timeout):
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
	def __init__(self,type,id,address,args,version,status = Event.UP):
		self.setId(id)
		self.setType(type)
		self.setAddress(address)
		self.setStatus(status)
		self.setTimestamp(0)
		self.setArgs(args)
		self.setVersion(version)
		self.setTimeout(args.get('timeout',TIMEOUT))
	def run(self):
		import database
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
		if version != self.getVersion():
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
#		if type(obj) in [str,types.IntType]:
#			return self.getId() == int(obj)
		return self.getId() == obj.getId() and self.getArgs() == obj.getArgs()
	def __cmp__(self,obj):
		return self.getTimestamp().__cmp__(obj.getTimestamp())
	def __hash__(self):
		return self.getId()
	def __repr__(self):
		s = '%i: %s %s %s' % (self.getId(),self.getType(),str(self.getAddress()),str(self.getArgs()))
		return s.ljust(60) + self.getStatus()
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
	def __init__(self,timeout,host,port=None):
		httplib.HTTPConnection.__init__(self,host,port)
		self.timeout = timeout
	def connect(self):
		self.sock = Socket(self.timeout)
		self.sock.connect((self.host,self.port))
class HttpHandler(JobHandler):
	def __init__(self,id,ip,args,version):
		port = args.get('port',80)
		JobHandler.__init__(self,'http',id,(ip,port),args,version)
	def execute(self):
		i = HTTPConnection(self.getTimeout(),*self.getAddress())
		path = self.getArgs().get('path',['/'])[0]
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
	def __init__(self,timeout,host='',user='',passwd='',acct=''):
		ftplib.FTP.__init__(self)
		if host:
			self.connect(host)
		if user:
			self.login(user,passwd,acct)
		self.timeout = timeout
	def connect(self, host = '', port = 0):
		'''Connect to host.  Arguments are:
		- host: hostname to connect to (string, default previous host)
		- port: port to connect to (integer, default previous port)'''
		if host: self.host = host
		if port: self.port = port
		msg = "getaddrinfo returns an empty list"
		self.sock = Socket(self.timeout)
		self.sock.connect((self.host,self.port))
		self.file = self.sock.makefile('rb')
		self.welcome = self.getresp()
		return self.welcome
class FtpHandler(JobHandler):
	"""
	takes the args:
	username
	password
	path (ACCT)
	"""
	def __init__(self,id,ip,args,version):
		port = args.get('port',21)
		JobHandler.__init__(self,'ftp',id,(ip,port),args,version)
	def execute(self):
		s = FTP(self.getTimeout())
		ip,port = self.getAddress()
		output = s.connect(ip,port)
		args = self.getArgs()
		username = args.get('username','')
		password = args.get('password','')
		path = args.get('path','')
		output = s.login(username,password,path)
		if output[:3] == '230':
			return Event.UP,'code 230'
		else:
			return Event.DOWN,output.split('\n')[0]
class SshHandler(JobHandler):
	"""
	"""
	def __init__(self,id,ip,args,version):
		port = args.get('port',22)
		JobHandler.__init__(self,'ssh',id,(ip,port),args,version)
	def execute(self):
		s = Socket(self.getTimeout())
		s.connect(self.getAddress())
		version = s.readline().strip()
		self.setVersion(version)
		return Event.UP,'OK'

import DNS
class DnsHandler(JobHandler):
	"""
	Valid argument(s): request
	"""

	def __init__(self, id, ip, args, version):
		port = args.get("port", 42)
		JobHandler.__init__(self, "dns", id, (ip, port), args, version)

	def execute(self):
		server=self.getAddress()
		d = DNS.DnsRequest(server=server[0], timeout=self.getTimeout())
		args = self.getArgs()
		request = args.get("request","").split(",")
		if request == [""]:
			print "valid debug message :)"
			return
		else:
			timeout = 0
			answer  = []
			for i in range(len(request)):
				print "request: %s"%request[i]
				try:
					reply = d.req(name=request[i].strip())
				except DNS.Error:
					timeout = 1
					print "%s timed out..." %request[i]
					
				if not timeout and len(reply.answers) > 0 :
					answer.append(1)
					print "%s -> %s"%(request[i], reply.answers[0]["data"])
				elif not timeout and len(reply.answers)==0:
					answer.append(0)
				
			if not timeout and 0 not in answer:
				return Event.UP, "Ok"
			elif not timeout and 0 in answer:
				return Event.UP, "No record found"
			else:
				return Event.DOWN, "Timeout"

class MysqlHandler(JobHandler):
	def __init__(self, id, ip, args, version):
		port = args.get("port", 3306)
		JobHandler.__init__(self, "mysql", id, (ip, port), args, version)
	def execute(self):
		s = Socket(self.getTimeout())
		s.connect(self.getAddress())
		line = s.readline()
		s.close()
		#this is ugly
		version = line.split('-')[1].split('\n')[1].strip()
		self.setVersion(version)
		return Event.UP, 'OK'



jobmap = {'http':HttpHandler,
	  'port':PortHandler,
	  'ftp':FtpHandler,
	  'ssh':SshHandler,
	  'dns':DnsHandler,
	  'mysql':MysqlHandler
	  }
