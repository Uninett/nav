"""
$Id: OracleHandler.py,v 1.1 2003/06/18 13:01:46 arveva Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/OracleHandler.py,v $
"""

from job import JobHandler, Event
import cx_Oracle

# connect via SQL*Net string or by each segment in a separate argument
connection = cx_Oracle.connect("nav_agent/ag3gva_r@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(COMMUNITY=TCP)(PROTOCOL=TCP)(Host=shinsaku.itea.ntnu.no)(Port=1521)))(CONNECT_DATA=(SID=FSKURS)(GLOBAL_NAME=FSKURS.ntnu.no)))")

        
cursor = connection.cursor()
cursor.arraysize = 50
cursor.execute("""
    select 'x', 'y', 'z'
    from dual""")
for column_1, column_2, column_3 in cursor.fetchall():
    print "Values:", column_1, column_2, column_3

class OracleHandler(JobHandler):
    """
    Handle Oracle databases.

    Arguments to this handler (with explenations):

    port    : Remote tcp-port where Oracle Listener is living. Default is 1521.
    sid     : Database SID
    hostname: Accessible from self.getAddress() as pure FQDN hostname
    username: Default is nav_agent
    password: Default is ag3gva_r
    """

#	def __init__(self, serviceid, boksid, ip, args, version):
#		port = args.get("port", 3306)
#		JobHandler.__init__(self, "mysql", serviceid, boksid, (ip, port), args, version)
#	def execute(self):
#		s = Socket.Socket(self.getTimeout())
#		s.connect(self.getAddress())
#		line = s.readline()
#		s.close()
#		#this is ugly
#		try:
#			version = line.split('-')[1].split('\n')[1].strip()
#			self.setVersion(version)
#		except:
#			return Event.DOWN, line
#		return Event.UP, 'OK'

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
