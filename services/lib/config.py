"""
$Author: magnun $
$Id: config.py,v 1.7 2002/07/15 23:01:45 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/config.py,v $

Implements the singleton pattern ensuring only one
instance created.
"""
import os, re


# Valid configoptions must be specified in this list
validoptions=["dbhost", "dbport", "db_nav", "userpw_manage"]

def config(configfile="db.conf"):
    if _config._instance is None:
        _config._instance=_config(configfile)
    return _config._instance

class _config(dict):
    _instance=None
    def __init__(self, configfile="db.conf"):
        dict.__init__(self)
        try:
            self._configfile=open(configfile, "r")
            self._regexp=re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)",re.M)
            self.parsefile()
        except:
            print "Failed to open %s" % configfile
            os.sys.exit(0)

    def parsefile(self):
        for (key, value) in self._regexp.findall(self._configfile.read()):
            if key.strip() in validoptions:
                self[key.strip()]=value.strip()
            else:
                pass
                #print "Unknown config option: %s" % key.strip()



if __name__ == "__main__":
    foo=config()
    foo.parsefile()
                
