"""
$Id: SshHandler.py,v 1.1 2003/03/26 16:02:17 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/SshHandler.py,v $
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
		try:
			ver = version.split('-')
			protocol = ver[0]
			major = ver[1]
			s.write("%s-%s-%s" % (protocol, major, "NAV_Servicemon"))
		except Exception, e:
			return Event.DOWN, "Failed to send version reply to %s: %s" % (self.getAddress(), str(e))
		s.close()
		self.setVersion(version)
		return Event.UP, version

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
			
