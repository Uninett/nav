"""
$Id: SshHandler.py,v 1.8 2003/01/03 15:43:54 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/SshHandler.py,v $
"""
from job import JobHandler, Event
import Socket
class SshHandler(JobHandler):
	"""
	"""
	def __init__(self,service):
		port = service['args'].get('port', 22)
		service['ip']=(service['ip'],port)
		JobHandler.__init__(self, "ssh", service)
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
			
