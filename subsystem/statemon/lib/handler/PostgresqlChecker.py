"""
$Id: PostgresqlChecker.py,v 1.1 2003/06/19 12:53:07 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/PostgresqlChecker.py,v $
"""
from abstractChecker import AbstractChecker, Event
import Socket
class PostgresqlChecker(AbstractChecker):
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get('port', 5432)
		AbstractChecker.__init__(self,'postgresql',serviceid, boksid, (ip,port), args, version)
	def execute(self):
		args = self.getArgs()
		s = Socket.Socket(self.getTimeout())
		s.connect(self.getAddress())
		s.close()
		return Event.UP,'alive'

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
								
