"""
$Id: PostgresqlHandler.py,v 1.1 2003/03/26 16:02:17 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/PostgresqlHandler.py,v $
"""
from job import JobHandler, Event
import Socket
class PostgresqlHandler(JobHandler):
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get('port', 5432)
		JobHandler.__init__(self,'postgresql',serviceid, boksid, (ip,port), args, version)
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
								
