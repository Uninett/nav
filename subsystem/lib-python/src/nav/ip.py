"""
$Id$

This file is part of the NAV project.

Provides common IP (Internet Protocol) functionality for NAV.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
import re, struct
import socket

_cidrPattern = re.compile('^([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)(/([0-9]+))?')

def ptoi(ip):
    """
    Return a 32 bit integer (actually long) value from a 32 bit ip
    adressed in packed format (4 byte string).  Packed format is
    converted from network byte order to host byte order first.
    """
    if type(ip) is str:
        if len(ip) == 4:
            return socket.ntohl(struct.unpack('i', ip)[0])
        else:
            raise ValueError, 'Expected 4 character string, found only %s' % len(ip)
    else:
        raise TypeError, "Argument must be 'str', not '%s'" % type(ip).__name__

def itop(addr):
    """
    The exact opposite of the ip2int function
    """
    if type(addr) in [int, long]:
        return struct.pack('i', socket.htonl(addr))
    else:
        raise TypeError, "Argument must be 'int' or 'long', not '%s'" % type(addr).__name__

def dtoi(ipstring):
    """
    Convert a decimal dotted IP address string into its integer
    representation (host byte order)
    """
    if type(ipstring) is str:
        try:
            packed = socket.inet_aton(ipstring)
        except socket.error, e:
            # For some reason, inet_aton barfs at this broadcast
            # address, so we make a special test out of this.
            if ipstring == "255.255.255.255":
                packed = "\xff\xff\xff\xff"
            else: raise e
        ip = socket.ntohl(struct.unpack('i', packed)[0])
        return ip
    else:
        raise TypeError, "Argument must be 'str', not '%s'" % type(ip).__name__

def itod(ip):
    """
    Convert a IP address represented by a (host byte order) integer
    value into decimal dotted string format.
    """
    if type(ip) is int:
        packed = struct.pack('i', socket.htonl(ip))
        ipstring = socket.inet_ntoa(packed)
        return ipstring
    else:
        raise TypeError, "Argument must be 'int', not '%s'" % type(ip).__name__
    

class IPv4:
    """This class represents an IPv4 address and/or subnet.

    Examples:
      ip = IPv4('129.241.75.1')
      net = IPv4('129.241.75.1/24')
      fullnet = IPv4('129.241.0.0', '255.255.0.0')

    To check whether an IP address or subnet is contained within
    another, you can use the following:

      if ip in net:
          print "%s is in %s" % (ip, net)

    Other useful things:

      net[0]  - returns the net address of this net.
      net[-1] - returns the broadcast address of this net.
      net[n]  - return the ip address of host number n in this net.
    """
    def __init__(self, address, mask=None):
        address = address.strip()
        matches = _cidrPattern.match(address)

        fullmask = 0xFFFFFFFF

        if matches:
            g = matches.groups()
            try:
                self.address = dtoi(g[0])
            except:
                raise "Illegal IP address string %s" % g[0]
            
            if g[1] is None:
                # We consider the mask parameter only if no mask
                # length was given in the address string.
                if mask is None:
                    self.maskbits = 32
                    self.mask = fullmask
                else:
                    maskInt = dtoi(mask)
                    # How far do we need to left-shift the full mask
                    # before it equals the given bit mask?
                    for xbits in range(0,32):
                        if fullmask << xbits == maskInt:
                            self.maskbits = 32-xbits
                            break
                    # If this loop never set the maskbits attribute,
                    # it means the subnet mask was invalid.
                    if not hasattr(self, 'maskbits'):
                        raise ValueError, "%s is an invalid subnet mask" % repr(mask)
            else:
                self.maskbits = int(g[2])
                if self.maskbits > 32:
                    raise ValueError, "There is no such thing as a %d bit subnet mask in IPv4" % self.maskbits
                self.mask = fullmask << (32 - self.maskbits)
        else:
            raise ValueError, "%s is an illegal IP or CIDR string" % repr(address)
                
    def __str__(self):
        if self.maskbits < 32:
            maskpart = "/%d" % self.maskbits
        else:
            maskpart = ""
        return "%s%s" % (itod(self.address), maskpart)

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__, str(self))

    def __getattr__(self, name):
        """Intelligent retrieval of some attributes (which are
        calculated on the fly)."""
        if name == 'network' and self.maskbits < 32:
            return self._getNet()
        elif name == 'host' and self.maskbits < 32:
            return self._getHost()
        else:
            raise AttributeError, "'%s' object has no attribute '%s'" % (self.__class__.__name__, name)

    def __len__(self):
        hostbits = 32 - self.maskbits
        return 2 ** hostbits

    def __cmp__(self, other):
        return cmp(self.address, other.address)

    def __hex__(self):
        return hex(self.address)
    
    def __getitem__(self, index):
        if type(index) is not int:
            raise TypeError, "sequence index must be integer"
        if index >= len(self):
            raise IndexError, "list index out of range"

        if hasattr(self, 'network'):
            host = self.network
            host |= index
        else:
            host = self.address
            
        ipstring = itod(host)
        return IPv4(ipstring)

    def __contains__(self, item):
        """Checks whether item (an IPv4 instance) is contained within
        the subnet this instance represents"""
        if item.__class__ is IPv4:
            if item.maskbits >= self.maskbits:
                itemMasked = item.address & self.mask
                selfMasked = self.address & self.mask
                return (itemMasked == selfMasked)
            else:
                return False
        else:
            # item cannot be compared in any way to an IPv4 instance.
            return False

    def _getNet(self):
        """Return the net address, host part masked out."""
        net = self.address & self.mask
        return net

    def _getHost(self):
        """Return the host address, net part masked out."""
        host = self.address & ~self.mask
        return host
