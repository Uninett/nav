

"""
Utility which runs one service check against specified server.
Useful when writing new service checks or while debugging.
"""
import sys
import os
import getopt

from nav.statemon import debug
debug.setDebugLevel(7)
from nav.statemon import abstractChecker
from nav.statemon import checkermap


try:
    #opts, args = getopt.getopt(sys.argv[1:], "i:s:h:a:", ["ip:", "sysname:", "handler:", "args:"])
    opts, args = getopt.getopt(sys.argv[1:], "i:s:h:a:")
except Exception, e:
    print str(e)
    sys.exit(1)

serviceid=0
netboxid=0
sysname=""
ip = ""
handler = ""
args={}
version = ""
if not opts:
    print "Usage:"
    print "checkService -i <ip address> -s <sysname>  -h <handler>"
    print
    sys.exit(1)


for opt, val in opts:
    if opt in ("-i", "--ip"):
        ip = val
    elif opt in ("-s", "--sysname"):
        sysname = val
    elif opt in ("-h", "--handler"):
        handler = val
    #elif opt in ("-a", "--args"):
    #    try:
    #        args = eval(val)
    #    except:
    #        print "%s is not a dict" % val

readArgs = 1
print "Input additional arguments (key=val), empty line to continue:"
while readArgs:
    line = raw_input()
    if not line:
        readArgs = 0
        break
    try:
        splitted = line.split('=')
        key = splitted[0]
        val = "=".join(splitted[1:])
        args[key] = val
    except Exception, e:
        print line, e
        print "Must be on form 'key=val'"

print args
debug.debug("Ip: %s sysname: %s handler: %s args: %s" % (ip, sysname, handler, args))
checker = checkermap.get(handler)
if not checker:
    debug.debug("No such handler: %s" % handler)
    sys.exit(1)

service={'id':serviceid,
         'netboxid':netboxid,
         'deviceid':0,
         'ip':ip,
         'sysname':sysname,
         'args':args,
         'version':version,
         'deviceid':0
         }

print "Checking"
myChecker = checker(service)
print '  Return value:', myChecker.execute()
print '       Version:', repr(myChecker.getVersion())
print "Finished"
