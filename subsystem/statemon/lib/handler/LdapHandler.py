"""
$Id: LdapHandler.py,v 1.4 2003/06/15 18:14:59 bgrotan Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/LdapHandler.py,v $
"""

from job import JobHandler
from event import Event
import ldap,base64,string

class LdapHandler(JobHandler):
	"""
	Handle LDAP-servers. It can be quite simple (just try anonymous bind) or quite
	sophisticated with additional search and retrieve specific dn's with specific attributes.

	Arguments to this handler (with explenations):
	port:	remote tcp-port where ldap-server is living. Default is 389
	hostname: accessible from self.getAddress() as pure FQDN hostname
	url:    if this is defined as arguments this will override hostname/port
		example-url: ldap://myserver.mydomain.com:389
	version: implies protocol-version of LDAP. Default is 3 - though 2 is also supported
	username: leave this blank if you want to bind anonymously
	password: leave this blank if you want to bind anonymously
	authtype: meant to handle authentication-types. Not implemented yet. Only simple auth yet
		types will be: TLS, SASL, simple, Kerberos
	base:	the server's basedn (e.g. dc=mydomain,dc=com)
	scope:	what level of the search will be needed? BASE, ONELEVEL and SUBTREE can be used
	filter: dn to search for. May have regexp and more. Example: cn=monitor
	compare: uses the function compare_s(dn, attr, value)  - useful for testing whether an object has a particular value (instead of doing a search with SCOPE_BASE and checking the value)
	attrs:  specific attributes you want to retrieve from searching filter (not implemented in this version)
	attr_val: regexp for matching attrs. If matched - Event.UP is returned - else Event.DOWN (not implemented in this version)

	NB! If compare is set/given - attrs and attr_val will be ignored!
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
		if args.has_key("username"):
			username = args["username"]
		else:
			username = ""
		if args.has_key("password"):
			pwd = args["password"]
		else:
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
			if args.has_key("compare"):
				try:
					result = l.compare_s(dn,attribute,value)
					if result:
						return Event.UP
					else:
						return Event.DOWN, "compare failed: %s:%s" % (attribute,value)
				except Exception,e:
					return Event.DOWN, "compare failed for some reason"

			elif:
				if args.has_key("base"):
					if (args["base"] == "cn=monitor"):
						my_res = l.search_s("base",ldap.SCOPE_BASE,"cn=monitor")
						my_res = my_res[0]
						my_dict = myres[1]
						version = my_dict["description"][0]
						self.setVersion(version)
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
					my_res = l.search(base, scope, filter, attrs)
					dn = my_res[0][0]
					mydict = my_res[0][1]
				except Exception,e:
					return Event.DOWN, "Failed ldapSearch on %s for %s: %s" % (self.getAddress(), filter, str(e))
				
				l.unbind()
		except Exception, e:
			return Event.DOWN, "Failed to bind to %s: %s" % (self.getAddress(), str(e))
		return Event.IP, version


def getRequiredArgs():
	""" 
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs

