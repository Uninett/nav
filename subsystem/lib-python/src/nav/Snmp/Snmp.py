#!/usr/bin/env python

import re

from pysnmp.proto import v1
from pysnmp.proto.api import generic
from pysnmp.mapping.udp import role

class Snmp:
    """
    Simple class that provides snmpget, snmpwalk and snmpjog(tm) functionality.
    Snmpget returns the result as one string.
    Snmpwalk returns the subtree as an array containing OID, value-pairs.
    Snmpjog returns the result as snmpwalk does, the difference is that snmpjog chops off (each line) the OID-prefix used in the query.
    """


    def __init__(self,host,community="public",port=161):
        """
        Makes a new Snmp-object.
        host: hostname
        community: community (password), defaults to "public"
        port: port, defaults to "161"
        """
        
        self.host = host
        self.community = community
        self.port = int(port)

        self.handle = role.manager((host,port))


    def get(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpget query on the host.
        query: OID to use in the query

        returns the result as a string.
        """

        req = v1.GetNextRequest()
        req.apiGenSetCommunity(self.community)
        req.apiGetPdu().apiSetVarBind([(query, None)])
        (answer, src) = self.handle.send_and_receive(req.encode())
        rsp = v1.GetResponse()
        rsp.decode(answer)
        vars = rsp.apiGetPdu().apiGetVarBind()

        return vars[0][1].get()

    def walk(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpwalk on the host.
        query: OID to use in the query

        returns an array containing key-value-pairs, where the returned OID is the key.
        """
        
        result = []
        mib = query

        stop = 0
        
        while stop == 0:

            req = v1.GetNextRequest()
            req.apiGenSetCommunity(self.community)
            req.apiGetPdu().apiSetVarBind([(mib, None)])
            (answer, src) = self.handle.send_and_receive(req.encode())
            rsp = v1.GetResponse()
            rsp.decode(answer)
            vars = rsp.apiGetPdu().apiGetVarBind()

            (mib,value) = vars[0]
            found = re.search(query,mib)

            if found:
                result.append((mib,value.get()))
            else:
                stop = 1
                
        return result
    
    def jog(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does a modified snmpwalk on the host. The query OID is chopped off the returned OID for each line in the result.
        query: OID to use in the query

        returns an array containing key-value-pairs, where the key is the returned OID minus the OID in the query, i.e query: 1.2.3, snmpwalk returned oid:1.2.3.4.5, snmpjog returned key: 4.5
        """
        result = []
        mib = query

        stop = 0
        
        while stop == 0:

            req = v1.GetNextRequest()
            req.apiGenSetCommunity(self.community)
            req.apiGetPdu().apiSetVarBind([(mib, None)])
            (answer, src) = self.handle.send_and_receive(req.encode())
            rsp = v1.GetResponse()
            rsp.decode(answer)
            vars = rsp.apiGetPdu().apiGetVarBind()

            (mib,value) = vars[0]

            found = re.search(query,mib)
            key = re.sub('.'+query+'.','',mib)

            if found:
                result.append((key,value.get()))
            else:
                stop = 1
                
        return result
