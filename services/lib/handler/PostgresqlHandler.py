"""
$Id: PostgresqlHandler.py,v 1.2 2002/06/28 01:06:40 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/PostgresqlHandler.py,v $
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
