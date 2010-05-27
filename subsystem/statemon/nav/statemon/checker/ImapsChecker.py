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
from nav.statemon.event import  Event
from nav.statemon import  Socket
import imaplib
import socket

#class IMAPConnection(imaplib.IMAP4):
#    def __init__(self, timeout, host, port):
#        self.timeout=timeout
#        imaplib.IMAP4.__init__(self, host, port)
#
#
#    def open(self, host, port):
#        """
#        Overload imaplib's method to connect to the server
#        """
#        self.sock=Socket.Socket(self.timeout)
#        self.sock.connect((self.host, self.port))
#        self.file = self.sock.makefile("rb")

class IMAPSConnection(imaplib.IMAP4):
    """IMAP4 client class over SSL connection

    Instantiate with: IMAP4_SSL([host[, port[, keyfile[, certfile]]]])

            host - host's name (default: localhost);
            port - port number (default: standard IMAP4 SSL port).
            keyfile - PEM formatted file that contains your private key (default: None);
            certfile - PEM formatted certificate chain file (default: None);

    for more documentation see the docstring of the parent class IMAP4.
    """


    def __init__(self, timeout, host = '', port = 993, keyfile = None, certfile = None):
        self.keyfile = keyfile
        self.certfile = certfile
        self.timeout = timeout
        imaplib.IMAP4.__init__(self, host, port)
        # self.ctx = SSL.Context(SSL.SSLv23_METHOD)


    def open(self, host, port ):
        """Setup connection to remote server on "host:port".
            (default: localhost:standard IMAP4 SSL port).
        This connection will be used by the routines:
            read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        # try with 2.3 socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)

        # som old things...
        #self.sock = Socket.Socket(self.timeout)
        #self.sslobj = SSL.Connection(self.ctx, self.sock)
        #self.sslobj = Socket.ssl(self.host, self.port, self.timeout)
        #self.sslobj.connect((host, port))
        #self.sock.connect((host, port))
        #self.sslobj = socket.ssl(self.sock.s, self.keyfile, self.certfile)
        #self.sslobj = Socket.ssl(self.sock.s, self.timeout, self.keyfile, self.certfile)


    def read(self, size):
        """Read 'size' bytes from remote."""
        # sslobj.read() sometimes returns < size bytes
        data = self.sslobj.read(size)
        while len(data) < size:
            data += self.sslobj.read(size-len(data))

        return data


    def readline(self):
        """Read line from remote."""
        # NB: socket.ssl needs a "readline" method, or perhaps a "makefile" method.
        line = ""
        while 1:
            char = self.sslobj.read(1)
            line += char
            if char == "\n": return line


    def send(self, data):
        """Send data to remote."""
        # NB: socket.ssl needs a "sendall" method to match socket objects.
        bytes = len(data)
        while bytes > 0:
            sent = self.sslobj.write(data)
            if sent == bytes:
                break    # avoid copy
            data = data[sent:]
            bytes = bytes - sent


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

class ImapsChecker(AbstractChecker):
    """
    Valid arguments:
    port
    username
    password
    """
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "imaps", service, port=993, **kwargs)
    def execute(self):
        args = self.getArgs()
        user = args.get("username","")
        ip, port = self.getAddress()
        passwd = args.get("password","")
        m = IMAPSConnection(self.getTimeout(), ip, port)
        ver = m.welcome
        if user:
            m.login(user, passwd)
            m.logout()
        version=''
        ver=ver.split(' ')
        if len(ver) >= 2:
            for i in ver[2:]:
                if i != "at":
                    version += "%s " % i
                else:
                    break
        self.setVersion(version)
        
        return Event.UP, version

def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = ['username', 'password']
    return requiredArgs

