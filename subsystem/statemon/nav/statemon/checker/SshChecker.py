"""
$Id$
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/checker/SshChecker.py,v $
"""
from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
from nav.statemon import Socket
class SshChecker(AbstractChecker):
	"""
	"""
	def __init__(self,service, **kwargs):
		AbstractChecker.__init__(self, "ssh", service, port=22, **kwargs)
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
			
