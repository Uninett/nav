from IPy import IP
from nav import db
from copy import deepcopy
from DBUtils import ResultSetIterator

from __future__ import nested_scopes

connection = db.getConnection('webfront','manage')
database_cursor = connection.cursor()

class Matrix:

	def __init__(self, start_net, end_net=None, bits_in_matrix=3):
		if end_net is None:
			end_net = self.getLastSubnet(start_net)
		self.start_net = start_net
		self.end_net = end_net
		self.bits_in_matrix = bits_in_matrix
		self.tree = self.buildTree()
	
	def getTemplateResponse(self):
		abstract()

	def extractMatrixNets(self):
		return extractSubnetsWithPrefixLength(end_net.prefixlen()-bits_in_matrix)

	def extractSubnetsWithPrefixLength(self,prefixlen):
		def Iterator(tree, prefixlen, acc):
			for net in tree:
				if net.prefixlen() == prefixlen:
					acc.append(net)
				if net.prefixlen() > prefixlen:
					Iterator(tree[net],prefixlen,acc)
		acc = []
		Iterator(self.tree,prefixlen,acc)
		return acc

	def extractTreeNets(self):
		def deleteSubnets(tree,limit):
			oldTree = deepcopy(tree)
			for ip in oldTree:
				if ip.prefixlen() >= limit:
					del tree[ip]
			for ip in tree:
				deleteSubnets(tree[ip],limit)
		treeNets = deepcopy(self.tree)
		deleteSubnets(treeNets,self.end_net.prefixlen()-self.bits_in_matrix+1)
		return treeNets

	def containsIp(self,ip,tree=None):
		"""Returns true if tree contains ip."""
		if tree is None:
			tree = self.tree
		for net in tree:
			if net == ip:
				return ip
			return self.containsIp(ip,tree[net])

	def buildTree(self):
		abstract()

	def sort_nets(self,nets):
		decorate = [(net.prefixlen(),net) for net in nets]
		decorate.sort()
		result = [i[-1] for i in decorate]
		return result

	def getLastSubnet(self, network, last_network_prefix_len=None):
		""" Retrieves the last _possible_ subnet of the argument ``network''.
			Does not care whether the subnet exists or not.

			Arguments:
				``network'': The network in question
				``last_network_prefix_len'': An optional specification of the prefix length
											 of the last network. Defaults to 32 for IPv6
											 and 128 for IPv6
		"""
		if last_network_prefix_len is None:
			last_network_prefix_len = network.netmask().prefixlen()
		return IP(''.join([network.net().strNormal(),"/",str(last_network_prefix_len)]))

	def getSubnets(self,network, min_length=None, max_length=128):
		"""Retrieves all the subnets of network

		Arguments:
			``min_length'': minimum subnet mask length, defaults to network.prefixlen().
			``max_length'': maximum subnet mask length, defaults to 128.

		Returns:
			DBUtils.ResulSetIterator
		"""

		if min_length is None:
			min_length = network.prefixlen()
		assert min_length < max_length
		sql = "SELECT netaddr FROM prefix WHERE family(netaddr)=%d AND netaddr << '%s' AND masklen(netaddr) >= %d AND masklen(netaddr) < %d" \
				% (network.version(),str(network),min_length,max_length)
		database_cursor.execute(sql)
		return [IP(i[0]) for i in database_cursor.fetchall()]

	def getSubnetsInRange(self, from_network, to_network):
		assert to_network.prefixlen() > from_network.prefixlen()
		return getSubnets(from_network,max_length=to_network.prefixlen())

	def getNearestSubnets(self, network):
		"""Retrieves the subnets of network with the lowest netmask (ie. the "nearest")"""

		sql = """SELECT netaddr FROM prefix p WHERE family(p.netaddr)=%d AND p.netaddr << '%s' AND 1 =
					(SELECT count(*) FROM prefix p2 WHERE family(p2.netaddr)=family(p.netaddr) AND p.netaddr << p2.netaddr
					AND p2.netaddr <<= '%s')""" \
				% (network.version(),str(network),str(network))
		database_cursor.execute(sql)
		return ResultSetIterator(database_cursor)
			
	def getCursor(self):
		return database_cursor

#because I'm a Java guy
def abstract():
	import inspect
	caller = inspect.getouterframes(inspect.currentframe())[1][3]
	raise NotImplementedException(" ".join(caller,"must be implemented in subclass"))
