package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

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

	// Return all gwips of this gwport
	Set gwipSet() { return gwportprefixMap.keySet(); }

	// Returns the set of gwips in gwportprefixMap, but not in the given set
	Set gwipIntersection(Set gwipSet) {
		Set s = new HashSet(gwportprefixMap.keySet());
		s.removeAll(gwipSet);
		return s;
	}

	// Returns the number of gwportprefices using hsrp
	int hsrpCount() {
		int hsrpCnt=0;
		for (Iterator it = gwportprefixMap.values().iterator(); it.hasNext();) {
			Gwportprefix gwp = (Gwportprefix)it.next();
			if (gwp.getHsrp()) hsrpCnt++;
		}
		return hsrpCnt;
	}

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

	void addGwportprefix(String gwip, Gwportprefix gp) {
		gwportprefixMap.put(gwip, gp);
	}

	Iterator getGwportPrefices() {
		return gwportprefixMap.values().iterator();
	}

	public boolean equalsGwport(Gwport gw) {
		return (ifindex.equals(gw.ifindex) &&
						(interf == null || interf.equals(gw.interf)) &&
						(link == null || link.equals(gw.link)) &&
						(masterindex == null || masterindex.equals(gw.masterindex)) &&
						(masterinterf == null || masterinterf.equals(masterinterf)) &&
						(speed == null || speed.equals(gw.speed)) &&
						(ospf == null || ospf.equals(gw.ospf)));
	}

	public boolean equals(Object o) {
		return (o instanceof Gwport && 
						equalsGwport((Gwport)o));
	}

	public int compareTo(Object o) {
		Gwport gw = (Gwport)o;
		return interf.compareTo(gw.interf);
	}

	public String toString() {
		return "ifindex="+ifindex+" interf="+interf + " ("+Integer.toHexString(hashCode())+")";
	}

	private String string(Object o) {
		if (o == null) return null;
		return String.valueOf(o);
	}

}
