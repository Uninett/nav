"""
$Id: SmbHandler.py,v 1.10 2002/12/09 15:33:15 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/SmbHandler.py,v $
"""
import os,re
from job import JobHandler, Event
pattern = re.compile(r'domain=\[[^\]]+\] os=\[([^\]]+)\] server=\[([^\]]+)\]',re.I) #tihihi
class SmbHandler(JobHandler):
	"""
	args:
	        'hostname'
		'username'
		'password'
		'port'
	"""
	def __init__(self, serviceid, boksid, ip, args, version,sysname):
		address = (ip,args.get('port',139))
		JobHandler.__init__(self,'smb',serviceid,boksid,address,args,version,sysname)
	def execute(self):
		ip,port = self.getAddress()
		args = self.getArgs()
		host = args.get('hostname',ip)
		username = args.get('username','')
		password = args.get('password','')

		if password and username:
			s = '-U ' + username + '%' + password
		else:
			s = '-N'


		s = os.popen('/usr/local/samba/bin/smbclient -L %s -p %i %s 2>/dev/null' % (host,port,s)).read()
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
								
