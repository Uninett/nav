"""
$Id: RpcHandler.py,v 1.2 2003/06/13 12:52:37 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/RpcHandler.py,v $
"""
import os
from job import JobHandler
from event import Event
class RpcHandler(JobHandler):
	"""
	args:
	requried
	ex: nfs,nlockmgr
	"""
	def __init__(self,service, **kwargs):
		JobHandler.__init__(self, "rpc", service, **kwargs)
		# This handler doesn't obey port argument
		self.setPort(self.getPort() or 111)

	def execute(self):
		args = self.getArgs()
		default = ['nfs', 'nlockmgr', 'mountd']
		required = args.get('required','').split(',')
		if not required:
			required= default

		ip, port = self.getAddress()

		output = os.popen('/usr/sbin/rpcinfo -p %s' % ip)
		output = output.read()
		if not output:
			return Event.DOWN,'timeout'

		missing = []
		for i in required:
			i = i.strip()
			if output.find(i) == -1:
				missing += [i]
		if missing:
			return Event.DOWN,'missing: ' + ', '.join(missing)
		else:
			return Event.UP, "Ok"

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = ['required']
	return requiredArgs
			
