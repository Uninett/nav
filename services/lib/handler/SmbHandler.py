"""
$Id: SmbHandler.py,v 1.5 2002/07/08 14:13:33 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/SmbHandler.py,v $
"""
import os,re
from job import JobHandler, Event
pattern = re.compile(r'domain=\[[^\]]+\] os=\[([^\]]+)\] server=\[([^\]]+)\]',re.I) #tihihi
class SmbHandler(JobHandler):
	"""
	args:
		'username'
		'password'
		'port'
	"""
	def __init__(self, serviceid, boksid, ip, args, version,db=None):
		address = (ip,args.get('port',139))
		JobHandler.__init__(self,'smb',serviceid,boksid,address,args,version,db=db)
	def execute(self):
		args = self.getArgs()
		username = args.get('username','')
		password = args.get('password','')

		if password and username:
			s = '-U ' + username + '%' + password
		else:
			s = '-N'

		ip,port = self.getAddress()
		s = os.popen('./Timeout.py -t %s /usr/local/samba/bin/smbclient -L %s -p %i %s' % (self.getTimeout(),ip,port,s)).read()
		version = pattern.search(s) and ' '.join(pattern.search(s).groups())
		if version:
			self.setVersion(version)
			return Event.UP,'OK'
		else:
			return Event.DOWN,'error %s' % s.strip().split('\n')[-1]

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
								
