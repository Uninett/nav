"""
$Id: DummyHandler.py,v 1.1 2003/03/26 16:02:17 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/handler/DummyHandler.py,v $
"""


from job import JobHandler, Event
class DummyHandler(JobHandler):
	def __init__(self,*args):
		JobHandler.__init__(self,'dummy',*args)
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
								
