"""
$Id: MysqlChecker.py,v 1.1 2003/06/19 12:53:07 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/MysqlChecker.py,v $
"""

from abstractChecker import AbstractChecker, Event
import Socket
class MysqlChecker(AbstractChecker):
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get("port", 3306)
		AbstractChecker.__init__(self, "mysql", serviceid, boksid, (ip, port), args, version)
	def execute(self):
		s = Socket.Socket(self.getTimeout())
		s.connect(self.getAddress())
		line = s.readline()
		s.close()
		#this is ugly
		try:
			version = line.split('-')[1].split('\n')[1].strip()
			self.setVersion(version)
		except:
			return Event.DOWN, line
		return Event.UP, 'OK'

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
								
