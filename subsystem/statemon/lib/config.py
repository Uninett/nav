"""
$Id: config.py,v 1.1 2003/03/26 16:01:43 magnun Exp $                                                                                                                              
This file is part of the NAV project.

Abstraction for the various config files used
by servicemon and pinger.
Implements the singleton pattern ensuring only one
instance created.
                                                                                                                                 
Copyright (c) 2002 by NTNU, ITEA nettgruppen                                                                                      
Author: Magnus Nordseth <magnun@stud.ntnu.no>
"""

import os, re

CONFIGFILEPATH=['/usr/local/nav/navme/etc/conf/','.']

class Conf(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        self._configfile=None
        for path in CONFIGFILEPATH:
            file=os.path.join(os.path.abspath(path),self._file)
            try:
                self._configfile=open(file, "r")
                break
            except IOError:
                pass

        if self._configfile is None:
            print "Failed to open %s" % self._file
            os.sys.exit(0)
        self._regexp=re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)",re.M)
        self.parsefile()
        self._configfile.close()

    def parsefile(self):
        for (key, value) in self._regexp.findall(self._configfile.read()):
            if self.validoptions:
                if key.strip() in self.validoptions:
                    self[key.strip()]=value.strip()
            else:
                self[key.strip()]=value.strip()

def dbconf(*args, **kwargs):
    if _dbconf._instance is None:
        _dbconf._instance=_dbconf(*args,**kwargs)
    return _dbconf._instance

class _dbconf(Conf):
    _instance=None
    def __init__(self, *args, **kwargs):
        self._file=kwargs.get('configfile','db.conf')
        # Valid configoptions must be specified in this list
        self.validoptions=["dbhost", "dbport", "db_nav", "userpw_manage"]
        Conf.__init__(self, *args, **kwargs)

class _serviceconf(Conf):
    _instance=None
    def __init__(self, *args, **kwargs):
        self._file=kwargs.get('configfile','servicemon.conf')
        self.validoptions=[]
        Conf.__init__(self, *args, **kwargs)


def serviceconf(*args, **kwargs):
    if _serviceconf._instance is None:
        _serviceconf._instance=_serviceconf(*args,**kwargs)
    return _serviceconf._instance

class _pingconf(Conf):
    _instance=None
    def __init__(self, *args, **kwargs):
        self._file=kwargs.get('configfile','pinger.conf')
        self.validoptions=[]
        Conf.__init__(self, *args, **kwargs)


def pingconf(*args, **kwargs):
    if _pingconf._instance is None:
        _pingconf._instance=_pingconf(*args,**kwargs)
    return _pingconf._instance



