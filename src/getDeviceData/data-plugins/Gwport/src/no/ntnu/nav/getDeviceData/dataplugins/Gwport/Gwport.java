package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.*;

import no.ntnu.nav.logger.*;

/**
 * Contain Gwport data
 */

public class Gwport implements Comparable
{
	/**
	 * The switch port has link.
	 */
	public static final char PORT_LINK_YES = 'y';

	/**
	 * The switch port does not have link.
	 */
	public static final char PORT_LINK_NO = 'n';

	/**
	 * The switch port is turned off (admin down).
	 */
	public static final char PORT_LINK_DOWN = 'd';

	private int gwportid;

	private String ifindex;
	private String interf;

	private Character link;
	private Integer masterindex;
	private String masterinterf;
	private Double speed;
	private Integer ospf;

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

	Integer getMasterindex() { return masterindex; }
	void setMasterindex(int i) { masterindex = new Integer(i); }

	String getMasterinterf() { return masterinterf; }

	Gwportprefix getGwportprefix(String gwip) { return (Gwportprefix)gwportprefixMap.get(gwip); }

	/**
	 * Set the masterinterf .
	 */
	public void setMasterinterf(String s) {
		masterinterf = s;
	}

	Character getLink() { return link; }
	String getLinkS() { return string(link); }
	

	/**
	 * Set the link status of the port:
	 * 
	 * <ul>
	 *  <li>'y' means link is up</li>
	 *  <li>'n' means link is down</li>
	 *  <li>'d' means the port is turned off (adm down)</li>
	 * </ul>
	 */
	public void setLink(char c) { link = new Character(c); }

	Double getSpeed() { return speed; }
	String getSpeedS() { return string(speed); }

	/**
	 * Set the current speed of the port in MBit/sec.
	 *
	 */
	public void setSpeed(double d) { speed = new Double(d); }

	Integer getOspf() { return ospf; }
	String getOspfS() { return string(ospf); }

	/**
	 * Set ospf cost.
	 */
	public void setOspf(int i) {
		ospf = new Integer(i);
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

	public boolean equalsGwport(Gwport gw) {
		return false;
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
		Gwport gw = (Gwport)o;
		return interf.compareTo(gw.interf);
	}

	public String toString() {
		return "ifindex="+ifindex+" interf="+interf;
	}

	private String string(Object o) {
		if (o == null) return null;
		return String.valueOf(o);
	}

}
