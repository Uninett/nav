"""
$Id: SmtpHandler.py,v 1.3 2003/06/16 15:40:26 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/SmtpHandler.py,v $
"""

from job import JobHandler
from event import Event
import smtplib, Socket
class SMTP(smtplib.SMTP):
	def __init__(self,timeout, host = '',port = 25):
		self.timeout = timeout
		smtplib.SMTP.__init__(self,host,port)
	def connect(self, host='localhost', port = 25):
		self.sock = Socket.Socket(self.timeout)
		self.sock.connect((host,port))
		return self.getreply()

class SmtpHandler(JobHandler):
	def __init__(self,service, **kwargs):
		JobHandler.__init__(self, "smtp", service,port=25, **kwargs)
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

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
			
