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
	//private int rootgwid;
	private Vlan vlan;

	Prefix(String netaddr, int masklen, Vlan vlan) {
		this.netaddr = netaddr;
		this.masklen = masklen;
		this.vlan = vlan;
	}

	Prefix(String gwip, String netmask, Vlan vlan) {
		this(and_ip(gwip, netmask), masklen(netmask), vlan);
	}

	private static String and_ip(String ip, String mask) {
		StringTokenizer a = new StringTokenizer(ip, ".");
		StringTokenizer b = new StringTokenizer(mask, ".");
		int base = 10;
		if (b.countTokens() == 1) {
			b = new StringTokenizer(mask, ":");
			base = 16;
		}
		String and_ip = "";

		while (a.hasMoreTokens()) {
			and_ip += "."+(Integer.parseInt(a.nextToken(),base)&Integer.parseInt(b.nextToken(),base));
		}
		return and_ip.substring(1, and_ip.length());
	}

	// Calc the number of bits in mask
	private static int masklen(String mask) {
		int bits = 0;
		String[] s = mask.split("\\.");
		int base = 10;
		if (s.length == 1) {
			s = mask.split(":");
			base = 16;
		}
		for (int i=0; i < s.length; i++) {
			// 8-(log (256-128) / log 2)
			bits += (int) Math.round( 8 - (Math.log(256-Integer.parseInt(s[i],base)) / Math.log(2)) );
		}
		return bits;
	}


	int getPrefixid() { return prefixid; }
	String getPrefixidS() { return String.valueOf(prefixid); }
	void setPrefixid(int i) { prefixid = i; }
	void setPrefixid(String s) { prefixid = Integer.parseInt(s); }

	String getNetaddr() { return netaddr; }
	Vlan getVlan() { return vlan; }

	/*
	public void setRootgwid(int rootgwid) {
		this.rootgwid = rootgwid;
	}
	void getRootgwid() { return rootgwid; }
	*/

	/*
	public boolean equalsGwport(Gwport gw) {
		return (port.equals(sw.port) &&
						ifindex.equals(sw.ifindex) &&
						link == sw.link &&
						speed.equals(sw.speed) &&
						duplex == sw.duplex &&
						media.equals(sw.media) &&
						trunk == sw.trunk &&
						portname.equals(sw.portname));
	}

	public boolean equals(Object o) {
		return (o instanceof Swport && 
						equalsSwport((Swport)o) &&
						super.equals(o));
	}
	*/

	public int compareTo(Object o) {
		Prefix p = (Prefix)o;
		return netaddr.compareTo(p.netaddr);
	}

	public String toString() {
		return netaddr + "/" + masklen;
	}

}
