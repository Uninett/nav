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

	private List vlanList;

	Prefix(String netaddr) {
		this.netaddr = netaddr;
	}

	int getPrefixid() { return prefixid; }
	String getPrefixidS() { return String.valueOf(prefixid); }
	void setPrefixid(int i) { prefixid = i; }
	void setPrefixid(String s) { prefixid = Integer.parseInt(s); }

	String getNetaddr() { return netaddr; }

	/**
	 * Return a Vlan-object which is used to describe a single vlan.
	 */
	public Vlan vlanFactory(int vlan) {
		Vlan v = new Vlan(vlan);
		vlanList.add(v);
		return v;
	}

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
		return "Prefix netaddr="+netaddr;
	}

}
