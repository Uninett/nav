"""
$Id: jobmap.py,v 1.2 2003/06/19 12:50:34 magnun Exp $                                                                                                                              
This file is part of the NAV project.

Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Magnus Nordseth <magnun@stud.ntnu.no>
	Erik Gorset	<erikgors@stud.ntnu.no>
"""
import os, re

class checkermap(dict):
    DEBUG = 0
    def __init__(self):
        dict.__init__(self)
        self.parsedir()


    def register(self, service, handler):
        if not service in self:
            self[service] = handler

    def get(self, service):
        exec( "import "+ self[service])
        return eval(self[service]+'.'+self[service])

    def parsedir(self):
        """
        Parses the dir lib/handler for Handlers.

        """
        files=os.listdir("./lib/checker/")
        handlerpattern="Checker.py"
        for file in files:
            if len(file) > len(handlerpattern) and file[len(file)-len(handlerpattern):]==handlerpattern:
                key = file[:-len(handlerpattern)].lower()
                handler = file[:-3]
		if self.DEBUG:
	                print "Registering checker %s from module %s" % (key, handler)
                self[key]=handler
                
