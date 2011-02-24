# -*- coding: ISO8859-1 -*-
#
# Copyright 2002 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Some code from Timothy O'Malley's TimeoutSocket.py
#
# $Id: $
# Authors: Erik Gorset <erikgors@stud.ntnu.no>
#          Magnus Nordseth <magnun@stud.ntnu.no>
#
"""
Socket module with timeout.
"""
import time, socket, sys, types, string
from select import select
from errno import errorcode

class Timeout(Exception):
    pass

class socketwrapper(socket.socket):
    def __init__(self, timeout):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
        self.settimeout(timeout)
        self.s = self  # to handle ssl properly

    def readline(self):
        line = ''
        while 1:
            s = self.recv(1024)
            line += s
            if '\n' in line or not s:
                return line
    def write(self, line):
        if line[-1] != '\n':
            line += '\n'
        self.send(line)



class timeoutsocket:
    def __init__(self, timeout):
        self.timeout = timeout
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, address):
        self.s.setblocking(0)
        try:
            self.s.connect(address)
        except socket.error, (number, info):
            if not errorcode[number] == 'EINPROGRESS':
                raise
        self.s.setblocking(1)
        r, w, e = select([], [self], [], self.timeout)
        if not w:
            raise Timeout('Timeout in connect after %i sec' %\
                      self.timeout)
    def recv(self, *args):
        r, w, e = select([self.s], [], [], self.timeout)
        if not r:
            raise Timeout('Timeout in recv after %i sec' % \
                      self.timeout)
        return self.s.recv(*args)
    def readline(self):
        line = ''
        while 1:
            s = self.recv(1024)
            line += s
            if '\n' in line or not s:
                return line
    def send(self, *args):
        r, w, e = select([], [self.s], [], self.timeout)
        if not w:
            raise Timeout('Timeout in write after %i sec' % \
                      self.timeout)
        self.s.send(*args)
    
    def write(self, line):
        if line[-1] != '\n':
            line += '\n'
        self.send(line)
    def close(self):
        self.s.close()
    def makefile(self, flags="r", bufsize=-1):
        #self._copies = self._copies +1
        return TimeoutFile(self, flags, bufsize)
            

    #def makefile(self,*args):
    #    return self.s.makefile(*args)
    def fileno(self):
        return self.s.fileno()
    def sendall(self, *args):
        r, w, e = select([], [self.s], [], self.timeout)
        if not w:
            raise Timeout('Timeout in write after %i sec' % \
                      self.timeout)
        return self.s.sendall(*args)
    

class TimeoutFile:
    """TimeoutFile object
    Implements a file-like object on top of TimeoutSocket.
    This is a slightly modified version of the TimeoutFile object
    in Timothy O'Malley's TimeoutSocket.py.

    """
    
    def __init__(self, sock, mode="r", bufsize=4096):
        self._sock          = sock
        self._bufsize       = 4096
        if bufsize > 0: self._bufsize = bufsize
        if not hasattr(sock, "_inqueue"): self._sock._inqueue = ""

    def __getattr__(self, key):
        return getattr(self._sock, key)

    def close(self):
        self._sock.close()
        self._sock = None
    
    def write(self, data):
        self.send(data)

    def read(self, size=-1):
        _sock = self._sock
        _bufsize = self._bufsize
        while 1:
            datalen = len(_sock._inqueue)
            if datalen >= size >= 0:
                break
            bufsize = _bufsize
            if size > 0:
                bufsize = min(bufsize, size - datalen )
            buf = self.recv(bufsize)
            if not buf:
                break
            _sock._inqueue = _sock._inqueue + buf
        data = _sock._inqueue
        _sock._inqueue = ""
        if size > 0 and datalen > size:
            _sock._inqueue = data[size:]
            data = data[:size]
        return data

    def readline(self, size=-1):
        _sock = self._sock
        _bufsize = self._bufsize
        while 1:
            idx = string.find(_sock._inqueue, "\n")
            if idx >= 0:
                break
            datalen = len(_sock._inqueue)
            if datalen >= size >= 0:
                break
            bufsize = _bufsize
            if size > 0:
                bufsize = min(bufsize, size - datalen )
            buf = self.recv(bufsize)
            if not buf:
                break
            _sock._inqueue = _sock._inqueue + buf

        data = _sock._inqueue
        _sock._inqueue = ""
        if idx >= 0:
            idx = idx + 1
            _sock._inqueue = data[idx:]
            data = data[:idx]
        elif size > 0 and datalen > size:
            _sock._inqueue = data[size:]
            data = data[:size]
        return data

    def readlines(self, sizehint=-1):
        result = []
        data = self.read()
        while data:
            idx = string.find(data, "\n")
            if idx >= 0:
                idx = idx + 1
                result.append( data[:idx] )
                data = data[idx:]
            else:
                result.append( data )
                data = ""
        return result

    def flush(self):  pass
        
if hasattr(socket, "setdefaulttimeout"):
    Socket = socketwrapper
else:
    Socket = timeoutsocket
