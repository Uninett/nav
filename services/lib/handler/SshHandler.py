"""
$Id: SshHandler.py,v 1.7 2002/12/09 15:33:15 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/SshHandler.py,v $
"""
from job import JobHandler, Event
import Socket
class SshHandler(JobHandler):
	"""
	"""
	def __init__(self,serviceid,boksid,ip,args,version,sysname):
		port = args.get('port',22)
		JobHandler.__init__(self,'ssh',serviceid,boksid,(ip,port),args,version,sysname)
	def execute(self):
		s = Socket.Socket(self.getTimeout())
		s.connect(self.getAddress())
		version = s.readline().strip()
		self.setVersion(version)
		return Event.UP, version

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
			
