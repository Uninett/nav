"""
$Id: DnsHandler.py,v 1.6 2002/07/15 20:16:35 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/DnsHandler.py,v $
"""
from job import JobHandler, Event
import DNS
class DnsHandler(JobHandler):
	"""
	Valid argument(s): request
	"""

	def __init__(self, serviceid, boksid, ip, args, version):
		port = args.get("port", 42)
		JobHandler.__init__(self, "dns", serviceid, boksid,(ip, port) , args, version)

	def execute(self):
		ip, port = self.getAddress()
		d = DNS.DnsRequest(server=ip, timeout=self.getTimeout())
		args = self.getArgs()
		#print "Args: ", args
		request = args.get("request","").split(",")
		if request == [""]:
			print "valid debug message :)"
			return Event.UP, "Argument request must be supplied"
		else:
			timeout = 0
			answer  = []
			for i in range(len(request)):
				print "request: %s"%request[i]
				try:
					reply = d.req(name=request[i].strip())
				except DNS.Error:
					timeout = 1
					#print "%s timed out..." %request[i]
					
				if not timeout and len(reply.answers) > 0 :
					answer.append(1)
					#print "%s -> %s"%(request[i], reply.answers[0]["data"])
				elif not timeout and len(reply.answers)==0:
					answer.append(0)


			ver = d.req(name="version.bind",qclass="chaos", qtype='txt').answers
			if len(ver) > 0:
				self.setVersion(ver[0]['data'][0])
					
			
			if not timeout and 0 not in answer:

				return Event.UP, "Ok"
			elif not timeout and 0 in answer:
				return Event.UP, "No record found"
			else:
				return Event.DOWN, "Timeout"


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
