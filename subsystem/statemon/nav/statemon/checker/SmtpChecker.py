"""
$Id$
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/checker/SmtpChecker.py,v $
"""

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
from nav.statemon.Socket import Socket
import smtplib
class SMTP(smtplib.SMTP):
	def __init__(self,timeout, host = '',port = 25):
		self.timeout = timeout
		smtplib.SMTP.__init__(self,host,port)
	def connect(self, host='localhost', port = 25):
		self.sock = Socket(self.timeout)
		self.sock.connect((host,port))
		return self.getreply()

class SmtpChecker(AbstractChecker):
	def __init__(self,service, **kwargs):
		AbstractChecker.__init__(self, "smtp", service,port=25, **kwargs)
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
				# smtp servers tend to display the version
				# and time/date seperated by a , or ;
				if ',' in i:
					break
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
			
