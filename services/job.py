"""
Overvåker

$Author: erikgors $
$Id: job.py,v 1.1 2002/06/04 10:50:49 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/job.py,v $
"""
import time,socket,sys

class Job:
	"""
	Jobb-klasse som hver enkel "tjeneste"-modul skal extende,
	den må ha en execute() som returnerer (state,txt)
	"""
	def __init__(self,name,address):
		self._name = name
		self._address = address 
		self._status = ''
		self._lastRun = 0
		self._state = ''
	def run(self):
		state,txt = self.execute()
		
		if state != self.getState():
			#forteller databasen at her har det skjedd noe
			database.add(self,state,txt)
		else:
			self.setState(state)
		self.setLastRun()
	def execute(self):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			s.connect(self.getAddress())
			txt = s.recv(1024)
			state = 'OK'
		except socket.error:
			state = 'socket.error'
			txt = sys.exc_info()[1].args

		return state,txt
	def getStatus(self):
		return self._status
	def setStatus(self,status):
		self._status = status
	def getLastRun(self):
		return self._lastRun
	def setLastRun(self):
		self._lastRun = time.time()
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
	def __eq__(self,obj):
		if type(obj) == str:
			return self.getName() == obj
		else:
			return self.getName() == obj.getName()
	def __hash__(self):
		return self.getName().__hash__()
	def __repr__(self):
		return 'job: \'' + self.getName() + '\''
