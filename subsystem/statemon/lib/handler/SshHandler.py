"""
$Id: SshHandler.py,v 1.2 2003/06/13 12:52:37 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/SshHandler.py,v $
"""
from job import JobHandler
from event import Event
import Socket
class SshHandler(JobHandler):
	"""
	"""
	def __init__(self,service, **kwargs):
		JobHandler.__init__(self, "ssh", service, **kwargs)
		self.setPort(self.getPort() or 22)
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
			
