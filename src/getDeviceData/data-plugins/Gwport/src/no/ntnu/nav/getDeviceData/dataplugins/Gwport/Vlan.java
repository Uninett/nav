package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import no.ntnu.nav.logger.*;

import java.util.ArrayList;

/**
 * Contain Vlan data
 */

public class Vlan implements Comparable
{
	private int vlanid;
	private int vlan;

	private String nettype;
	private String orgid;
	private String usageid;
	private String netident;
	private String description;

	Vlan(String netident) {
		this.netident = netident;
	}

	Vlan(String netident, int vlan) {
		this(netident);
		this.vlan = vlan;
	}

	int getVlanid() { return vlanid; }
	void setVlanid(int i) { vlanid = i; }	

	int getVlan() { return vlan; }
	void setVlan(int i) { vlan = i; }

	/**
	 * Set nettype.
	 */
	public void setNettype(String s) {
		nettype = s;
	}

	/**
	 * Set org.
	 */
	public void setOrgid(String s) {
		orgid = s;
	}

	/**
	 * Set usage.
	 */
	public void setUsageid(String s) {
		usageid = s;
	}

	/**
	 * Set description.
	 */
	public void setDescription(String s) {
		description = s;
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
		Vlan v = (Vlan)o;
		return new Integer(vlan).compareTo(new Integer(v.vlan));
	}

	public String toString() {
		return vlan + ", nettype="+nettype+", org="+orgid+", usage="+usageid+", netident="+netident+", descr="+description;
	}

}
