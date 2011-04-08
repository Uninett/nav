# -*- coding: ISO8859-1 -*-
"""
core - kjøre jobber som prosesser i stedet for tråder

$Author$
$Id$
$Source: /usr/local/cvs/navbak/navme/subsystem/statemon/lib/core.py,v $

tanken er at programmet skal lese argumenter fra stdin
starte jobbene som egne prosesser som skriver resultat til stdout

eks stdin:
(serviceid,boksid,ip,type,version,{property:value})

eks stdout:
(serviceid,boksid,status,info,version,responsetid)
"""

import os, sys, time, signal
from job import jobmap, Event


MAX = 10
TIMEOUT = 5

class Timeout(Exception):
    pass

def handler(s, f):
    raise Timeout('timeout')

def do(serviceid, boksid, ip, type, version, args):
    start = time.time()
    j = jobmap[type](serviceid, boksid, ip, args, version)
    status, info = j.execute()
    version = j.getVersion()
    return (serviceid, status, info, version, time.time() - start)

def core(childs = MAX):
    signal.signal(signal.SIGALRM, handler)
    for child in range(childs):
        pid = os.fork()
        if not pid:
            while 2:
                try:
                    s = raw_input()
                    if not s:
                        sys.exit(0)
                    serviceid, boksid, ip, type, version, args = eval(s)
                    timeout = args.get('timeout', TIMEOUT)
                    signal.alarm(timeout)
                    print do(serviceid, boksid, ip, type, version, args)
                    signal.alarm(0)
                except Timeout, info:
                    print (serviceid, Event.DOWN, 'timeout', 0)
                except SystemExit:
                    raise

    try:
        for i in range(childs):
            os.wait()
    except:
        #logge til syslog elns
        pass

if __name__ == '__main__':
    if len(sys.argv) == 2:
        childs = int(sys.argv[1])
        core(childs)
    else:
        core()
