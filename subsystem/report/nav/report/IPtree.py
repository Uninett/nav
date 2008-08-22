# -*- coding: utf-8 -*-
# $Id:$
#
# Copyright 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Authors: Jostein Gogstad <jostein.gogstad@idi.ntnu.no>
#          Jørgen Abrahamsen <jorgen.abrahamsen@uninett.no>
#

from IPy import IP
from copy import deepcopy
from nav import db
from nav.report.IPtools import getMask,sort_nets_by_prefixlength,andIpMask

db_cursor = db.getConnection('webfront','manage').cursor()

tree = None

def buildTree(start_net, end_net=None, bits_in_matrix=0, add_missing_nets=False, forceBuild=False):
	"""Builds a tree from start_net to (and included) end_net.

	Arguments:
		start_net: IPy.IP instance of the starting point
		forceBuild: Force tree build instead of using cached result

	Returns: A tree (using a hash map)

	This module was originally implemented for the prefix matrix which
	needed three additional options:
		end_net: The last net to be shown in the matrix
		bits_in_matrix: Number of bits to exclude from the end_net IP,
			defaults to 0
		add_missing_nets: If a leaf nodes' parent does not have prefix
			length == (end_net - bits_in_matrix) such a parent will be added
			in between the leaf and the original parent. The extra parent
			will serve as a 'foreign key' later on when the prefix matrix
			splits the tree on all nodes with prefix length =
			end_net.prefixlen() - bits_in_matrix.

			defaults to False
	"""

	result = {start_net:{}}
	subnets = getSubnets(start_net)
	sorted_subnets = sort_nets_by_prefixlength(subnets)

	#TODO: Reimplement this to respect that the list is allready sorted,
	#	   that way we won't have to sort the list again.
	if add_missing_nets and bits_in_matrix > 0:
		mask = getMask(start_net.version(),end_net.prefixlen()-bits_in_matrix)
		for ip in sorted_subnets:
			if ip.prefixlen() <= mask.prefixlen():
				continue
			supernet = andIpMask(ip,mask)
			if supernet not in sorted_subnets:
				sorted_subnets.append(supernet)

		sorted_subnets = sort_nets_by_prefixlength(sorted_subnets)

	#build the tree
	for ip in sorted_subnets:
		insertIntoTree(result,ip)

	return result

def insertIntoTree(tree,ip):
	for ip_item in tree:
		if ip_item.overlaps(ip):
			insertIntoTree(tree[ip_item],ip)
			return
	tree[ip] = {}

def getSubnets(network, min_length=None, max_length=128):
	"""Retrieves all the subnets of the argument ``network''.

	Arguments:
		``min_length'': minimum subnet mask length, defaults to network.prefixlen().
		``max_length'': maximum subnet mask length, defaults to 128.

	Returns:
		List with IPy.IP objects
	"""

	if min_length is None:
		min_length = network.prefixlen()
	assert min_length < max_length
	sql = "SELECT netaddr FROM prefix WHERE family(netaddr)=%d AND netaddr << '%s' AND masklen(netaddr) >= %d AND masklen(netaddr) < %d" \
			% (network.version(),str(network),min_length,max_length)
	db_cursor.execute(sql)
	db_result = db_cursor.fetchall()
	return [IP(i[0]) for i in db_result]

def removeSubnetsWithPrefixLength(tree, prefixlen):
	"""Generates a new tree from tree, but without subnets with
	prefix length >= prefixlen."""

	def deleteSubnets(tree,limit):
		oldTree = deepcopy(tree)
		for ip in oldTree.keys():
			if ip.prefixlen() >= limit:
				del tree[ip]
		for ip in tree.keys():
			deleteSubnets(tree[ip],limit)
	treeNets = deepcopy(tree)
	deleteSubnets(treeNets,prefixlen)
	return treeNets

def getSubtree(tree,ip):
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
	return searchTree(tree,ip)

def search(tree,ip):
	tree = getSubtree(tree,ip)
	if tree is None:
		return False
	else:
		return True

def isLeafNode(node):
	if len(node.keys()) == 0:
		return True
	else:
		return False

def getMaxLeaf(tree,maximum_prefix_length=128):
	"""Returns the leaf node with highest prefix length.
	If several found; returns the first hit."""

	def dfs(tree,max):
		for node in tree.keys():
			if isLeafNode(tree[node]):
				if node.prefixlen() > max.prefixlen() and node.prefixlen() <= maximum_prefix_length:
					max = node
			else:
				result = dfs(tree[node],max)
				if result.prefixlen() > max.prefixlen() and result.prefixlen() <= maximum_prefix_length:
					max = result
		return max

	root = tree.keys()[0]
	return dfs(tree,root)

def printTree(tree, depth=0):
	def printT(tree,depth):
		for net in tree:
			print 3*depth*" " + str(net)
			printT(tree[net],depth+1)
	printT(tree,depth)

def extractSubtreesWithPrefixLength(tree,prefixlen):
	"""Returns a map of subtrees with length prefixlen. Generated from
	tree"""
	keys = extractSubnetsWithPrefixLength(tree,prefixlen)
	map = {}
	for key in keys:
		map[key] = getSubtree(tree,key)
	return map

def extractSubnetsWithPrefixLength(tree,prefixlen):
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
	Iterator(tree,prefixlen,acc)
	return acc
