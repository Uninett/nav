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
		this.vlan = new Integer(vlan);
	}

	int getVlanid() { return vlanid; }
	String getVlanidS() { return ""+vlanid; }
	void setVlanid(int i) { vlanid = i; }
	void setVlanid(String s) { vlanid = Integer.parseInt(s); }

	Integer getVlan() { return vlan; }
	String getVlanS() { return vlan == null ? null : String.valueOf(vlan); }
	void setVlan(int i) { vlan = new Integer(i); }

	String getNettype() { return nettype; }
	String getOrgid() { return orgid; }
	String getUsageid() { return usageid; }
	String getNetident() { return netident; }
	String getDescription() { return description; }

	void setNetident(String s) { netident = s; }

	void setEqual(Vlan vl) {
		if (vl.vlan != null) vlan = vl.vlan;
		if (vl.nettype != null && !vl.nettype.equals(UNKNOWN_NETTYPE)) nettype = vl.nettype;
		if (vl.orgid != null) orgid = vl.orgid;
		if (vl.usageid != null) usageid = vl.usageid;
		if (vl.netident != null) netident = vl.netident;
		if (vl.description != null) description = vl.description;
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

	public boolean equalsVlan(Vlan vl) {
		return ((vlan == null || vlan.equals(vl.vlan)) &&
						(nettype == null || nettype.equals(UNKNOWN_NETTYPE) || nettype.equals(vl.nettype)) &&
						(orgid == null || orgid.equals(vl.orgid)) &&
						(usageid == null || usageid.equals(vl.usageid)) &&
						(netident == null || netident.equals(vl.netident)) &&
						(description == null || description.equals(vl.description)));
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

}
