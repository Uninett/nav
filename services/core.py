"""
core - kjøre jobber som prosesser i stedet for tråder

$Author: erikgors $
$Id: core.py,v 1.2 2002/06/18 15:12:52 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/core.py,v $

tanken er at programmet skal lese argumenter fra stdin
starte jobbene som egne prosesser som skriver resultat til stdout

eks stdin:
(serviceid,ip,type,version,{property:value})

eks stdout:
(serviceid,status,info,version,responsetid)
"""
import os,sys,time,random,signal
from job import jobmap,Event

MAX = 50
TIMEOUT = 5
class Core:
	def __init__(self,jobargs):
		"""
		jobargs er en liste med args til jobbene
		"""
		self.jobargs = jobargs
		self.counter = 0
		self.t = {}
	def run(self):
		for i in self.jobargs:
			if self.counter < MAX:
				start = time.time()
				serviceid,ip,type,version,args = i
				pid = os.fork()
				if not pid:
					timeout = args.get('timeout',TIMEOUT)
					signal.alarm(timeout)
					#kjøre en job
					j = jobmap[type](serviceid,ip,args,version)
					status,info = j.execute()
					version = j.getVersion()
					#printe resultatet til stdout
					print (serviceid,status,info,version,time.time() - start)
					sys.exit(0)
				else:
					self.t[pid] = serviceid
					self.counter += 1
			else:
				self.wait()
		while self.counter:
			self.wait()
	def wait(self):
		pid,status = os.wait()
		if status:
			print (self.t[pid],Event.DOWN,'timeout','',0)


		del self.t[pid]
		self.counter -= 1

if __name__ == '__main__':
	jobargs = []
	while 1:
		line = raw_input()
		if not line:
			break
		line = eval(line)
		if not type(line) == tuple:
			raise TypeError(str(line))
		jobargs += [line]
	core = Core(jobargs)
	core.run()
