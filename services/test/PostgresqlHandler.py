"""
$Id: PostgresqlHandler.py,v 1.1 2002/06/26 09:04:45 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/test/PostgresqlHandler.py,v $
"""
from job import JobHandler, Event
class PostgresqlHandler(JobHandler):
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get('port', 5432)
		JobHandler.__init__(self,'postgresql',serviceid, boksid, (ip,port), args, version)
	def execute(self):
		args = self.getArgs()
		s = Socket(self.getTimeout())
		s.connect(self.getAddress())
		s.close()
		return Event.UP,'alive'
