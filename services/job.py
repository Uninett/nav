"""
Overvåkeren

$Id: job.py,v 1.36 2002/06/25 23:51:53 magnun Exp $
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
	def __init__(self,serviceid,boksid,type,status,info):
		self.serviceid = serviceid
		self.boksid = boksid
		self.type = type
		self.status = status
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
			raise Timeout('Timeout in connect after %i sec' % self.timeout)
	def recv(self,*args):
		r,w,e = select([self.s],[],[],self.timeout)
		if not r:
			raise Timeout('Timeout in recv after %i sec' % self.timeout)
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
			raise Timeout('Timeout in write after %i sec' % self.timeout)
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
	def __init__(self,type,serviceid,boksid,address,args,version,status = Event.UP):
		self.setServiceid(serviceid)
		self.setBoksid(boksid)
		self.setType(type)
		self.setAddress(address)
		self.setStatus(status)
		self.setTimestamp(0)
		self.setArgs(args)
		self.setVersion(version)
		self.setTimeout(args.get('timeout',TIMEOUT))
	def run(self):
		import database
		import rrd
		start = time.time()
		version = self.getVersion()
		try:
			status,info = self.execute()
		except Exception,info:
			status = Event.DOWN
			info = str(info)
		self.setResponsetime(time.time()-start)

		rrd.update(self.getServiceid(),'N',self.getStatus(),self.getResponsetime())
		
		if status != self.getStatus():
			database.newEvent(Event(self.getServiceid(),self.getBoksid(),self.getType(),status,info))
			self.setStatus(status)
		if version != self.getVersion() and self.getStatus() == Event.UP:
			database.newVersion(self.getServiceid(),self.getVersion())
		self.setTimestamp()
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
		return self.getServiceid() == obj.getServiceid() and self.getArgs() == obj.getArgs()
	def __cmp__(self,obj):
		return self.getTimestamp().__cmp__(obj.getTimestamp())
	def __hash__(self):
		value = self.getServiceid() + self.getArgs().__str__().__hash__()
		value = value % 2**31
		return int(value)
	def __repr__(self):
		s = '%i: %s %s %s' % (self.getServiceid(),self.getType(),str(self.getAddress()),str(self.getArgs()))
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
	def __init__(self,serviceid,boksid,ip,args,version):
		port = args.get('port',80)
		JobHandler.__init__(self,'http',serviceid,boksid,(ip,port),args,version)
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
	def __init__(self,serviceid,boksid,ip,args,version):
		port = args.get('port',21)
		JobHandler.__init__(self,'ftp',serviceid,boksid,(ip,port),args,version)
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
	def __init__(self,serviceid,boksid,ip,args,version):
		port = args.get('port',22)
		JobHandler.__init__(self,'ssh',serviceid,boksid,(ip,port),args,version)
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

	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get("port", 42)
		JobHandler.__init__(self, "dns", serviceid, boksid, (ip, port), args, version)

	def execute(self):
		ip, port =self.getAddress()
		d = DNS.DnsRequest(server=ip, timeout=self.getTimeout())
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
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get("port", 3306)
		JobHandler.__init__(self, "mysql", serviceid, boksid, (ip, port), args, version)
	def execute(self):
		s = Socket(self.getTimeout())
		s.connect(self.getAddress())
		line = s.readline()
		s.close()
		#this is ugly
		version = line.split('-')[1].split('\n')[1].strip()
		self.setVersion(version)
		return Event.UP, 'OK'

class PostgresqlHandler(JobHandler):
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get('port', 5432)
		JobHandler.__init__(self,'postgresql',serviceid, boksid, (ip,port), args, version)
	def execute(self):
		args = self.getArgs()
		s = Socket(self.getTimeout())
		s.connect(self.getAddress())
		s.close()
		return Event.UP,'alive'

import imaplib
class IMAPConnection(imaplib.IMAP4):
	def __init__(self, timeout, host, port):
		self.timeout=timeout
		imaplib.IMAP4.__init__(self, host, port)


	def open(self, host, port):
		"""
		Overload imaplib's method to connect to the server
		"""
		self.sock=Socket(self.timeout)
		self.sock.connect((self.host, self.port))
		self.file = self.sock.makefile("rb")

class ImapHandler(JobHandler):
	"""
	Valid arguments:
	port
	username
	password
	"""
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get("port", 143)
		JobHandler.__init__(self, "imap", serviceid, boksid, (ip, port), args, version)
		
	def execute(self):
		args = self.getArgs()
		user = args.get("username","")
		ip, port = self.getAddress()
		passwd = args.get("password","")
		m = IMAPConnection(self.getTimeout(), ip, port)
		m.login(user, passwd)
		m.logout()
		return Event.UP, "Ok"


import poplib
class PopConnection(poplib.POP3):
	def __init__(self, timeout, ip, port):
		self.ip=ip
		self.port=port

		self.sock=Socket(timeout)
		self.sock.connect((self.ip, self.port))
		self.file=self.sock.makefile('rb')
		self._debugging=0
		#self.welcome=self._getresp()

class PopHandler(JobHandler):
	"""
	args:
	username
	password
	port
	"""
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get("port", 110)
		JobHandler.__init__(self, "pop3", serviceid, boksid, (ip, port), args, version)

	def execute(self):
		args = self.getArgs()
		user = args.get("username","")
		passwd = args.get("password", "")
		ip, port = self.getAddress()
		p = PopConnection(self.getTimeout(), ip, port)
		p.user(user)
		p.pass_(passwd)
		nummessages = len(p.list()[1])
		p.quit()
		return Event.UP, "Ok"



class SmbHandler(JobHandler):
	"""
	args:
		'username'
		'password'
		'port'
	"""
	def __init__(self, serviceid, boksid, ip, args, version):
		address = (ip,args.get('port',139))
		JobHandler.__init__(self,'smb',serviceid,boksid,address,args,version)
	def execute(self):
		args = self.getArgs()
		username = args.get('username','')
		password = args.get('password','')

		if password and username:
			s = '-U ' + username + '%' + password
		else:
			s = '-N'

		ip,port = self.getAddress()
		import os
		status = os.system('smbclient -L %s -p %i %s 2>/dev/null > /dev/null' %(ip,port,s))

		if status:
			return Event.DOWN,'error %i' % status
		else:
			return Event.UP,'OK'

import os
class DcHandler(JobHandler):
	"""
	Required argument:
	username
	"""
	def __init__(self, serviceid, boksid, ip, args, version):
		address = (ip, 0)
		JobHandler.__init__(self, 'dc', serviceid, boksid, address, args, version)

	def execute(self):
		args = self.getArgs()
		username = args.get('username','')
		if not username:
			return Event.DOWN, "Missing required argument: username"
		ip, host = self.getAddress()
		command = "/usr/local/samba/bin/rpcclient -U %% -c 'lookupnames %s' %s  2>/dev/null" % (username, ip)
		result = os.popen(command).readlines()[-1]
		if result.split(" ")[0] == username:
			return Event.UP, 'Ok'
		else:
			return Event.DOWN, result
		

import smtplib
class SMTP(smtplib.SMTP):
	def __init__(self,timeout, host = '',port = 25):
		self.timeout = timeout
		smtplib.SMTP.__init__(self,host,port)
	def connect(self, host='localhost', port = 25):
		self.sock = Socket(self.timeout)
		self.sock.connect((host,port))
		return self.getreply()

class SmtpHandler(JobHandler):
	def __init__(self, serviceid, boksid, ip, args, version):
		address = (ip,args.get('port',25))
		JobHandler.__init__(self,'smtp',serviceid,boksid,address,args,version)
	def execute(self):
		ip,port = self.getAddress()
		s = SMTP(self.getTimeout())
		code,msg = s.connect(ip,port)
		if code != 220:
			return Event.DOWN,msg
		version = msg.split()[2:]
		if len(version) >= 1:
			s = version[0]
			for i in version[1:]:
				s += ' ' + i
				if ';' in s:
					break
			version = s
		else:
			version = ''
		self.setVersion(version)
		return Event.UP,msg


jobmap = {'http':HttpHandler,
	  'port':PortHandler,
	  'ftp':FtpHandler,
	  'ssh':SshHandler,
	  'dns':DnsHandler,
	  'imap':ImapHandler,
	  'mysql':MysqlHandler,
	  'smb':SmbHandler,
	  'smtp':SmtpHandler,
	  'pop':PopHandler,
	  'dc':DcHandler
	  }
