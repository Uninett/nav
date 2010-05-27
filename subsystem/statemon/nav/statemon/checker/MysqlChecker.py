# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 University of Tromsø
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

import socket
from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event

class MysqlError(Exception):
    pass

class MysqlConnection:
    """
    Very minimal implementation of MySQL protocol.
    (Packet layer only.)
    Error messages from the server raise MysqlError exceptions.
    """
    
    def __init__(self, addr, timeout=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout != None:
            sock.settimeout(timeout)
        sock.connect(addr)
        self.file = sock.makefile('r+')

        self.seqno = 0

    def read_packet(self):
        header = self.file.read(4)

        ll = ord(header[0])
        mm = ord(header[1])
        hh = ord(header[2])
        size = hh << 16 | mm << 8 | ll
        seqno = ord(header[3])

        self.seqno = seqno

        data = self.file.read(size)

        if data.startswith('\xff'):
            raise MysqlError(data[3:])
        
        return data

    def write_packet(self, data):
        size = len(data)
        ll = size >> 16
        mm = (size >> 8) & 0xff 
        hh = size & 0xff 
        seqno = self.seqno = (self.seqno + 1) % 256

        header = '%c%c%c%c' % (hh, mm, ll, seqno)

        self.file.write(header + data)
        self.file.flush()

    def write_auth_packet(self, username):
        data = '\x85\xa4\x00\x00\x00%s\x00\x00' % username
        self.write_packet(data)

    def close(self):
        self.write_packet(chr(1))  # Send COM_QUIT
        self.file.close()
            
class MysqlChecker(AbstractChecker):
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "mysql", service, port=3306, **kwargs)

    def execute(self):

        try:
            #
            # Connect and read handshake packet.
            #
            conn = MysqlConnection(self.getAddress(), self.getTimeout())
            data = conn.read_packet()

            #
            # Get server version from handshake
            #
            version = data[1:].split('\0')[0]  # Null terminated string
            self.setVersion(version)

            #
            # Send authentication packet to make server happy.
            # (If we don't do this, the server will be angry at
            # us for a while.)
            #
            conn.write_auth_packet('navmon')
            try:
                conn.read_packet()
            except MysqlError, err:
                pass  # Ignore login error

            conn.close()

            return Event.UP, 'OK'
        
        except MysqlError, err:
            return Event.DOWN, str(err)
            
    
def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = []
    return requiredArgs
