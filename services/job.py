"""
Overvåker

$Author: erikgors $
$Id: job.py,v 1.6 2002/06/07 11:11:59 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/job.py,v $
"""
import time,socket,sys

FEIL = 0
OK = 100

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
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect(self.getAddress())
			txt = s.recv(1024)
#			s.setblocking(0)
#			while 1:
#				i = s.recv(1024)
#				if not i:
#					break
#				txt += i
			state = OK
			txt = txt.strip()
		except:
			state = FEIL
			txt = str(sys.exc_type) + str(sys.exc_info()[1].args)
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
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect(self.getAddress())
			state = OK
			txt = 'alive'
		except:
			state = FEIL
			txt = str(sys.exc_type) + str(sys.exc_info()[1].args)
		s.close()
		return state,txt
class Dummy(Job):
	def __init__(self,address):
		Job.__init__(self,address)
		Job.setName(self,'dummy')
	def execute(self):
		import random
		time.sleep(random.random()*10)
		return OK,'ok'

class Url(Job):
	def __init__(self,address,type,path = '/'):
		Job.__init__(self,address)
		Job.setName(self,'url')
		self.url = '%s://%s:%i%s' % (type,address[0],address[1],path)
	def execute(self):
		import urllib
		try:
			txt = urllib.urlopen(self.url).read()
			state = OK
			txt = 'OK'
		except:
			state = FEIL
			txt = str(sys.exc_type) + str(sys.exc_info()[1].strerror.args)
		return state,txt
class Http(Url):
	def __init__(self,address,path = '/'):
		Url.__init__(self,address,'http',path)
		Job.setName(self,'http')
	def execute(self):
		import urllib
		try:
			i = urllib.urlopen(self.url)
			state = OK
			txt = i.headers.getheader('server')
		except:
			state = str(sys.exc_type)
			txt = str(sys.exc_info()[1].strerror.args)
		return state,txt
