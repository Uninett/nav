# -*- coding: utf-8 -*-
#
# Copyright (C) 2003,2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
import cx_Oracle, string, exceptions, sys
import os

class OracleChecker(AbstractChecker):
    """

    Description:
    ------------
    This checker tries to connect to a given Oracle database.
    
    The checker relies on that the neccesary Oracle software have been
    installed and that the following Oracle environment variables
    have been set:

    - $ORACLE_HOME
    - $NLS_LANG

    
    Arguments:
    ----------
    hostname: Accessible from self.getAddress() as pure FQDN hostname
    port    : Remote tcp-port where Oracle Listener is living. Default is 1521.
    sid     : Database SID
    username: An Oracle database account with the following permissions:
              - CREATE SESSION 
              - ALTER SESSION
              - select on sys.v_$instance
    password: Password for the Oracle database account.


    Return values:
    --------------
    Succesful connection:
        return Event.UP, "Oracle " + version
    Failure to connect:
        return Event.DOWN, str(sys.exc_value)

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
        return Event.UP, "Oracle " + version
