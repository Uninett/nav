"""
$Id$
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
		# map service to t=tcp or u=udp
		mapper = {'nfs':'t',
			  'status':'t',
			  'nlockmgr':'u',
			  'mountd':'t',
			  'ypserv':'u',
			  'nfs':'u',
			  'ypbind':'u'
			  }
		default = ['nfs', 'nlockmgr', 'mountd', 'status']
		required = args.get('required','')
		if not required:
			required = default
		else:
			required = required.split(',')

		ip, port = self.getAddress()
		for service in required:
			protocol = mapper.get(service, '')
			if not protocol:
				return Event.DOWN, "Unknown argument: [%s], can only check %s" % (service, str(mapper.keys()))
			output = os.popen('/usr/sbin/rpcinfo -%s %s %s' % (protocol,ip,service))
			output = output.read()
			if output.find("ready"):
				continue
			if outut.find("not available"):
				return Event.DOWN, "%s not avail" % service
			if not output:
				return Event.DOWN,'timeout'

		return Event.UP, "Ok"

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = ['required']
	return requiredArgs
			
