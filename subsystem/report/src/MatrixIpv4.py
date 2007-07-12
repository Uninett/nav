from IPy import IP
from nav.web.templates.MatrixTemplate import MatrixTemplate
from Matrix import Matrix
from Utils import contains

from __future__ import nested_scopes

#TODO: Finish getTemplateResponse

class MatrixIpv4(Matrix):
	
	def __init__(self,start_net,end_net=None):
		Matrix.__init__(self,start_net,end_net=end_net,bits_in_matrix=3)
		self.column_headings = self._getColumnHeaders()

	def getTemplateResponse(self):
		pass

	def _getColumnHeaders(self):
		msb = 8 - (self.end_net.prefixlen()-self.bits_in_matrix) % 8
		lsb = msb - self.bits_in_matrix
		if lsb <= 0:
			lsb = 1
		if msb <= 0:
			msb = 1
		return [(2**lsb)*i for i in range(0,msb)]
