"""
threadpool

$Id: threadpool.py,v 1.5 2002/06/06 09:19:45 erikgors Exp $
"""

import threading,time
from Queue import Queue
IDLE = 2
WORK = 4

THREADS = 10


jobqueue = Queue()
workers = []

class Worker(threading.Thread):
	def __init__(self,name):
		threading.Thread.__init__(self)
		threading.Thread.setName(self,name)
		self.status = IDLE
		self.running = 1

	def run(self):
		while self.running:
			self.status = IDLE
			self.job = jobqueue.get()

			self.status = WORK
			result = self.job.run()
def start():
	global workers
	for i in range(THREADS):
		thread = Worker('thread ' + str(i))
		workers += [thread]
		thread.start()
