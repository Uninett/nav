package no.ntnu.nav.getDeviceData.dataplugins.Gwport;

import no.ntnu.nav.logger.*;

import java.util.ArrayList;

/**
 * Contain Vlan data
 */

public class Vlan implements Comparable
{
	public static final String UNKNOWN_NETTYPE = "unknown";

	private int vlanid;
	private Integer vlan;

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
		setVlan(vlan);
	}

	int getVlanid() { return vlanid; }
	String getVlanidS() { return ""+vlanid; }
	void setVlanid(int i) { vlanid = i; }
	void setVlanid(String s) { vlanid = Integer.parseInt(s); }

	Integer getVlan() { return vlan; }
	String getVlanS() { return vlan == null ? null : String.valueOf(vlan); }
	void setVlan(int i) { vlan = i == 0 ? null : new Integer(i); }

	String getNettype() { return nettype; }
	String getOrgid() { return orgid; }
	String getUsageid() { return usageid; }
	String getNetident() { return netident; }
	String getDescription() { return description; }

	void setNetident(String s) { netident = s; }

	void setEqual(Vlan vl) {
		if (vl.vlan != null) vlan = vl.vlan;
		if (!vl.nettype.equals(UNKNOWN_NETTYPE)) nettype = vl.nettype;
		orgid = vl.orgid;
		usageid = vl.usageid;
		netident = vl.netident;
		description = vl.description;
	}

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

	public boolean equalsDataVlan(Vlan vl) {
		return ((equals(orgid, vl.orgid)) &&
				(equals(usageid, vl.usageid)) &&
				(equals(netident, vl.netident)) &&
				(equals(description, vl.description)));
	}

	public boolean equalsVlan(Vlan vl) {
		return ((vlan == null || vlan.equals(vl.vlan)) &&
				(equals(nettype, vl.nettype)) &&
				equalsDataVlan(vl));
	}

	public boolean equals(Object o) {
		return (o instanceof Vlan && 
						equalsVlan((Vlan)o));
	}

	public int compareTo(Object o) {
		Vlan v = (Vlan)o;
		return vlan.compareTo(v.vlan);
	}

	public String toString() {
		return vlan + ", nettype="+nettype+", org="+orgid+", usage="+usageid+", netident="+netident+", descr="+description + " ("+Integer.toHexString(hashCode())+")";
	}

	public static boolean equals(String s1, String s2) {
		if (s1 == null && s2 == null) return true;
		if (s1 != null) return s1.equals(s2);
		return s2.equals(s1);
	}


}
