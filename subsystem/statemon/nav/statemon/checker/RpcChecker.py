"""
$Id: RpcChecker.py,v 1.1 2003/06/19 12:56:18 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/checker/RpcChecker.py,v $
"""
import os
from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
class RpcChecker(AbstractChecker):
	"""
	args:
	requried
	ex: nfs,nlockmgr
	"""
	def __init__(self,service, **kwargs):
		AbstractChecker.__init__(self, "rpc", service,port=111, **kwargs)
		# This handler doesn't obey port argument
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
			
