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
	private String gwip;

	private String masterindex;
	private double speed;
	private int ospf;
	private boolean hsrp;

	private List prefixList;

	Gwport(String ifindex, String interf, String gwip) {
		this(ifindex, interf);
		this.gwip = gwip;
	}

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
	String getGwip() { return gwip; }

	String getMasterindex() { return masterindex; }
	
	/**
	 * Set the masterindex .
	 */
	public void setMasterindex(String s) {
		masterindex = s;
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

	boolean getHsrp() { return hsrp; }

	/**
	 * Set if hsrp is enabled/disabled.
	 */
	public void setHsrp(boolean b) {
		hsrp = b;
	}

	/**
	 * Return a Prefix-object which is used to describe a single prefix.
	 */
	public Prefix prefixFactory(String netaddr) {
		Prefix p = new Prefix(netaddr);
		prefixList.add(p);
		return p;
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
		return "Gwport ifindex="+ifindex+" interf="+interf;
	}

}
