#!/usr/bin/env python

import re,pysnmp,exceptions
from pysnmp.proto import v1, v2c
from pysnmp.proto.api import generic
from pysnmp.mapping.udp import role
import pysnmp.proto.cli.ucd
#from pysnmp.asn1.univ import Null
#import types

class TimeOutException(exceptions.Exception):
    """Base class for PySNMP error handlers
    """
    def __init__(self, err_msg=None):
        """
        """
        exceptions.Exception.__init__(self)

        if err_msg is not None:
            self.err_msg = str(err_msg)
        else:
            self.err_msg = ''

    def __str__(self):
        """
        """
        return self.err_msg

    def __repr__(self):
        """
        """
        return self.__class__.__name__ + '(' + self.err_msg + ')'
    
class NameResolverException(exceptions.Exception):
    """Base class for PySNMP error handlers
    """
    def __init__(self, err_msg=None):
        """
        """
        exceptions.Exception.__init__(self)

        if err_msg is not None:
            self.err_msg = str(err_msg)
        else:
            self.err_msg = ''

    def __str__(self):
        """
        """
        return self.err_msg

    def __repr__(self):
        """
        """
        return self.__class__.__name__ + '(' + self.err_msg + ')'
    

class Snmp:
    """
    Simple class that provides snmpget, snmpwalk and snmpjog(tm) functionality.
    Snmpget returns the result as one string.
    Snmpwalk returns the subtree as an array containing OID, value-pairs.
    Snmpjog returns the result as snmpwalk does, the difference is that snmpjog chops off (each line) the OID-prefix used in the query.
    """


    def __init__(self,host,community="public",version="1",port=161,retries=3,timeout=1,reporttype=None):
        """
        Makes a new Snmp-object.
        host: hostname
        community: community (password), defaults to "public"
        port: port, defaults to "161"
        """
        
        self.host = host
        self.community = community
        self.version = str(version)
        self.port = int(port)
        self.retries = retries
        self.timeout = timeout
        self.reporttype = reporttype

        self.handle = role.manager((host,port))


    def get(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpget query on the host.
        query: OID to use in the query

        returns the result as a string.
        """

        if not query.startswith("."):
            query = "." + query

        # Choose protocol version specific module
        try:
            snmp = eval('v' + self.version)
        except (NameError, AttributeError):
            print 'Unsupported SNMP protocol version: %s' % (self.version)
            #sys.exit(-1)
            return

        args = [ self.host, self.community, query]

        # Create SNMP GET request
        req = snmp.GetRequest()

        # Initialize request message from C/L params
        req.cliUcdSetArgs(args[1:])

        # Create SNMP response message framework
        rsp = snmp.Response()

        result = []

        def cb_fun(answer, src):
            """This is meant to verify inbound messages against out-of-order
               messages
            """
            # Decode message
            rsp.decode(answer)

            # Make sure response matches request
            if req.match(rsp):
                return 1

        # Encode SNMP request message and try to send it to SNMP agent and
        # receive a response

        weiter = 0
        try:
            (answer, src) = self.handle.send_and_receive(req.encode(), (None, 0), cb_fun)
            weiter = 1
        except pysnmp.mapping.udp.error.NoResponseError, e:
            #timeout
            raise TimeOutException(e)
        except pysnmp.mapping.udp.error.NetworkError, n:
            #dns
            raise NameResolverException(n)

        if weiter:

            # Fetch Object ID's and associated values
            vars = rsp.apiGenGetPdu().apiGenGetVarBind()

            # Check for remote SNMP agent failure
            if rsp.apiGenGetPdu().apiGenGetErrorStatus():
                raise str(rsp['pdu'].values()[0]['error_status']) + ' at '\
                      + str(vars[rsp.apiGenGetPdu().apiGenGetErrorIndex()-1][0])

            # Print out results
            #for (oid, val) in vars:
            try:
                value = vars[0][1].get()
            except TypeError:
                # stygg hack, skulle da strengt tatt ikke være nødvendig å be om typen til objektet. Skulle holdt å kalle get en gang uten parametre. Da hadde man også sluppet try-except
                value = vars[0][1].get('internet').get()

            return value

        else:
            return

    
    def walk(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpwalk on the host.
        query: OID to use in the query

        returns an array containing key-value-pairs, where the returned OID is the key.
        """

        if not query.startswith("."):
            query = "." + query
        result = []
        
        try:
            snmp = eval('v' + self.version)

        except (NameError, AttributeError):
            print 'Unsupported SNMP protocol version: %s' % (self.version)
            #sys.exit(-1)
        # Create SNMP GET/GETNEXT request
        req = snmp.GetRequest(); nextReq = snmp.GetNextRequest()

        #s
        args = [ self.host, self.community, query]
        #args = ['',self.host,self.community,query,self.port,self.retries,self.timeout,self.version, self.reporttype]

        # Initialize request message from C/L params
        req.cliUcdSetArgs(args[1:]); nextReq.cliUcdSetArgs(args[1:])

        # Create a response message framework
        rsp = snmp.Response()

        # Store tables headers
        headVars = map(lambda x: x[0], req.apiGenGetPdu().apiGenGetVarBind())

        # Traverse agent MIB
        while 1:
            def cb_fun(answer, src):
                """This is meant to verify inbound messages against out-of-order
                   messages
                """
                # Decode message
                rsp.decode(answer)

                # Make sure response matches request
                if req.match(rsp):
                    return 1

            # Encode SNMP request message and try to send it to SNMP agent and
            # receive a response
            try:
                (answer, src) = self.handle.send_and_receive(req.encode(), (None, 0), cb_fun)
            except pysnmp.mapping.udp.error.NoResponseError, e:
                raise TimeOutException(e)
            except pysnmp.mapping.udp.error.NetworkError, n:
                raise NameResolverException(n)


            # Fetch Object ID's and associated values
            vars = rsp.apiGenGetPdu().apiGenGetVarBind()

            # Check for remote SNMP agent failure
            if rsp.apiGenGetPdu().apiGenGetErrorStatus():
                # SNMP agent reports 'no such name' when walk is over
                if rsp.apiGenGetPdu().apiGenGetErrorStatus() == 2:
                    # Switch over to GETNEXT req on error
                    # XXX what if one of multiple vars fails?
                    if not (req is nextReq):
                        req = nextReq
                        continue
                    # One of the tables exceeded
                    for l in vars, headVars:
                        del l[rsp['pdu'].values()[0]['error_index'].get()-1]
                    if not vars:
                        print "feilet"
                        #sys.exit(0)
                        break
                else:
                    raise str(rsp['pdu'].values()[0]['error_status']) + ' at '\
                          + str(vars[rsp.apiGenGetPdu().apiGenGetErrorIndex()-1][0])

            # Exclude completed var-binds
            while 1:
                for idx in range(len(headVars)):
                    if not snmp.ObjectIdentifier(headVars[idx]).isaprefix(vars[idx][0]):
                        # One of the tables exceeded
                        for l in vars, headVars:
                            del l[idx]
                        break
                else:
                    break

            if not headVars:
                return result
                #sys.exit(0)

            # Print out results
            for (oid, val) in vars:
                try:
                    value = val.get()
                except TypeError:
                    # stygg hack, skulle da strengt tatt ikke være nødvendig å be om typen til objektet. Skulle holdt å kalle get en gang uten parametre. Da hadde man også sluppet try-except
                    value = val.get('internet').get()
                result.append((oid,value))

            # Update request ID
            req.apiGenGetPdu().apiGenSetRequestId(req.apiGenGetPdu().apiGenGetRequestId()+1)

            # Switch over GETNEXT PDU for if not done
            if not (req is nextReq):
                req = nextReq

            # Load get-next'ed vars into new req
            req.apiGenGetPdu().apiGenSetVarBind(vars)

    
    def jog(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does a modified snmpwalk on the host. The query OID is chopped off the returned OID for each line in the result.
        query: OID to use in the query

        returns an array containing key-value-pairs, where the key is the returned OID minus the OID in the query, i.e query: 1.2.3, snmpwalk returned oid:1.2.3.4.5, snmpjog returned key: 4.5
        """
        walked = self.walk(query)
        result = []
        if walked:
            for oid,value in walked:
                #found = re.search(query,oid)
                key = re.sub('\.?' + query + '\.?','',oid)
                result.append((key,value))
        
        return result
