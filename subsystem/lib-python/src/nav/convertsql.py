#!/usr/bin/env python

import re

# lager først snmpoid.sql med:
# pg_dump -a -d -u -f /home/gartmann/snmpoid.sql -t snmpoid manage 

out = file("navsnmpoid.sql","w")
for line in file("snmpoid.sql"):
    if line.startswith("INSERT"):

        name = re.search("\d+\,\ (.*?)\,",line).group(1)
        line = re.sub("\d+\, ","",line)
        line = re.sub("(?:\,\ \w+){4}\)",")",line)
        line = re.sub("INTO snmpoid","INTO snmpoid (oidkey, snmpoid, descr, oidsource)",line)
        out.write("DELETE FROM snmpoid WHERE snmpoidid=%s;\n"%name+line+"\n")
