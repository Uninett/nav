"""
$Id: PortHandler.py,v 1.2 2002/07/01 16:10:53 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/PortHandler.py,v $
"""
from job import JobHandler, Event
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

