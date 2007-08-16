from Matrix import Matrix
from ColorConfiguration import ColorConfiguration
from nav.web.templates.MatrixIpv6Template import MatrixIpv6Template

import nav.path
import os
import string

configfile = os.path.join(nav.path.sysconfdir,"report/matrix.conf")

class MatrixIpv6(Matrix):
	"""This class serves as an interface for the prefix matrix.

	Call getTemplateResponse() to get the template response."""

	def __init__(self,start_net,end_net=None):
		Matrix.__init__(self,start_net,end_net=end_net,bits_in_matrix=4)
		self.column_headings = ["%X" % i for i in range(0,16)]

	def getTemplateResponse(self):
		import Matrix
		import Utils
		import IPTools
		import MetaIP

		template = MatrixIpv6Template()
		template.path = [("Home", "/"), ("Report", "/report/"), ("Prefix Matrix",False)]

		#functions and classes
		template.sort_nets_by_address = getattr(IPTools,"sort_nets_by_address")
		template.MetaIP = getattr(MetaIP,"MetaIP")
		template.getLastbitsIpMap = getattr(IPTools,"getLastbitsIpMap")
		template.sub = getattr(Utils,"sub")
		template.stringDotJoin = getattr(string,"join")
		template.isIntermediateNets = getattr(IPTools,"isIntermediateNets")

		#variables
		template.start_net = self.start_net
		template.end_net = self.end_net
		template.tree_nets = self.tree_nets
		template.matrix_nets = self.matrix_nets
		template.column_headings = self.column_headings
		template.bits_in_matrix = self.bits_in_matrix
		template.color_configuration = ColorConfiguration(configfile)
		return template.respond()
