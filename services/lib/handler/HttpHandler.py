"""
$Id: HttpHandler.py,v 1.4 2002/07/01 16:10:53 magnun Exp $
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
	def __init__(self,serviceid,boksid,ip,args,version):
		port = args.get('port',80)
		JobHandler.__init__(self,'http',serviceid,boksid,(ip,port),args,version)
	def execute(self):
		i = HTTPConnection(self.getTimeout(),*self.getAddress())
		path = self.getArgs().get('path',['/'])[0]
		url = 'http://%s:%i%s' % (self.getAddress()[0],self.getAddress()[1],path)
		i.putrequest('GET',url)
		i.endheaders()
		response = i.getresponse()
		if response.status >= 200 and response.status < 300:
			status = Event.UP
			version = response.getheader('SERVER')
			self.setVersion(version)
			info= 'OK (' + str(response.status) + ')'
		else:
			status = Event.DOWN
			info = 'ERROR (' +  str(response.status) + ')'
		return status,info


def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
								
