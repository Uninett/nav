"""
threadpool

$Id: threadpool.py,v 1.4 2002/06/04 15:06:21 erikgors Exp $
"""

import threading
IDLE = 2
WORK = 4


jobqueue = []
threadpool = []

class jobber(threading.Thread):
	def __init__(self,name):
		Thread.__init__(self)
		Thread.setName(self,name)
		self.status = IDLE
		self.running = 1

	def run(self):
		while self.running:
			self.status = IDLE
			self.job = jobqueue.pop()

			self.status = WORKING
			result = self.job.run()
