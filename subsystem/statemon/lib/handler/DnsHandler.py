"""
$Id: DnsHandler.py,v 1.2 2003/05/26 17:47:14 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/DnsHandler.py,v $
"""
from job import JobHandler, Event
import DNS
class DnsHandler(JobHandler):
	"""
	Valid argument(s): request
	"""
	def __init__(self,service):
		port = service['args'].get('port',42)
		service['ip']=(service['ip'],port)
		JobHandler.__init__(self,"dns",service)

	def execute(self):
		ip, port = self.getAddress()
		d = DNS.DnsRequest(server=ip, timeout=self.getTimeout())
		args = self.getArgs()
		#print "Args: ", args
		request = args.get("request","").strip()
		timeout=0
		if not request:
			#print "valid debug message :)"
			return Event.UP, "Argument request must be supplied"
		else:
			answer  = ""
			#print "request: %s"%request[i]
			try:
				reply = d.req(name=request)
			except DNS.Error:
				timeout = 1
				#print "%s timed out..." %request[i]
					
			if not timeout and len(reply.answers) > 0 :
				answer=1
				#print "%s -> %s"%(request[i], reply.answers[0]["data"])
			elif not timeout and len(reply.answers)==0:
				answer=0

			# This breaks on windows dns servers and probably other not bind servers
			#ver = d.req(name="version.bind",qclass="chaos", qtype='txt').answers
			#if len(ver) > 0:
			#	self.setVersion(ver[0]['data'][0])
					
			

			if not timeout and answer == 1:
				return Event.UP, "Ok"
			elif not timeout and answer == 1:
				return Event.UP, "No record found, request=%s" % request
			else:
				return Event.DOWN, "Timeout while requesting %s" % request


def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = ['request']
	return requiredArgs

def provides():
	"""
	Returns a string, telling what test this module provides
	"""
	return "dns"
