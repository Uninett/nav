from DBUtils import ResultSetIterator
from IPy import IP
from nav.web.templates.MatrixTemplate import MatrixTemplate
from Matrix import Matrix

from __future__ import nested_scopes

#TODO: Fininsh getTemplateResponse

class MatrixIpv4(Matrix):
	
	def __init__(self,start_net,end_net=None):
		Matrix.__init__(self,start_net,end_net)
		self.column_headings = self._getColumnHeaders()

	def getTemplateResponse(self):
		template = MatrixTemplate()
		template.network = self.start_net
		template.headings = self.column_headings

	def _getColumnHeaders(self):
		msb = 8 - (self.end_net.prefixlen()-self.bits_in_matrix) % 8
		lsb = msb - self.bits_in_matrix
		if lsb <= 0:
			lsb = 1
		if msb <= 0:
			msb = 1
		return [(2**lsb)*i for i in range(0,msb)]

	def buildTree(self):
		result = {self.start_net:{}}
		subnets = self.getSubnets(self.start_net)
		mask = self.getMask(self.end_net.prefixlen()-self.bits_in_matrix)
		sorted_subnets = self.sort_nets(subnets)
		for ip in sorted_subnets:
			if ip.prefixlen() <= mask.prefixlen():
				continue
			supernet = self.andIpMask(ip,mask)
			if not contains(sorted_subnets,supernet):
				sorted_subnets.append(supernet)
				 
		sorted_subnets = self.sort_nets(sorted_subnets)
		
		for ip in sorted_subnets:
			self._insertIntoTree(result,ip)

		return result

	def _insertIntoTree(self,tree,ip):
		for ip_item in tree:
			if ip_item.overlaps(ip):
				self._insertIntoTree(tree[ip_item],ip)
				return
		tree[ip] = {}
	
	def andIpMask(self,ip,mask):
		ip_split = ip.net().strNormal().split(".")
		mask_split = mask.net().strNormal().split(".")
		assert len(ip_split)==len(mask_split)==4
		supernet = ""
		for i in range(0,len(ip_split)):
			andOp = int(ip_split[i]) & int(mask_split[i])
			supernet = ".".join([supernet,str(andOp)])
		return IP("/".join([supernet[1:],str(mask.prefixlen())]))
	
	def getMask(self,bit_count):
		ip_builder = ""
		temp = 0
		for i in range(0,bit_count):
			if i % 8 == 0 and i > 0:
				ip_builder = ".".join([ip_builder,str(temp)])
				temp = 0
			temp += 2**(7-(i%8))
		ip_builder = ".".join([ip_builder,str(temp)])
		ip_builder = ip_builder[1:]
		for i in range(0,4-len(ip_builder.split("."))):
			ip_builder = ".".join([ip_builder,"0"])
		return IP("/".join([ip_builder,str(bit_count)]))

def contains(list, element):
	try:
		list.index(element)
		return True
	except ValueError:
		return False

