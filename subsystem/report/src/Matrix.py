import string
from nav import db

connection = db.getConnection('webfront','manage')
database = connection.cursor()

class Matrix:

    def __init__(self, network=None):

        if not network:
            #temporary out of order
            #must be fixed in database
            #database.execute("select netaddr, nettype from prefix inner join vlan using (vlanid) where nettype='scope'")
            #network = database.fetchone()[0]
            network = "129.241.0.0/16"
            
        self.this_net = NetworkAddress(network)
        self.unntak = {}
        self.subnet = {}
        self.big_net_rowspan = {}
        self.numbers = (0,32,64,96,128,160,192,224)
        self.bnet = self.this_net.bnet
        self.start = self.this_net.startnet
        self.end = self.this_net.endnet
        self.network = network

    def makeMatrix(self):

        whole_net = self.this_net
        unntak = self.unntak
        subnet = self.subnet
        big_net_rowspan = self.big_net_rowspan

        sql = "select prefixid, netaddr, vlan, active_ip_cnt, max_ip_cnt, nettype, description, orgid from prefix left outer join vlan using (vlanid) left outer join prefix_active_ip_cnt using (prefixid) left outer join prefix_max_ip_cnt using (prefixid) order by netaddr"
        database.execute(sql)

        prefices = database.fetchall()
        lastnetaddr = "0"

        for prefix in prefices:
            if not prefix[1] == lastnetaddr:
                lastnetaddr = prefix[1]

                small_net = NetworkAddress(lastnetaddr)

                tip = [ int(small_net.net_splitted[i]) & int(whole_net.mask_splitted[i]) for i in range(0,len(small_net.net_splitted))]
                a = string.join([str(t) for t in tip],".")
                #raise repr(a+whole_net.b)
            
                #check that actual netaddr is in the address scope
                if a==whole_net.b and small_net.masklen >= whole_net.masklen:
                    #raise repr(a+whole_net.b)
                    tip[2] = int(small_net.net_splitted[2]) & int(small_net.mask_splitted[2])
                    tip[3] = int(small_net.net_splitted[3]) & int(small_net.mask_splitted[3])
                    if small_net.masklen > 27:
                        unntak[tip[2]] = str(tip[2])

                    else:
                        if not subnet.has_key(tip[2]):
                            subnet[tip[2]] = {}
                        subnet[tip[2]][tip[3]] = Subnet(small_net.net, small_net.masklen, prefix[0], prefix[2], prefix[3], prefix[4], prefix[5], prefix[6], prefix[7])

                        if small_net.masklen < 24:
                            big_net_rowspan[tip[2]] = pow(2,24-small_net.masklen)


class Subnet:

    def __init__(self,ip,masklen,prefixid,vlan,machines,max,nettype,description,orgid):
        self.bits = masklen
        self.vlan = vlan
        self.machines = 0
        if machines:
            self.machines = int(machines)
        self.max = None
        if max:
            self.max = int(max)
        self.ip = ip
        self.prefixid = prefixid
        self.nettype = nettype
        if not description:
            self.description = orgid
        else:
            self.description = description
        self.percent = 0
        if self.machines and self.max:
            self.percent = self.machines*100/self.max

class NetworkAddress:

    def __init__(self,inet_quad):
        splitted = inet_quad.split("/")
        self.net = splitted[0]
        if len(splitted) > 1:
            self.masklen = int(splitted[1])
        else:
            self.masklen = 32

        self.mask = self.bits_mask(self.masklen)

        net_splitted = self.net.split(".")
        mask_splitted = self.mask.split(".")
        
        self.startnet = int(net_splitted[2])
        self.endnet = 255 - int(mask_splitted[2])

        self.b = string.join([str(int(net_splitted[i]) & int(mask_splitted[i])) for i in range (0, len(net_splitted))],".")

        self.net_splitted = net_splitted
        self.mask_splitted = mask_splitted
        
        self.bnet = string.join(net_splitted[0:2], ".")

    def bits_mask(self, number_of_bits):

        if number_of_bits == 32:
            return "255.255.255.255"
        elif number_of_bits == 31:
            return "255.255.255.254"
        elif number_of_bits == 30:
            return "255.255.255.252"
        elif number_of_bits == 29:
            return "255.255.255.248"
        elif number_of_bits == 28:
            return "255.255.255.240"
        elif number_of_bits == 27:
            return "255.255.255.224"
        elif number_of_bits == 26:
            return "255.255.255.192"
        elif number_of_bits == 25:
            return "255.255.255.128"
        elif number_of_bits == 24:
            return "255.255.255.0"
        elif number_of_bits == 23:
            return "255.255.254.0"
        elif number_of_bits == 22:
            return "255.255.252.0"
        elif number_of_bits == 21:
            return "255.255.248.0"
        elif number_of_bits == 20:
            return "255.255.240.0"
        elif number_of_bits == 19:
            return "255.255.224.0"
        elif number_of_bits == 18:
            return "255.255.192.0"
        elif number_of_bits == 17:
            return "255.255.128.0"
        elif number_of_bits == 16:
            return "255.255.0.0"
        elif number_of_bits == 15:
            return "255.254.0.0"
        elif number_of_bits == 14:
            return "255.252.0.0"
        elif number_of_bits == 13:
            return "255.248.0.0"
        elif number_of_bits == 12:
            return "255.240.0.0"
        elif number_of_bits == 11:
            return "255.224.0.0"
        elif number_of_bits == 10:
            return "255.192.0.0"
        elif number_of_bits == 9:
            return "255.128.0.0"
        elif number_of_bits == 8:
            return "255.0.0.0"
        elif number_of_bits == 7:
            return "254.0.0.0"
        elif number_of_bits == 6:
            return "252.0.0.0"
        elif number_of_bits == 5:
            return "248.0.0.0"
        elif number_of_bits == 4:
            return "240.0.0.0"
        elif number_of_bits == 3:
            return "224.0.0.0"
        elif number_of_bits == 2:
            return "196.0.0.0"
        elif number_of_bits == 1:
            return "128.0.0.0"
        elif number_of_bits == 0:
            return "0.0.0.0"
        else:
            raise ValueError(str(number_of_bits)+" is not an accepted value for mask")

