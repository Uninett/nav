from IPTree import buildTree
from IPTree import getSubtree
from IPTree import removeSubnetsWithPrefixLength
from IPTree import extractSubtreesWithPrefixLength

from IPTools import getLastSubnet

class Matrix:

	def __init__(self, start_net, end_net=None, bits_in_matrix=3):
		"""This class is "abstract" and should not be instansiated directly.

		Superclass with usefull methods for IP matrices.
		
		Direct known subclasses:
				MatrixIpv6
				MatrixIpv4
		""" 

		if end_net is None:
			end_net = getLastSubnet(start_net)
		self.start_net = start_net
		self.end_net = end_net
		self.bits_in_matrix = bits_in_matrix
		self.tree = buildTree(start_net, end_net, bits_in_matrix=bits_in_matrix, add_missing_nets=True)
		self.tree_nets = self.extractTreeNets()
		self.matrix_nets = self.extractMatrixNets()

	def getTemplateResponse(self):
		abstract()
	
	def has_too_small_nets(self,net):
		"""Returns true if argument ``net'' has too many small subnets for the matrix."""
		for net in getSubtree(self.tree,net):
			if net.prefixlen() > self.end_net.prefixlen():
				return True
		return False

	def extractMatrixNets(self):
		"""These should be shown as horizontal rows in the matrix."""
		return extractSubtreesWithPrefixLength(self.tree,self.end_net.prefixlen()-self.bits_in_matrix)

	def extractTreeNets(self):
		"""These should be listed vertically in the leftmost column.""" 
		return removeSubnetsWithPrefixLength(self.tree,self.end_net.prefixlen()-self.bits_in_matrix+1)

#because I'm a Java guy
def abstract():
	import inspect
	caller = inspect.getouterframes(inspect.currentframe())[1][3]
	raise NotImplementedError(" ".join([caller,"must be implemented in subclass"]))
