from IPy import IP
from Matrix import Matrix
from Matrix import contains
from Matrix import database_cursor
from ColorConfiguration import ColorConfiguration

import nav.path
import os
import string
import ConfigParser

configfile = os.path.join(nav.path.sysconfdir,"report/matrix.conf")

class MatrixIpv6(Matrix):

	def __init__(self,start_net,end_net=None):
		Matrix.__init__(self,start_net,end_net=end_net,bits_in_matrix=4)
		self.column_headings = ["%X" % i for i in range(0,16)]

	def getTemplateResponse(self):
		self.template.start_net = self.start_net
		self.template.end_net = self.end_net
		self.template.tree_nets = self.tree_nets
		self.template.matrix_nets = self.matrix_nets
		self.template.column_headings = self.column_headings
		self.template.bits_in_matrix = self.bits_in_matrix
		self.template.color_configuration = ColorConfiguration(configfile)
		return self.template.respond()

	def buildTree(self):
		result = {self.start_net:{}}
		subnets = self.getSubnets(self.start_net)
		mask = self.getMask(self.end_net.prefixlen()-self.bits_in_matrix)
		sorted_subnets = self.sort_nets_by_prefixlength(subnets)

		#append supernodes to the list of sorted subnets. The supernodes
		#should be blocks containing the network shown in the matrix body
		#(i.e. the last rows in the matrix "tree" (to the left))

		#TODO: Reimplement this to respect that the list is allready sorted,
		#	   that way we won't have to sort the list again.
		for ip in sorted_subnets:
			if ip.prefixlen() <= mask.prefixlen():
				continue
			supernet = self.andIpMask(ip,mask)
			if not contains(sorted_subnets,supernet):
				sorted_subnets.append(supernet)

		sorted_subnets = self.sort_nets_by_prefixlength(sorted_subnets)

		#build the tree
		for ip in sorted_subnets:
			self.insertIntoTree(result,ip)

		return result

	def getNybblesMap(self,ip_list):
		"""See Matrix.py for doc"""
		from math import ceil
		start_nybble_index = None
		end_nybble_index = None

		if ip_list[0].prefixlen() < 112:
			start_nybble_index = -2 - int(ceil(float(self.bits_in_matrix)/4))
			end_nybble_index = start_nybble_index + int(ceil(float(self.bits_in_matrix)/4))
		else:
			start_nybble_index = -int(ceil(float(self.bits_in_matrix)/4))
			end_nybble_index = start_nybble_index + int(ceil(float(self.bits_in_matrix)/4))

		return dict(zip([i.net().strCompressed()[start_nybble_index:end_nybble_index] for i in ip_list],ip_list))

	def insertIntoTree(self,tree,ip):
		for ip_item in tree:
			if ip_item.overlaps(ip):
				self.insertIntoTree(tree[ip_item],ip)
				return
		tree[ip] = {}
	
	def andIpMask(self,ip,mask):
		"""Logical AND between ip and mask.

		``ip'': IPy.IP
		``mask'': IPy.IP"""
		ip_split = str(ip.net()).split(":")
		mask_split = str(mask.net()).split(":")
		assert len(ip_split) == len(mask_split) == 8
		supernet = ""
		for i in range(0,len(ip_split)):
			andOp = self.hexAnd(ip_split[i],mask_split[i])
			supernet = ":".join([supernet,andOp])
		return IP("/".join([supernet[1:],str(mask.prefixlen())]))
	
	def hexAnd(self, hex1, hex2):
		"""Logic AND for two hex number.

		``hex1'', ``hex2'': hexadecimal numbers. Must be strings, function
			accepts both "0xFE" and "FE"."""
		dec1 = int(hex1,16)
		dec2 = int(hex2,16)
		result = dec1 & dec2
		return "%x" % result
	
	def getMask(self, masklength):
		"""Generates an IPv6 mask with prefix length equal to argument
		``masklength''."""
		result = None
		mask_array = ['f' for i in range(0,masklength/4)]
		mask_string = "".join(mask_array)
		last_nybble = masklength % 4

		if last_nybble:
			last_nybble_dec = sum([2**(4-i) for i in range(1,last_nybble+1)])
			mask_string = "".join([mask_string,"%x" % last_nybble_dec])

		result = [mask_string[4*i:4+4*i] for i in range(0,int(float(masklength)/16+0.5))]
		if len(result[-1]) < 4:
			for i in range(0,4-len(result[-1])):
				result[-1] = "".join([result[-1],"0"])
		result = ":".join(result)

		if masklength < 112:
			result = "".join([result,"::"])
		return IP("/".join([result,str(masklength)]))

