"""
$Id: DummyChecker.py,v 1.1 2003/06/19 12:53:07 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/DummyChecker.py,v $
"""


from abstractChecker import AbstractChecker, Event
class DummyChecker(AbstractChecker):
	def __init__(self,*args):
		AbstractChecker.__init__(self,'dummy',*args)
	def execute(self):
		import random
		time.sleep(random.random()*10)
		return Event.UP,'OK'

def getRequiredArgs():
	"""
	Returns a list of required arguments
	"""
	requiredArgs = []
	return requiredArgs
								
