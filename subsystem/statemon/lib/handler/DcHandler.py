"""
$Id: DcHandler.py,v 1.1 2003/03/26 16:02:17 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/DcHandler.py,v $
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
