from IPy import IP
from nav import db

from IPTree import buildTree
from IPTree import getSubtree
from IPTree import removeSubnetsWithPrefixLength
from IPTree import extractSubtreesWithPrefixLength

from IPTools import getLastSubnet

#TODO:	Standardize documentation style.

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
		self.max_diff_before_dots = 6

	def getTemplateResponse(self):
		abstract()
	
	def has_too_small_nets(self,net):
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

def suggestEndNet(start_net):
	max_prefix_length = None
	if start_net.version == 4:
		max_prefix_length = 32
	else:
		max_prefix_length = 128 

	sql = """SELECT MAX(masklen(netaddr))
			 FROM prefix
			 WHERE netaddr << '%s' AND masklen(netaddr) < %d""" \
					 % (str(start_net),max_prefix_length)

	db_cursor = db.getConnection('webfront','manage').cursor()
	db_cursor.execute(sql)
	end_net_prefix_len = db_cursor.fetchall()[0][0]
	if end_net_prefix_len == None:
		return IP("/".join([str(start_net.net()),str(128)]))
	else:
		return IP("/".join([str(start_net.net()),str(end_net_prefix_len)]))

#because I'm a Java guy
def abstract():
	import inspect
	caller = inspect.getouterframes(inspect.currentframe())[1][3]
	raise NotImplementedError(" ".join([caller,"must be implemented in subclass"]))
