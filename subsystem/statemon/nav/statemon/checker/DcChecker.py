"""
$Id: DcChecker.py,v 1.2 2003/06/20 09:34:45 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/checker/DcChecker.py,v $
"""

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
import os

class DcChecker(AbstractChecker):
	"""
	Required argument:
	username
	"""
	def __init__(self,service, **kwargs):
		AbstractChecker.__init__(self, "dc", service, **kwargs)

	def execute(self):
		args = self.getArgs()
		username = args.get('username','')
		if not username:
			return Event.DOWN, "Missing required argument: username"
		ip, host = self.getAddress()
		command = "/usr/local/samba/bin/rpcclient -U %% -c 'lookupnames %s' %s  2>/dev/null" % (username, ip)
		result = os.popen(command).readlines()
		if not result:
			return Event.UP, "Failed to check service"
		result = result[-1]
		if result.split(" ")[0] == username:
			return Event.UP, 'Ok'
		else:
			return Event.DOWN, result

				
def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = ['username']
	return requiredArgs
