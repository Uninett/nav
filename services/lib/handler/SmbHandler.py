"""
$Id: SmbHandler.py,v 1.1 2002/06/27 11:49:04 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/SmbHandler.py,v $
"""

from job import JobHandler, Event
class SmbHandler(JobHandler):
	"""
	args:
		'username'
		'password'
		'port'
	"""
	def __init__(self, serviceid, boksid, ip, args, version):
		address = (ip,args.get('port',139))
		JobHandler.__init__(self,'smb',serviceid,boksid,address,args,version)
	def execute(self):
		args = self.getArgs()
		username = args.get('username','')
		password = args.get('password','')

		if password and username:
			s = '-U ' + username + '%' + password
		else:
			s = '-N'

		ip,port = self.getAddress()
		import os
		status = os.system('smbclient -L %s -p %i %s 2>/dev/null > /dev/null' %(ip,port,s))

		if status:
			return Event.DOWN,'error %i' % status
		else:
			return Event.UP,'OK'
