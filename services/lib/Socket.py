"""
$Id: Socket.py,v 1.4 2002/08/26 20:55:02 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/Socket.py,v $
"""

import time,socket,sys,types
from select import select
from errno import errorcode

class Timeout(Exception):
	pass

class Socket:
	def __init__(self,timeout):
		self.timeout = timeout
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
	def recv(self,*args):
		print "I Socket.recv()"
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
		print "I Socket.send()"
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
	def makefile(self,*args):
		return self.s.makefile(*args)
	def fileno(self):
		return self.s.fileno()
	def sendall(self,*args):
		print "I sendall"
		r,w,e = select([],[self.s],[],self.timeout)
		if not w:
			raise Timeout('Timeout in write after %i sec' % self.timeout)
		return self.s.sendall(*args)
	

