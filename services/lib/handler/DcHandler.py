"""
$Id: DcHandler.py,v 1.6 2003/01/03 15:43:54 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/DcHandler.py,v $
"""

from job import JobHandler, Event
import os

class DcHandler(JobHandler):
	"""
	Required argument:
	username
	"""
	def __init__(self,service):
		service['ip']=(service['ip'], 0)
		JobHandler.__init__(self, "dc", service)

	def execute(self):
		args = self.getArgs()
		username = args.get('username','')
		if not username:
			return Event.DOWN, "Missing required argument: username"
		ip, host = self.getAddress()
		command = "/usr/local/samba/bin/rpcclient -U %% -c 'lookupnames %s' %s  2>/dev/null" % (username, ip)
		result = os.popen(command).readlines()[-1]
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
