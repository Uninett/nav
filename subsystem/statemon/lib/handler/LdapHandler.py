"""
$Id: LdapHandler.py,v 1.2 2003/06/15 13:25:16 bgrotan Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/LdapHandler.py,v $
"""

from job import JobHandler
from event import Event
import ldap,base64,string

class LdapHandler(JobHandler):
	"""
	"""

	def __init__(self,service, **kwargs):
		JobHandler.__init__(self, "ldap", service, **kwargs)
		self.setPort(self.getPort() or 389)
	def execute(self):

		args = self.getArgs()
		# we can connect in 2 ways. By hostname/ip (and portnumber)
		# or by ldap-uri
		if args.has_key("url"):
			if is_ldap_url(args["url"]):
				l = ldap.initialize(args["url"])
		else:
			l = ldap.open(self.getAddress())
		username = ""
		pwd = ""

		timeout = self.getTimeout()
		try:
			l.simplebind(user,pwd)
			if args.has_key("version"):
				version = args["version"]
				if (version==2):
					l.protocol_version = ldap.VERSION2
				elif (version==3):
					l.protocol_version = ldap.VERSION3
				else:
					return Event.DOWN, "unsupported protocol version"
			else:
				# default is protocol-version 3
				try:
					l.protocol_version = ldap.VERSION3
				except Exception,e:
					return Event.DOWN, "unsupported protocol version"

			if args.has_key("base"):
				if args.has_key("scope"):
					scope = args["scope"]
					scope = "ldap.SCOPE_"+scope.upper()
					if args.has_key("filter"):
						filter = args["filter"]
						if args.has_key("attrs"):
							attrs = args["attrs"]
						else:
							attrs = "None"
					else:
						filter = "objectclass=dcObject"
				else:
					scope = ldap.SCOPE_SUBTREE
			else:
				base = "dc=ntnu,dc=no"
			try:
				myres = l.search(base, scope, filter)
				dn = myres[0][0]
				mydict = myres[0][1]
			except Exception,e:
				return Event.DOWN, "Failed search on %s for %s: %s" % (self.getAddress(), filter, str(e))
				
			l.unbind()
			# krever enten monitor-backend og søk etter base cn=monitor eller håndtere dette
			# selv i openldap-2.0.x 
			# self.setVersion(version)
		except Exception, e:
			return Event.DOWN, "Failed to bind to %s: %s" % (self.getAddress(), str(e))
		return Event.IP, version


def getRequiredArgs():
	""" 
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs

