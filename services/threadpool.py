"""
threadpool

$Id: threadpool.py,v 1.1 2002/06/04 09:14:10 erikgors Exp $
"""

import threading
IDLE = 1
WORK = 2


jobqueue = []
threadpool = []

class jobber(threading.Thread):
	def __init__(self,name):
		setName(name)
		self.status = IDLE
		self.running = 1

	def run(self):
		while self.running:
			self.status = IDLE
			self.job = jobqueue.pop()

			self.status = WORKING
			result = self.job.run()
