"""
$Id: HttpChecker.py,v 1.1 2003/06/19 12:53:07 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/HttpChecker.py,v $
"""
from event import Event
from abstractChecker import AbstractChecker
import httplib
import Socket
class HTTPConnection(httplib.HTTPConnection):
	def __init__(self,timeout,host,port=None):
		httplib.HTTPConnection.__init__(self,host,port)
		self.timeout = timeout
	def connect(self):
		self.sock = Socket.Socket(self.timeout)
		self.sock.connect((self.host,self.port))
class HttpChecker(AbstractChecker):
	def __init__(self,service, **kwargs):
		AbstractChecker.__init__(self, "http", service,port=80, **kwargs)
	def execute(self):
		ip, port = self.getAddress()
		i = HTTPConnection(self.getTimeout(), ip, port)
		vhost = self.getArgs().get('vhost','')
		path  = self.getArgs().get('path','')
		if vhost:
			url = "http://%s/%s" % (vhost, path)
		else:
			url = "http://%s:%i/%s" % (ip, port, path)

		i.putrequest('GET',url)
		i.endheaders()
		response = i.getresponse()
		if response.status >= 200 and response.status < 300:
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
								
