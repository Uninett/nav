from IPy import IP
from nav import db

from Utils import contains

from math import ceil

cursor = db.getConnection('webfront','manage').cursor()

ipv4MetaMap = None
ipv6MetaMap = None

def _createIpv6MetaMap():
	"""At the time of writing, neither prefix_active_ip_cnt nor prefix_max_ip_cnt
	contain/calculates the correct values for IPv6. Once this has been fixed, this
	function needs to be changed."""
	
	sql = """SELECT prefixid, nettype, netaddr
			 FROM prefix LEFT OUTER JOIN vlan USING(vlanid)
			 WHERE family(netaddr)=6"""

	cursor.execute(sql)
	rows = cursor.fetchall()
	result = {}
	for row in rows:
		tupple = {}
		tupple["prefixid"] = row[0]
		tupple["nettype"] = row[1]
		result[IP(row[2])] = tupple
	return result

def _createIpv4MetaMap():
	sql = """SELECT prefixid, active_ip_cnt, max_ip_cnt, nettype, netaddr
			 FROM prefix LEFT OUTER JOIN prefix_active_ip_cnt USING(prefixid)
						 LEFT OUTER JOIN prefix_max_ip_cnt USING(prefixid)
						 LEFT OUTER JOIN vlan USING(vlanid)
			 WHERE family(netaddr)=4"""
	cursor.execute(sql)
	rows = cursor.fetchall()
	result = {}
	for row in rows:
		tupple = {}
		tupple["prefixid"] = row[0]
		tupple["active_ip_cnt"] = row[1]
		tupple["max_ip_cnt"] = row[2]
		tupple["nettype"] = row[3]
		result[IP(row[4])] = tupple
	return result

if ipv4MetaMap is None:
	ipv4MetaMap = _createIpv4MetaMap()

if ipv6MetaMap is None:
	ipv6MetaMap = _createIpv6MetaMap()

class UnexpectedRowCountError(Exception): pass
class MetaIP:
	"""Class for holding meta information on one IPy.IP address"""
	def __init__(self,ip):
		self.netaddr = ip
		self.prefixid = None
		self.active_ip_cnt = None
		self.max_ip_cnt = None
		self.nettype = None	
		self.usage_percent = None

		if ip.version() == 4:
			self._setupIpv4()
		else:
			self._setupIpv6()
	
	def getTreeNet(self):
		"""This method is used to get the string representation of the IP
		shown in the tree to left of the prefix matrix."""

		#IPv6: Whole address
		#IPv4: Not whole address
		if self.netaddr.version() == 6:
			return self._getTreeNetIpv6()
		elif self.netaddr.version() == 4:
			return self._getTreeNetIpv4()
	
	def _getTreeNetIpv4(self):
		"""Remove host octet."""
		netaddr_string = self.netaddr.net().strNormal()
		return netaddr_string[:netaddr_string.rfind(".")]

	def _getTreeNetIpv6(self):
		"""Compress self.netaddr, remove "::", and padd with ":0"."""
		netaddr = None
		hexlets_in_address = int(float(self.netaddr.prefixlen())/16+0.5)
		if self.netaddr.prefixlen() < 112:
			netaddr = self.netaddr.net().strCompressed()[:-2]
		else:
			netaddr = self.netaddr.net().strCompressed()

		#in case .strCompressed() compressed it too much
		while netaddr.count(":") < hexlets_in_address-1:
			netaddr = ":".join([netaddr,"0"])

		return netaddr ##...don't want leading zero after all
	
	def _setupIpv6(self):
		if contains(ipv6MetaMap.keys(),self.netaddr):
			metainfo = ipv6MetaMap[self.netaddr]
			self.prefixid = metainfo["prefixid"]
			self.nettype = metainfo["nettype"]
			self.usage_percent = 4

	def _setupIpv4(self):
		if contains(ipv4MetaMap.keys(),self.netaddr):
			metainfo = ipv4MetaMap[self.netaddr]
			self.prefixid = metainfo["prefixid"]
			self.nettype = metainfo["nettype"]
			
			active_ip_cnt = metainfo["active_ip_cnt"]
			max_ip_cnt = metainfo["max_ip_cnt"]

			if active_ip_cnt is None:
				self.active_ip_cnt = 0
			else:
				self.active_ip_cnt = int(active_ip_cnt)

			self.max_ip_cnt = int(max_ip_cnt)

			if self.active_ip_cnt > 0 and self.max_ip_cnt > 0:
				self.usage_percent = int(ceil(100*float(self.active_ip_cnt)/self.max_ip_cnt))
			else:
				self.usage_percent = 0
