import sys, os
sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib")
sys.path.append(os.path.split(os.path.realpath(os.sys.argv[0]))[0]+"/lib/handler")
import debug
import job
import getopt
import jobmap

myDebug = debug.debug(level=7)

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
for opt, val in opts:
    if opt in ("-i", "--help"):
        ip = val
    elif opt in ("-s", "--sysname"):
        sysname = val
    elif opt in ("-h", "--handler"):
        handler = val
    elif opt in ("-a", "--args"):
        try:
            args = eval(val)
        except:
            print "%s is not a dict" % val

myDebug.log("Ip: %s sysname: %s handler: %s args: %s" % (ip, sysname, handler, args))
mapper = jobmap.jobmap()
job = mapper.get(handler)
if not job:
    myDebug.log("No such handler: %s" % handler)
    sys.exit(1)

service={'id':serviceid,
         'netboxid':netboxid,
         'ip':ip,
         'sysname':sysname,
         'args':args,
         'version':version
         }
    
myJob = job(service)
myJob.run()
