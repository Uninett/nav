"""
$Id: Pop3Handler.py,v 1.2 2002/07/08 14:13:33 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/Pop3Handler.py,v $
"""
from job import JobHandler, Event
import poplib, Socket
class PopConnection(poplib.POP3):
	def __init__(self, timeout, ip, port):
		self.ip=ip
		self.port=port
		self.sock=Socket.Socket(timeout)
		self.sock.connect((self.ip, self.port))
		self.file=self.sock.makefile('rb')
		self._debugging=0
		self.welcome = self._getresp()


class Pop3Handler(JobHandler):
	"""
	args:
	username
	password
	port
	"""
	def __init__(self, serviceid, boksid, ip, args, version,db=None):
		port = args.get("port", 110)
		JobHandler.__init__(self, "pop3", serviceid, boksid, (ip, port), args, version,db=db)

	def execute(self):
		args = self.getArgs()
		user = args.get("username","")
		passwd = args.get("password", "")
		ip, port = self.getAddress()
		p = PopConnection(self.getTimeout(), ip, port)
		ver = p.getwelcome()
		p.user(user)
		p.pass_(passwd)
		nummessages = len(p.list()[1])
		p.quit()
		version = ''
		ver=ver.split(' ')
		if len(ver) >= 1:
			for i in ver[1:]:
				if i != "server":
					version += "%s " % i
				else:
					break
		self.setVersion(version)
				
		return Event.UP, "Ok"

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = ['username', 'password']
	return requiredArgs
			
