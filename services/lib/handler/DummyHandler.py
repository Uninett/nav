"""
$Id: DummyHandler.py,v 1.2 2002/07/01 16:10:53 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/handler/DummyHandler.py,v $
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
								
