"""
Overvåker

$Author: erikgors $
$Id: job.py,v 1.7 2002/06/11 14:07:10 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/job.py,v $
"""
import time,socket,sys
from select import select
from errno import errorcode

class Timeout(Exception):
	pass
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
		r,w,e = select([],[self.s],[],self.timeout)
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


class Job:
	"""
	Jobb-klasse som hver enkel "tjeneste"-modul skal extende,
	den må ha en execute() som returnerer (state,txt)

	sorteres ettersom når den sist ble kjørt (getTimestamp)

	Denne vil koble til en port og lese _en_ linje
	"""
	def __init__(self,address):
		self.setName('generic')
		self.setAddress(address)
		self.setStatus('')
		self.setTimestamp(0)
		self.setState(())
	def run(self):
		start = time.time()
		state = self.execute()
		self.setUsage(time.time()-start)
		
		if state != self.getState() and self.getState():
			#forteller databasen at her har det skjedd noe
			database.add(self,state)
		else:
			self.setState(state)
		self.setTimestamp()
	def execute(self):
		s = Socket()
		try:
			s.connect(self.getAddress())
			txt = s.readline()
			state = 'UP'
		except Exception,info:
			state = 'DOWN'
			txt = str(info)
		s.close()

		return state,txt
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
	def setState(self,txt):
		self._state = txt
	def getState(self):
		return self._state
	def setName(self,name):
		self._name = name
	def getName(self):
		return self._name
	def getAddress(self):
		return self._address
	def setAddress(self,address):
		self._address = address
	def __eq__(self,obj):
		if type(obj) == str:
			return self.getName() == obj
		elif type(obj) == tuple:
			return obj == self.getAddress()
		else:
			return self.getName() == obj.getName() and self.getAddress() == obj.getAddress()
	def __cmp__(self,obj):
		return self.getTimestamp().__cmp__(obj.getTimestamp())
	def __hash__(self):
		i = (self.getName().__hash__() + self.getAddress().__hash__()) % 2**31
		return int(i)
	def __repr__(self):
		return '\'' + self.getName() + '\' ' + str(self.getAddress())
class Port(Job):
	"""
	sjekker om en port er i live
	"""
	def __init__(self,address):
		Job.__init__(self,address)
		Job.setName(self,'portlive')
	def execute(self):
		s = Socket()
		try:
			s.connect(self.getAddress())
			state = 'UP'
		except Exception,info:
			state = 'DOWN'
			txt = str(info)
		s.close()

		return state,txt
class Dummy(Job):
	def __init__(self,address):
		Job.__init__(self,address)
		Job.setName(self,'dummy')
	def execute(self):
		import random
		time.sleep(random.random()*10)
		return 'UP','ok'

#class Url(Job):
#	def __init__(self,address,type,path = '/'):
#		Job.__init__(self,address)
#		Job.setName(self,'url')
#		self.url = '%s://%s:%i%s' % (type,address[0],address[1],path)
#	def execute(self):
#		import urllib
#		try:
#			txt = urllib.urlopen(self.url).read()
#			state = 'UP'
#			txt = 'UP'
#		except Exception,info:
#			state = 'DOWN'
#			txt = str(info)
#		return state,txt
class Http(Job):
	def __init__(self,address,path = '/'):
		Job.__init__(self,address)
		Job.setName(self,'http')
		self.path = path
	def execute(self):
		import httplib
		try:
			i = httplib.HTTPConnection('')
			i.sock = Socket()
			i.sock.connect(self.getAddress())
			i.putrequest('GET','http://%s:%i%s' % (self.getAddress()[0],self.getAddress()[1],self.path))
			i.endheaders()
			response = i.getresponse()
			if response.status >= 200 and response.status < 300:
				state = 'UP'
				txt = response.getheader('SERVER')
			else:
				state = 'DOWN'
				txt = 'status == ' +  str(response.status)
		except Exception,info:
			state = 'DOWN'
			txt = str(info)
		return state,txt
