# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# $Id$
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
from nav.statemon.Socket import Socket
import smtplib
import re

class SMTP(smtplib.SMTP):
	def __init__(self,timeout, host = '',port = 25):
		self.timeout = timeout
		smtplib.SMTP.__init__(self,host,port)
	def connect(self, host='localhost', port = 25):
		self.sock = Socket(self.timeout)
		self.sock.connect((host,port))
		return self.getreply()

class SmtpChecker(AbstractChecker):
	# Regexp for matching version strings:
	# Most SMTP servers add a date after one of the characters
	# ",", ";" or "#", we don't need that part of the version
	# string
	versionMatch = re.compile(r'([^;,#]+)')
	
	def __init__(self,service, **kwargs):
		AbstractChecker.__init__(self, "smtp", service,port=25, **kwargs)
	def execute(self):
		ip,port = self.getAddress()
		s = SMTP(self.getTimeout())
		code,msg = s.connect(ip,port)
		try:
			s.quit()
		except smtplib.SMTPException:
			pass
		if code != 220:
			return Event.DOWN,msg
		try:
			domain, version = msg.strip().split(' ', 1)
		except ValueError:
			version = ''
		match = self.versionMatch.match(version)
		if match:
			version = match.group(0)
		self.setVersion(version)
		return Event.UP,msg

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
			
