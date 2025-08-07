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
"""IMAP over SSL service checker"""

import contextlib
import socket
import imaplib

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class ImapsChecker(AbstractChecker):
    """Internet mail application protocol (ssl)"""

    IPV6_SUPPORT = True
    DESCRIPTION = "Internet mail application protocol (ssl)"
    ARGS = (
        ('username', ''),
        ('password', ''),
    )
    OPTARGS = (
        ('port', ''),
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=993, **kwargs)

    def execute(self):
        user = self.args.get("username", "")
        ip, port = self.get_address()
        passwd = self.args.get("password", "")
        with contextlib.closing(IMAPSConnection(self.timeout, ip, port)) as session:
            ver = session.welcome
            if user:
                session.login(user, passwd)
                session.logout()
            version = ''
            ver = ver.split(' ')
            if len(ver) >= 2:
                for i in ver[2:]:
                    if i != "at":
                        version += "%s " % i
                    else:
                        break
            self.version = version

            return Event.UP, version


class IMAPSConnection(imaplib.IMAP4):
    """IMAP4 client class over SSL connection

    Instantiate with: IMAP4_SSL([host[, port[, keyfile[, certfile]]]])

            host - host's name (default: localhost);
            port - port number (default: standard IMAP4 SSL port).
            keyfile - PEM formatted file that contains your private key
                      (default: None);
            certfile - PEM formatted certificate chain file (default: None);

    for more documentation see the docstring of the parent class IMAP4.
    """

    def __init__(self, timeout, host='', port=993, keyfile=None, certfile=None):
        self.keyfile = keyfile
        self.certfile = certfile
        self.timeout = timeout
        self.sslobj = None
        imaplib.IMAP4.__init__(self, host, port)

    def open(self, host, port):
        """Setup connection to remote server on "host:port".
            (default: localhost:standard IMAP4 SSL port).
        This connection will be used by the routines:
            read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        self.sock = socket.create_connection((host, port))
        self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)

    def read(self, size):
        """Read 'size' bytes from remote."""
        # sslobj.read() sometimes returns < size bytes
        data = self.sslobj.read(size)
        while len(data) < size:
            data += self.sslobj.read(size - len(data))

        return data

    def readline(self):
        """Read line from remote."""
        # socket.ssl really needs a "readline" method, or perhaps a "makefile"
        # method.
        line = ""
        while 1:
            char = self.sslobj.read(1)
            line += char
            if char == "\n":
                return line

    def send(self, data):
        """Send data to remote."""
        # NB: socket.ssl needs a "sendall" method to match socket objects.
        bytecount = len(data)
        while bytecount > 0:
            sent = self.sslobj.write(data)
            if sent == bytecount:
                break  # avoid copy
            data = data[sent:]
            bytecount = bytecount - sent

    def shutdown(self):
        """Close I/O established in "open"."""
        self.sock.close()

    def socket(self):
        """Return socket instance used to connect to IMAP4 server.

        socket = <instance>.socket()
        """
        return self.sock

    def ssl(self):
        """Return SSLObject instance used to communicate with the IMAP4 server.

        ssl = <instance>.socket.ssl()
        """
        return self.sslobj
