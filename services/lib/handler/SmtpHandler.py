"""
$Id: SmtpHandler.py,v 1.1 2002/06/27 11:49:04 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/SmtpHandler.py,v $
"""

from job import JobHandler, Event
import smtplib
class SMTP(smtplib.SMTP):
	def __init__(self,timeout, host = '',port = 25):
		self.timeout = timeout
		smtplib.SMTP.__init__(self,host,port)
	def connect(self, host='localhost', port = 25):
		self.sock = Socket(self.timeout)
		self.sock.connect((host,port))
		return self.getreply()

class SmtpHandler(JobHandler):
	def __init__(self, serviceid, boksid, ip, args, version):
		address = (ip,args.get('port',25))
		JobHandler.__init__(self,'smtp',serviceid,boksid,address,args,version)
	def execute(self):
		ip,port = self.getAddress()
		s = SMTP(self.getTimeout())
		code,msg = s.connect(ip,port)
		if code != 220:
			return Event.DOWN,msg
		version = msg.split()[2:]
		if len(version) >= 1:
			s = version[0]
			for i in version[1:]:
				s += ' ' + i
				if ';' in s:
					break
			version = s
		else:
			version = ''
		self.setVersion(version)
		return Event.UP,msg

