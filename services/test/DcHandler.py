"""
$Id: DcHandler.py,v 1.1 2002/06/26 09:04:45 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/test/DcHandler.py,v $
"""

from job import JobHandler, Event
import os

class DcHandler(JobHandler):
	"""
	Required argument:
	username
	"""
	def __init__(self, serviceid, boksid, ip, args, version):
		address = (ip, 0)
		JobHandler.__init__(self, 'dc', serviceid, boksid, address, args, version)

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
