from IPy import IP
from nav import db
from copy import deepcopy
from DBUtils import ResultSetIterator

from __future__ import nested_scopes

connection = db.getConnection('webfront','manage')
database_cursor = connection.cursor()

#TODO:	Extract the tree utilities to an own module
#			getSubnets needs in that case to be reimplemented to take arbitrary sql
#			for subnet extraction.
#
#		Standardize documentation style.

class Matrix:

	def __init__(self, start_net, end_net=None, bits_in_matrix=3):
		if end_net is None:
			end_net = self.getLastSubnet(start_net)
		self.start_net = start_net
		self.end_net = end_net
		self.prefix_map = None #maps netaddrs to prefices
		self.bits_in_matrix = bits_in_matrix
		self.tree = self.buildTree()
		self.tree_nets = self.extractTreeNets()
		self.matrix_nets = self.extractMatrixNets()
		self.max_diff_before_dots = 6
	
	def getTemplateResponse(self):
		abstract()

	def buildTree(self):
		"""Builds a tree of subnets.

		Note: method getSubnets might be usefull."""
		abstract()
	
	def has_too_small_nets(self,net):
		for net in self.getSubtree(net):
			if net.prefixlen() > self.end_net.prefixlen():
				return True
		return False

	def extractMatrixNets(self):
		"""These should be shown as horizontal rows in the matrix."""

		return self.extractSubtreesWithPrefixLength(self.end_net.prefixlen()-self.bits_in_matrix)

	def extractTreeNets(self):
		"""These should be listed vertically in the leftmost column.""" 

		return self.removeSubnetsWithPrefixLength(self.end_net.prefixlen()-self.bits_in_matrix+1)

	def removeSubnetsWithPrefixLength(self, prefixlen):
		"""Generates a new tree from self.tree, but without subnets with
		prefix length >= prefixlen."""
	
		def deleteSubnets(tree,limit):
			oldTree = deepcopy(tree)
			for ip in oldTree.keys():
				if ip.prefixlen() >= limit:
					del tree[ip]
			for ip in tree.keys():
				deleteSubnets(tree[ip],limit)
		treeNets = deepcopy(self.tree)
		deleteSubnets(treeNets,prefixlen)
		return treeNets

	def getSubtree(self,ip):
		"""Returns the subtree identified by the arguments ``ip''.
		None if not found."""

		def searchTree(tree,goal):
			"""DFS in tree for goal."""
			for node in tree.keys():
				if node == goal:
					return tree[node]
				else:
					result = searchTree(tree[node],goal)
					if result is not None:
						return result
		return searchTree(self.tree,ip)

	def printTree(self, depth=0):
		def printT(tree,depth):
			for net in tree:
				print 3*depth*" " + str(net)
				printT(tree[net],depth+1)
		printT(self.tree,depth)


	def sort_nets_by_prefixlength(self,nets):
		"""Sorts a list with IP instances."""
		decorate = [(net.prefixlen(),net) for net in nets]
		decorate.sort()
		result = [i[-1] for i in decorate]
		return result

	def sort_nets_by_address(self,nets):
		"""Sorts a list with IP instances."""
		abstract()
	
	def net_diff(self,net1,net2):
		assert net1.prefixlen()==net2.prefixlen()
		if net1 > net2:
			(net1,net2) = (net2,net1)
		return [IP("/".join([str(net),str(net1.prefixlen())])) for net in range(net1.int(), net2.int(), 256)]

	def extractSubtreesWithPrefixLength(self,prefixlen):
		"""Returns a map of subtrees with length prefixlen. Generated from
		self.tree"""
		keys = self.extractSubnetsWithPrefixLength(prefixlen)
		map = {}
		for key in keys:
			map[key] = self.getSubtree(key)
		return map

	def extractSubnetsWithPrefixLength(self,prefixlen):
		"""Returns a list of subtrees with length prefix lehgth.

		Note: Use extractSubtreesWithPrefixLength if you want the trees
			and not the IPs."""

		def Iterator(tree, prefixlen, acc):
			for net in tree.keys():
				if net.prefixlen() == prefixlen:
					acc.append(net)
				if net.prefixlen() < prefixlen:
					Iterator(tree[net],prefixlen,acc)
		acc = []
		Iterator(self.tree,prefixlen,acc)
		return acc

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
		"""Retrieves all the subnets of the argument ``network''.

		Arguments:
			``min_length'': minimum subnet mask length, defaults to network.prefixlen().
			``max_length'': maximum subnet mask length, defaults to 128.

		Returns:
			DBUtils.ResulSetIterator
		"""

		if min_length is None:
			min_length = network.prefixlen()
		assert min_length < max_length
		sql = "SELECT prefix,netaddr FROM prefix WHERE family(netaddr)=%d AND netaddr << '%s' AND masklen(netaddr) >= %d AND masklen(netaddr) < %d" \
				% (network.version(),str(network),min_length,max_length)
		database_cursor.execute(sql)
		db_result = database_cursor.fetchall()
		prefix_list = [i[0] for i in db_result]
		netaddr_list = [IP(i[1]) for i in db_result]
		self.prefix_map.update(zip(netaddr_list,prefix_list))
		return netaddr_list

	def getCursor(self):
		return database_cursor

#because I'm a Java guy
def abstract():
	import inspect
	caller = inspect.getouterframes(inspect.currentframe())[1][3]
	raise NotImplementedError(" ".join([caller,"must be implemented in subclass"]))
