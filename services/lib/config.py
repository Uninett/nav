"""
$Author: magnun $
$Id: config.py,v 1.1 2002/06/13 14:00:24 magnun Exp $
$Source: /usr/local/cvs/navbak/navme/services/lib/config.py,v $


"""
import os

CONFIGFILE="/usr/local/nav/local/etc/conf/db.conf"

class config:
    def __init__(self):
        try:
            self._configfile=open(CONFIGFILE, "r")
            self.config={}
        except:
            print "Failed to open %s" % CONFIGFILE
            os.sys.exit(0)

    def  parsefile(self):
        for eachline in self._configfile.xreadlines():
            eachline = eachline.strip()
            if eachline[0] != "#" and eachline[0] != "":
                key=self.config.split("=")[0]
                value=self.config.split("=")[1]
                print "%s : %s" % (key, value)


if __name__ == "__main__":
    foo=config()
    foo.parsefile()
                
