import mibretriever
import nav.bitvector

class QBridgeMib(mibretriever.MibRetriever):
    from nav.smidumps.qbridge_mib import MIB as mib

class PortList(str):
    """Represent an octet string, as defined by the PortList syntax of
    the Q-BRIDGE-MIB.

    Offers conveniences such as subtracting one PortList from another,
    and retrieving a list of port numbers represented by a PortList
    octet string.

    """

    def __sub__(self, other):
        new_ints = [ord(char) - ord(other[index]) 
                    for index, char in enumerate(self)]
        return PortList(''.join(chr(i) for i in new_ints))
    
    def get_ports(self):
        """Return a list of port numbers represented by this PortList."""
        vector = nav.bitvector.BitVector(self)
        ports = []
        for i in range(len(vector)):
            if vector[i]:
                # bitvector is indexed from 0, but ports are indexed from 1
                ports.append(i+1)
        return ports
