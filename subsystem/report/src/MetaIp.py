from IPy import IP
from nav import db
import Matrix

class UnexpectedRowCountError(Exception): pass
class MetaIp:
	"""Class for holding meta information on one IPy.IP address"""
	def __init__(self,ip):
		self.netaddr = ip
		self.prefixid = None
		self.active_ip_cnt = None
		self.max_ip_cnt = None
		self.net_type = None	
		self.usage_percent = None

		if ip.version() == 4:
			self._setupIpv4()
		else:
			self._setupIpv6()
	
	def getTreeNet(self):
		if self.netaddr.version() == 6:
			return self._getTreeNetIpv6()
	
	def _getTreeNetIpv6(self):
		netaddr = None
		hexlets_in_address = int(float(self.netaddr.prefixlen())/16+0.5)
		if self.netaddr.prefixlen() < 112:
			netaddr = self.netaddr.net().strCompressed()[:-2]
		else:
			netaddr = self.netaddr.net().strCompressed()

		first_hexlets = netaddr[:netaddr.rfind(":")]
		long_last_hexlet = self.netaddr.net().strFullsize().split(":")[hexlets_in_address-1]
		return ":".join([first_hexlets,long_last_hexlet[:-1]])

	def _setupIpv6(self):
		sql = """SELECT prefixid,nettype
				 FROM prefix LEFT OUTER JOIN vlan USING(vlanid)
				 WHERE netaddr='%s'""" % str(self.netaddr)

		cursor = Matrix.database_cursor or db.getConnection('webfront','manage').cursor()
		cursor.execute(sql)
		rows = cursor.fetchall()
		if len(rows) == 1:
			info = rows[0]

			self.prefixid = info[0]
			self.net_type = info[1]
			#DEBUG ONLY
			self.usage_percent = 100

	def _setupIpv4(self):
		sql = """SELECT prefixid, active_ip_cnt, max_ip_cnt, nettype
				 FROM prefix LEFT OUTER JOIN prefix_active_ip_cnt USING(prefixid)
							 LEFT OUTER JOIN prefix_max_ip_cnt USING(prefixid)
							 LEFT OUTER JOIN vlan USING(vlanid)
				 WHERE netaddr='%s'""" % str(self.netaddr)
		con = db.getConnection('webfront','manage')
		cursor = con.cursor()

		cursor.execute(sql)
		rows = cursor.fetchall()
		if len(rows) == 1:
			info = rows[0]

			self.prefixid = info[0]
			self.active_ip_cnt = info[1]
			self.max_ip_cnt = info[2]
			self.net_type= info[3]

			if self.active_ip_cnt > 0 and self.max_ip_cnt > 0:
				self.usage_percent = float(self.active_ip_cnt)/self.max_ip_cnt
			else:
				#TODO: Remove the next line and uncomment the line after that when the database
				#		has been fixed to handle IPv6
				self.usage_percent = 100
				#self.usage_percent = "ERR: Negative number"
