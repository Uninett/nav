"""
$Author: magnun $
$Id: config.py,v 1.4 2002/06/15 21:27:55 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/Attic/config.py,v $


"""
import os, re


# Valid configoptions must be specified in this list
validoptions=["dbhost", "dbport", "db_nav", "userpw_manage"]

class config(dict):
    def __init__(self, configfile="db.conf"):
        dict.__init__(self)
        try:
            self._configfile=open(configfile, "r")
            self._regexp=re.compile(r"^([^#=]+)\s*=\s*([^#\n]+)",re.M)
            self.parsefile()
        except:
            print "Failed to open %s" % CONFIGFILE
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
                
