"""
$Id: jobmap.py,v 1.1 2002/06/28 09:19:58 erikgors Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/jobmap.py,v $
"""
import os, re

class jobmap(dict):
    DEBUG = 0
    def __init__(self):
        dict.__init__(self)
        self.parsedir()


    def register(self, service, handler):
        if not service in self:
            self[service] = handler

#    def __getitem__(self, service):
#        exec( "import "+ self[service])
#        print self[service]+'.'+self[service]
#        return eval(self[service]+'.'+self[service])

    def get(self, service):
        exec( "import "+ self[service])
        return eval(self[service]+'.'+self[service])

    def parsedir(self):
        """
        Parses the dir lib/handler for Handlers.

        """
        files=os.listdir("./lib/handler/")
        handlerpattern="Handler.py"
        for file in files:
            if len(file) > len(handlerpattern) and file[len(file)-len(handlerpattern):]==handlerpattern:
                key = file[:-len(handlerpattern)].lower()
                handler = file[:-3]
		if self.DEBUG:
	                print "Registering handler %s from module %s" % (key, handler)
                self[key]=handler
                
