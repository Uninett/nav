"""
$Id: OracleHandler.py,v 1.4 2003/06/20 12:46:45 arveva Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/OracleHandler.py,v $
"""

from job import JobHandler, Event
import cx_Oracle, string, exceptions, sys

#class OracleHandler(JobHandler):
#    """
#    Handle Oracle databases.
#
#    Arguments to this handler:
#
#    port    : Remote tcp-port where Oracle Listener is living. Default is 1521.
#    sid     : Database SID
#    hostname: Accessible from self.getAddress() as pure FQDN hostname
#    username: Default is nav_agent
#    password: Default is ag3gva_r
#    """

#    def __init__(self,service, **kwargs):
#        JobHandler.__init__(self, "oracle", service, port=1521, **kwargs)
#    def execute(self):


# Test values:
#print ""
#print "Test values:"
hostname = "shinsaku.itea.ntnu.no"
#print "Host: " + hostname

sid = "FSKURS"
#print "Database SID: " + sid


# Default values:
#print ""
#print "Default values:"
port = "1521"
#print "Listener port: " + port

username = "nav_agent"
#print "Default database username: " + username

password = "ag3gva_r"
#print "Default database password: " + password


# Connect string:
#print ""
connect_string = username + "/" + password + "@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(COMMUNITY=TCP)(PROTOCOL=TCP)(Host=" + hostname + ")(Port=" + port + ")))(CONNECT_DATA=(SID=" + sid + ")(GLOBAL_NAME=" + sid + ")))" 
#print "Connect String: "
#print connect_string

#print ""
print ""
print "Results: "


try:
    connection = cx_Oracle.connect(connect_string)
    cursor = connection.cursor()
    cursor.arraysize = 50
    cursor.execute("""
        select version
        from sys.v_$instance""")
    row = cursor.fetchone()
    version = row[0]        
    print "UP, Oracle " + version

except:
#    return Event.DOWN, line
    print "DOWN, " + str(sys.exc_value)
        
#		return Event.UP, 'OK'


def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
