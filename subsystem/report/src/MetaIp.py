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
		self.usage_percent = None

		self._setup()
	
	def extractNetIp(self):
		"""Extract only the octets (or words) of the IP address which
		belongs to the net.

		Returns a string.

		This function is needed by the template."""

		if self.ip.version() == 6:
			return self._extractNetIpIpv6()
		
	def _extractNetIpIpv6(self):
		ip_string = ip.net().strCompressed()
		bits_not_in_net = 16 - ip.prefixlen() % 16
		nybbles_not_in_net = bits_not_in_net / 4
		return ip_string[:-nybbles_not_in_net]

	def _setup(self):
		sql = """SELECT prefixid, active_ip_cnt, max_ip_cnt, nettype
				 FROM prefix LEFT OUTER JOIN prefix_active_ip_cnt USING(prefixid)
							 LEFT OUTER JOIN prefix_max_ip_cnt USING(prefixid)
							 LEFT OUTER JOIN vlan USING(vlanid)
				 WHERE netaddr='%s'""" % str(self.netaddr)
		con = db.getConnection('webfront','manage')
		cursor = con.cursor()

		cursor.execute(sql)
		rows = cursor.fetchall()
		if len(rows) > 1:
			raise SeveralPreficesOnOneIpError
		info = rows[0]

		self.prefixid = info[0]
		self.active_ip_cnt = info[1]
		self.max_ip_cnt = info[2]
		self.nettype= info[3]

		if self.active_ip_cnt > 0 and self.max_ip_cnt > 0:
			self.usage_percent = float(self.active_ip_cnt)/self.max_ip_cnt
		else:
			self.usage_percent = "ERR: Negative number"
