"""
$Id: DcHandler.py,v 1.5 2002/12/09 15:33:15 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/DcHandler.py,v $
"""

from job import JobHandler, Event
import os

class DcHandler(JobHandler):
	"""
	Required argument:
	username
	"""
	def __init__(self, serviceid, boksid, ip, args, version, sysname):
		address = (ip, 0)
		JobHandler.__init__(self, 'dc', serviceid, boksid, address, args, version,sysname)

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
