"""
$Id: event.py,v 1.1 2003/06/16 11:51:50 magnun Exp $

This file is part of the NAV project.                                                                                             
                                                                                                                                 
Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Magnus Nordseth <magnun@stud.ntnu.no>
"""
import time
class Event:
    UP = 'UP'
    DOWN = 'DOWN'
    
    def __init__(self,serviceid,netboxid,type,status,info,eventtype='serviceState', version=''):
        self.serviceid = serviceid
        self.netboxid = netboxid
        self.type = type
        self.status = status
        self.info = info
        self.eventtype = eventtype
        self.version = version
        self.sysname = ""
        self.handler = ""
        self.time = time.strftime('%H:%M:%S')
        
    def setSysname(self, name):
        self.sysname=name
            
            
