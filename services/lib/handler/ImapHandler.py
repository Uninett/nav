"""
$Id: ImapHandler.py,v 1.2 2002/06/28 01:06:40 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/ImapHandler.py,v $
"""

from job import JobHandler, Event
import imaplib, Socket
class IMAPConnection(imaplib.IMAP4):
	def __init__(self, timeout, host, port):
		self.timeout=timeout
		imaplib.IMAP4.__init__(self, host, port)


	def open(self, host, port):
		"""
		Overload imaplib's method to connect to the server
		"""
		self.sock=Socket.Socket(self.timeout)
		self.sock.connect((self.host, self.port))
		self.file = self.sock.makefile("rb")

class ImapHandler(JobHandler):
	"""
	Valid arguments:
	port
	username
	password
	"""
	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get("port", 143)
		JobHandler.__init__(self, "imap", serviceid, boksid, (ip, port), args, version)
		
	def execute(self):
		args = self.getArgs()
		user = args.get("username","")
		ip, port = self.getAddress()
		passwd = args.get("password","")
		m = IMAPConnection(self.getTimeout(), ip, port)
		m.login(user, passwd)
		m.logout()
		return Event.UP, "Ok"
