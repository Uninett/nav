"""
$Id: RpcHandler.py,v 1.10 2003/01/12 02:34:13 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/RpcHandler.py,v $
"""
import os
from job import JobHandler, Event
class RpcHandler(JobHandler):
	"""
	args:
	requried
	ex: nfs,nlockmgr
	"""
	def __init__(self,service):
		port = service['args'].get('port', 111)
		service['ip']=(service['ip'],port)
		JobHandler.__init__(self, "rpc", service)

	def execute(self):
		args = self.getArgs()
		default = ['nfs', 'nlockmgr', 'mountd']
		required = args.get('required','').split(',')
		if not required:
			required= default

		ip, port = self.getAddress()

		#input, output, err = os.popen3('/usr/sbin/rpcinfo -p %s' % ip)
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
			
