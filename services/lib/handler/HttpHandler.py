"""
$Id: HttpHandler.py,v 1.12 2002/12/09 15:33:15 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/HttpHandler.py,v $
"""
from job import Event, JobHandler
import httplib
import Socket
class HTTPConnection(httplib.HTTPConnection):
	def __init__(self,timeout,host,port=None):
		httplib.HTTPConnection.__init__(self,host,port)
		self.timeout = timeout
	def connect(self):
		self.sock = Socket.Socket(self.timeout)
		self.sock.connect((self.host,self.port))
class HttpHandler(JobHandler):
	def __init__(self,serviceid,boksid,ip,args,version,sysname):
		port = args.get('port',80)
		JobHandler.__init__(self,'http',serviceid,boksid,(ip,port),args,version,sysname)
	def execute(self):
		i = HTTPConnection(self.getTimeout(),*self.getAddress())
		vhost = self.getArgs().get('vhost','')
		path  = self.getArgs().get('path','')
		ip, port = (self.getAddress()[0],self.getAddress()[1])
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
								
