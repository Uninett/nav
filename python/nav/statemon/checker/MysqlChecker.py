# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, 2020 Uninett AS
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
"""A MySQL service checker"""

import socket
import struct

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class MysqlChecker(AbstractChecker):
    """MySQL"""

    IPV6_SUPPORT = True

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=3306, **kwargs)

    def execute(self):
        conn = None
        try:
            #
            # Connect and read handshake packet.
            #
            conn = MysqlConnection(self.get_address(), self.timeout)
            data = conn.read_packet()

            #
            # Get server version from handshake
            #
            version = data[1:].split(b'\x00')[0]  # Null terminated string
            self.version = version.decode("utf-8")

            #
            # Send authentication packet to make server happy.
            # (If we don't do this, the server will be angry at
            # us for a while.)
            #
            conn.write_auth_packet('navmon')
            try:
                conn.read_packet()
            except MysqlError:
                pass  # Ignore login error

            return Event.UP, 'OK'

        except (MysqlError, socket.timeout) as err:
            return Event.DOWN, str(err)

        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass


class MysqlConnection(object):
    """Very minimal implementation of MySQL protocol. (Packet layer only.)

    Error messages from the server raise MysqlError exceptions.

    """

    def __init__(self, addr, timeout=None):
        host, _port = addr
        sock = socket.create_connection(addr, timeout)
        self.file = sock.makefile('rwb')

        self.seqno = 0

    def read_packet(self):
        header = self.file.read(4)

        lll, mmm, hhh, seqno = struct.unpack('BBBB', header)
        size = hhh << 16 | mmm << 8 | lll

        self.seqno = seqno

        data = self.file.read(size)
        if data.startswith(b'\xff'):
            error = data.removeprefix(b'\xff').decode("utf-8")
            raise MysqlError(error)

        return data

    def write_packet(self, data):
        size = len(data)
        lll = size >> 16
        mmm = (size >> 8) & 0xFF
        hhh = size & 0xFF
        seqno = self.seqno = (self.seqno + 1) % 256

        header = struct.pack("BBBB", hhh, mmm, lll, seqno)

        self.file.write(header + data)
        self.file.flush()

    def write_auth_packet(self, username):
        data = b'\x85\xa4\x00\x00\x00%s\x00\x00' % username.encode("utf-8")
        self.write_packet(data)

    def close(self):
        self.write_packet(b'\x01')  # Send COM_QUIT
        self.file.close()


class MysqlError(Exception):
    pass
