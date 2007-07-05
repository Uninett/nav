from IPy import IP
from nav import db

class SeveralPreficesOnOneIpError(Exception): pass
class MetaIp:
	"""Class for holding meta information on one IPy.IP address"""
	def __init__(self,ip):
		self.netaddr = ip
		self.prefixid = None
		self.active_ip_cnt = None
		self.max_ip_cnt = None
		self.nettype = None
		
		self.__setup()
	
	def extractNetIp(self):
		"""Extract only the octets (or words) of the IP address which
		belongs to the net.

		Returns a string.

		This function is needed by the template."""

		if self.ip.version() == 6:
			return self.__extractNetIpIpv6()
		
	def __extractNetIpIpv6(self):
		ip_string = ip.net().strCompressed()
		bits_not_in_net = 16 - ip.prefixlen() % 16
		nybbles_not_in_net = bits_not_in_net / 4
		return ip_string[:-nybbles_not_in_net]

	def __setup(self):
		sql = """SELECT prefixid, active_ip_cnt, max_ip_cnt, nettype
				 FROM prefix JOIN prefix_active_ip_cnt USING(prefixid)
							 JOIN prefix_max_ip_cnt USING(prefixid)
							 JOIN vlan USING(vlanid)
				 WHERE netaddr=self.netaddr and nettype != 'scope'"""
		con = db.getConnection('webfront','manage')
		cursor = con.cursor()

		cursor.execute(sql)
		info = cursor.fetchall()
		if len(info) > 1:
			raise SeveralPreficesOnOneIpError
		self.prefixid = info[0]
		self.active_ip_cnt = info[1]
		self.max_ip_cnt = info[2]
		self.netaddr = info[3]
