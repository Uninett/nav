"""
$Id: HttpChecker.py,v 1.1 2003/06/19 12:56:18 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/checker/HttpChecker.py,v $
"""
from event import Event
from abstractChecker import AbstractChecker
from urlparse import urlsplit
import httplib
import Socket
import socket
class HTTPConnection(httplib.HTTPConnection):
	def __init__(self,timeout,host,port=80):
		httplib.HTTPConnection.__init__(self,host,port)
		self.timeout = timeout
		self.connect()
	def connect(self):
		self.sock = Socket.Socket(self.timeout)
		self.sock.connect((self.host,self.port))
class HTTPSConnection(httplib.HTTPSConnection):
	def __init__(self,timeout,host,port=443):
		httplib.HTTPSConnection.__init__(self,host,port)
		self.timeout = timeout
		self.connect()
	def connect(self):
		sock = Socket.Socket(self.timeout)
		sock.connect((self.host,self.port))
		ssl = socket.ssl(sock.s, None, None)
		self.sock = httplib.FakeSocket(sock, ssl)
		
class HttpChecker(AbstractChecker):
	def __init__(self,service, **kwargs):
		AbstractChecker.__init__(self, "http", service,port=80, **kwargs)
	def execute(self):
		ip, port = self.getAddress()
		url = self.getArgs().get('url','')
		if not url:
			url = "/"
		protocol, vhost, path, query, fragment = urlsplit(url)
		
		if protocol == 'https':
			i = HTTPSConnection(self.getTimeout(), ip, port)
		else:
			i = HTTPConnection(self.getTimeout(), ip, port)
		if vhost:
			i.host=vhost
		i.set_debuglevel(9)
		i.putrequest('GET',path)
		internalRev = "$Rev $"
		internalRev = internalRev[:-1].replace('$Rev: ','')
		i.putheader('User-Agent','NAV/ServiceMon Build 1734 Release 31337, internal revision %s' % internalRev
		i.endheaders()
		response = i.getresponse()
		if response.status >= 200 and response.status < 400:
			status = Event.UP
			version = response.getheader('SERVER')
			self.setVersion(version)
			info= 'OK (%s) %s' % (str(response.status), version)
		else:
			status = Event.DOWN
			info = 'ERROR (%s) %s'  % (str(response.status),url)

		return status,info


def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
								
