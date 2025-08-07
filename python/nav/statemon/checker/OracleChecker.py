#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Oracle database service checker"""

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event
import cx_Oracle


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
    hostname: Accessible from self.get_address() as pure FQDN hostname
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

    DESCRIPTION = "Oracle database"
    OPTARGS = (
        ('port', ''),
        ('sid', ''),
        ('username', ''),
        ('password', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=1521, **kwargs)

    def execute(self):
        user = self.args.get("username", "")
        ip, port = self.get_address()
        passwd = self.args.get("password", "")
        sid = self.args.get("sid", "")
        connect_string = (
            "%s/%s@(DESCRIPTION=(ADDRESS_LIST=(ADDRESS=("
            "COMMUNITY=TCP)(PROTOCOL=TCP)(Host=%s)(Port=%s)))("
            "CONNECT_DATA=(SID=%s)(GLOBAL_NAME=%s)))"
        ) % (user, passwd, ip, port, sid, sid)
        print("Connecting with: %s" % connect_string)
        try:
            connection = cx_Oracle.connect(connect_string)
            cursor = connection.cursor()
            cursor.arraysize = 50
            cursor.execute(
                """
                select version
                from sys.v_$instance"""
            )
            row = cursor.fetchone()
            version = row[0]
        except Exception as err:  # noqa: BLE001
            return Event.DOWN, str(err)
        finally:
            connection.close()
        return Event.UP, "Oracle " + version
