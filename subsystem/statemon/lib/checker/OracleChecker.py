"""
$Id: OracleChecker.py,v 1.1 2003/06/25 15:41:13 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/checker/OracleChecker.py,v $


This file is part of the NAV project.

Copyright (c) 2002 by NTNU, ITEA nettgruppen
Author: Arve Vanvik <arveva@itea.ntnu.no>
"""

from abstractChecker import AbstractChecker
from event import Event
import cx_Oracle, string, exceptions, sys
import os
# Don't ask me why this is necessary
os.environ['ORACLE_HOME']='/ora01/OraHome1'

class OracleChecker(AbstractChecker):
    """
    Handle Oracle databases.

    Arguments to this handler:

    port    : Remote tcp-port where Oracle Listener is living. Default is 1521.
    sid     : Database SID
    hostname: Accessible from self.getAddress() as pure FQDN hostname
    username: Default is nav_agent
    password: Default is ag3gva_r
    """
    def __init__(self, *args):
        AbstractChecker.__init__(self,'oracle',port=1521, *args)
    def execute(self):
        args = self.getArgs()
        user = args.get("username","")
        ip, port = self.getAddress()
        passwd = args.get("password","")
        sid = args.get("sid","")
        connect_string = "%s/%s@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(COMMUNITY=TCP)(PROTOCOL=TCP)(Host=%s)(Port=%s)))(CONNECT_DATA=(SID=%s)(GLOBAL_NAME=%s)))" % (user, passwd, ip, port, sid, sid)
        print "Connecting with: %s" % connect_string
        try:
            connection = cx_Oracle.connect(connect_string)
            cursor = connection.cursor()
            cursor.arraysize = 50
            cursor.execute("""
                select version
                from sys.v_$instance""")
            row = cursor.fetchone()
            version = row[0]
            connection.close()
        except:
            return Event.DOWN, str(sys.exc_value) 
        return Event.UP, "OK, Oracle" + version

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
