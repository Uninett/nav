"""
$Id: OracleHandler.py,v 1.2 2003/06/19 09:43:21 arveva Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/OracleHandler.py,v $
"""

from job import JobHandler, Event
import cx_Oracle

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
try:
    connection = cx_Oracle.connect("nav_agent/ag3gva_r@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(COMMUNITY=TCP)(PROTOCOL=TCP)(Host=shinsaku.itea.ntnu.no)(Port=1521)))(CONNECT_DATA=(SID=FSKURS)(GLOBAL_NAME=FSKURS.ntnu.no)))")
    cursor = connection.cursor()
    cursor.arraysize = 50
    cursor.execute("""
        select 'x', 'y', 'z'
                from dual""")
    for column_1, column_2, column_3 in cursor.fetchall():
                print "Values:", column_1, column_2, column_3

except:
#    return Event.DOWN, line
    print "feil"   
        
#		return Event.UP, 'OK'


def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
