"""
$Id: SshHandler.py,v 1.1 2002/06/26 09:04:45 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/test/SshHandler.py,v $
"""
from job import JobHandler, Event
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
