"""
$Id: Socket.py,v 1.1 2003/03/26 16:01:43 magnun Exp $                                                                                                                              
This file is part of the NAV project.

Socket module with timeout.

Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Erik Gorset	<erikgors@stud.ntnu.no>
"""
import time,socket,sys,types,string
from select import select
from errno import errorcode

class Timeout(Exception):
	pass

def ssl(sock, sock, keyfile=None, certfile=None):
	"""
	Returns an sslsocket with timeout support.
	"""
	return SslSocket(timeout, sock, keyfile, certfile)

class SslSocket:
	def __init__(self, timeout, realsock, keyfile=None, certfile=None):
		self.timeout = timeout
		self.realsock = realsock
		self.sslsock = socket.ssl(sock, keyfile, certfile)
	def read(*args):
		r,w,e = select([self.realsock],[],[],self.timeout)
		if not r:
			raise Timeout('Timeout in readafter %i sec' % self.timeout)
		return self.sslsock.read(*args)
	def write(*args):
		r,w,e = select([],[self.realsock],[],self.timeout)
		if not w:
			raise Timeout('Timeout in write after %i sec' % self.timeout)
		return self.sslsock.write(*args)
	

class Socket:
	def __init__(self, timeout):
		self.timeout = timeout
		if sock:
			self.s = sock
		else:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def connect(self,address):
		self.s.setblocking(0)
		try:
			self.s.connect(address)
		except socket.error, (number,info):
			if not errorcode[number] == 'EINPROGRESS':
				raise
		self.s.setblocking(1)
		r,w,e = select([],[self],[],self.timeout)
		if not w:
			raise Timeout('Timeout in connect after %i sec' % self.timeout)
	def read(self, buf):
		return self.recv(buf)

	def recv(self,*args):
		r,w,e = select([self.s],[],[],self.timeout)
		if not r:
			raise Timeout('Timeout in recv after %i sec' % self.timeout)
		return self.s.recv(*args)
	def readline(self):
		line = ''
		while 1:
			s = self.recv(1024)
			line += s
			if '\n' in line or not s:
				return line
	def send(self,*args):
		r,w,e = select([],[self.s],[],self.timeout)
		if not w:
			raise Timeout('Timeout in write after %i sec' % self.timeout)
		self.s.send(*args)
	
	def write(self,line):
		if line[-1] != '\n':
			line += '\n'
		self.send(line)
	def close(self):
		self.s.close()
	def makefile(self, flags="r", bufsize=-1):
		#self._copies = self._copies +1
		return TimeoutFile(self, flags, bufsize)
		    

	#def makefile(self,*args):
	#	return self.s.makefile(*args)
	def fileno(self):
		return self.s.fileno()
	def sendall(self,*args):
		r,w,e = select([],[self.s],[],self.timeout)
		if not w:
			raise Timeout('Timeout in write after %i sec' % self.timeout)
		return self.s.sendall(*args)
	

class TimeoutFile:
    """TimeoutFile object
    Implements a file-like object on top of TimeoutSocket.
    This is a slightly modified version of the TimeoutFile ovject
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
	    
