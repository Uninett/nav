"""
...

$Author: erikgors $
$Id: main.py,v 1.2 2002/06/06 12:44:58 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/main.py,v $
"""
import os,sys,time
import job,threadpool

ROUND = 60

jobs = []
def renew():
	global jobs
	#newjobs = database.getAll()
	newjobs = []
	for i in range(20):
		newjobs += [job.Dummy(('localhost',80))]
	

	s = []
	for i in newjobs:
		if i in jobs:
			s.append(jobs[jobs.index(i)])
		else:
			s.append(i)
	jobs = s

def main():
	threadpool.start()
	while 1:
		start = time.time()
		renew()
		jobs.sort()
		filter(threadpool.jobqueue.put,jobs)
		wait = time.time() + ROUND - start
		print 'venter i %i sec' % (wait)
		if wait <= 0:
			print 'AIAIAI vente kan bli et problem'
		else:
			time.sleep(wait)
		

if __name__ == '__main__':
	main()
	sys.exit(0)
	pid = os.fork()
	if pid:
		print 'main starter'
		sys.stdin.close()
		sys.stdout.close()
		sys.stderr.close()
		main()
	else:
		sys.exit(0)
