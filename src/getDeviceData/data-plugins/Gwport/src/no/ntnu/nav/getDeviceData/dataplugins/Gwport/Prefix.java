package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;

import no.ntnu.nav.logger.*;

/**
 * Contain Prefix data
 */

public class Prefix implements Comparable
{
	private int prefixid;

	private String netaddr;
	private int masklen;
	private Vlan vlan;

	private Set gwportidSet = new HashSet();

	Prefix(String netaddr, int masklen, Vlan vlan) {
		this.netaddr = netaddr;
		this.masklen = masklen;
		this.vlan = vlan;
	}

	Prefix(String gwip, String netmask, Vlan vlan) {
		this(and_ip(gwip, netmask), masklen(netmask), vlan);
	}

	public static String and_ip(String ip, String mask) {
		StringTokenizer a = new StringTokenizer(hexToIp(ip), ".");
		StringTokenizer b = new StringTokenizer(hexToIp(mask), ".");
		String and_ip = "";

		while (a.hasMoreTokens()) {
			and_ip += "."+(Integer.parseInt(a.nextToken())&Integer.parseInt(b.nextToken()));
		}
		return and_ip.substring(1, and_ip.length());
	}

	// Calc the number of bits in mask
	public static int masklen(String mask) {
		int bits = 0;
		String[] s = hexToIp(mask).split("\\.");

		for (int i=0; i < s.length; i++) {
			// 8-(log (256-128) / log 2)
			bits += (int) Math.round( 8 - (Math.log(256-Integer.parseInt(s[i])) / Math.log(2)) );
		}
		return bits;
	}

	public static String hexToIp(String s) {
		return convIp(s, 16, 10, ':', '.', 0);
	}

	public static String ipToHex(String s) {
		return convIp(s, 10, 16, '.' ,':', 2);
	}

	public static String convIp(String hexIp, int fromBase, int toBase, char oldsep, char newsep, int minDigits) {
		if (hexIp == null || hexIp.indexOf(oldsep) < 0) return hexIp;
		String ip = "";
		String escape = oldsep == '.' ? "\\" : "";
    String[] s = hexIp.split(escape+oldsep);
		for (int i=0; i < s.length; i++) {
			String t = Integer.toString(Integer.parseInt(s[i],fromBase),toBase);
			if (minDigits > 0) while (t.length() < minDigits) t = "0" + t;
			ip += t.toUpperCase() + newsep;
		}
		return ip.substring(0, ip.length()-1);
	}
		


	int getPrefixid() { return prefixid; }
	String getPrefixidS() { return String.valueOf(prefixid); }
	void setPrefixid(int i) { prefixid = i; }
	void setPrefixid(String s) { prefixid = Integer.parseInt(s); }

	void setNetaddr(String n) { netaddr = n; }
	void setMasklen(int l) { masklen = l; }
	void setVlan(Vlan v) { vlan = v; }

	void addGwport(String gwportid) { gwportidSet.add(gwportid); }
	void removeGwport(String gwportid) { gwportidSet.remove(gwportid); }
	int gwportCount() { return gwportidSet.size(); }
	Iterator getGwportidIterator() { return gwportidSet.iterator(); }

	String getNetaddr() { return netaddr; }
	int getMasklen() { return masklen; }
	String getCidr() { return netaddr+"/"+masklen; }
	Vlan getVlan() { return vlan; }

	/*
	public void setRootgwid(int rootgwid) {
		this.rootgwid = rootgwid;
	}
	void getRootgwid() { return rootgwid; }
	*/

	public boolean equalsPrefix(Prefix p) {
		return (netaddr.equals(p.netaddr) &&
						masklen == p.masklen &&
						vlan.getVlanid() == p.vlan.getVlanid());
	}

	public boolean equals(Object o) {
		return (o instanceof Prefix && 
						equalsPrefix((Prefix)o));
	}

	public int compareTo(Object o) {
		Prefix p = (Prefix)o;
		return netaddr.compareTo(p.netaddr);
	}

	public String toString() {
		return netaddr + "/" + masklen;
	}

}
