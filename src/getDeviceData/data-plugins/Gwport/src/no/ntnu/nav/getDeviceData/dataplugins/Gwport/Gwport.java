package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;

import no.ntnu.nav.logger.*;

/**
 * Contain Gwport data
 */

public class Gwport implements Comparable
{
	private int gwportid;

	private String ifindex;
	private String interf;

	private int masterindex;
	private String masterinterf;
	private double speed;
	private int ospf;

	private Map gwportprefixMap = new HashMap();

	Gwport(String ifindex, String interf) {
		this.ifindex = ifindex;
		this.interf = interf;
	}

	int getGwportid() { return gwportid; }
	String getGwportidS() { return String.valueOf(gwportid); }
	void setGwportid(int i) { gwportid = i; }
	void setGwportid(String s) { gwportid = Integer.parseInt(s); }

	String getIfindex() { return ifindex; }
	String getIfindexS() { return ((ifindex.length()==1)?" ":"")+getIfindex(); }
	String getInterf() { return interf; }
	//String getGwip() { return gwip; }

	int getMasterindex() { return masterindex; }
	void setMasterindex(int i) { masterindex = i; }

	String getMasterinterf() { return masterinterf; }
	
	/**
	 * Set the masterinterf .
	 */
	public void setMasterinterf(String s) {
		masterinterf = s;
	}

	double getSpeed() { return speed; }
	
	/**
	 * Set the speed.
	 */
	public void setSpeed(double d) {
		speed = d;
	}

	int getOspf() { return ospf; }

	/**
	 * Set ospf cost.
	 */
	public void setOspf(int i) {
		ospf = i;
	}

	/**
	 * Return a Prefix-object which is used to describe a single prefix.
	 */
	public Prefix prefixFactory(String gwip, boolean hsrp, String netmask, Vlan vlan) {
		Prefix p = new Prefix(gwip, netmask, vlan);
		Gwportprefix gp = new Gwportprefix(gwip, hsrp, p);
		gwportprefixMap.put(gwip, gp);
		return p;
	}

	Prefix prefixFactory(String gwip, boolean hsrp, String netaddr, int masklen, Vlan vlan) {
		Prefix p = new Prefix(netaddr, masklen, vlan);
		Gwportprefix gp = new Gwportprefix(gwip, hsrp, p);
		gwportprefixMap.put(gwip, gp);
		return p;
	}

	Iterator getGwportPrefices() {
		return gwportprefixMap.values().iterator();
	}

	/*
	private String ifindex;
	private String interf;
	private String gwip;

	private String masterindex;
	private double speed;
	private int ospf;
	private boolean hsrp;

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
		Gwport gw = (Gwport)o;
		return interf.compareTo(gw.interf);
	}

	public String toString() {
		return "ifindex="+ifindex+" interf="+interf;
	}

}
