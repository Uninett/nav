"""
$Id$
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/checker/PortChecker.py,v $
"""
import select

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import  Event
from nav.statemon import Socket
class PortChecker(AbstractChecker):
	def __init__(self,service, **kwargs):
		AbstractChecker.__init__(self,'port', service, port=23, **kwargs)
	def execute(self):
		s = Socket.Socket(self.getTimeout())
		s.connect(self.getAddress())
		r,w,x = select.select([s],[],[],self.getTimeout())
		if r:
			s.readline()
		status = Event.UP
		txt = 'Alive'
		s.close()

		return status,txt

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
								
