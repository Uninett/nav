"""
$Id: SshHandler.py,v 1.4 2002/07/08 14:13:33 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/SshHandler.py,v $
"""
from job import JobHandler, Event
import Socket
class SshHandler(JobHandler):
	"""
	"""
	def __init__(self,serviceid,boksid,ip,args,version,db=None):
		port = args.get('port',22)
		JobHandler.__init__(self,'ssh',serviceid,boksid,(ip,port),args,version,db=db)
	def execute(self):
		s = Socket.Socket(self.getTimeout())
		s.connect(self.getAddress())
		version = s.readline().strip()
		self.setVersion(version)
		return Event.UP,'OK'

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
			
