"""
$Id: PopHandler.py,v 1.2 2002/06/28 01:06:40 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/Attic/PopHandler.py,v $
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
		#self.welcome=self._getresp()

class PopHandler(JobHandler):
	"""
	args:
	username
	password
	port
	"""
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get("port", 110)
		JobHandler.__init__(self, "pop3", serviceid, boksid, (ip, port), args, version)

	def execute(self):
		args = self.getArgs()
		user = args.get("username","")
		passwd = args.get("password", "")
		ip, port = self.getAddress()
		p = PopConnection(self.getTimeout(), ip, port)
		p.user(user)
		p.pass_(passwd)
		nummessages = len(p.list()[1])
		p.quit()
		return Event.UP, "Ok"
