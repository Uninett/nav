package no.ntnu.nav.getDeviceData.dataplugins.Swport;

import no.ntnu.nav.logger.*;

import java.util.ArrayList;

/**
 * Contain Swport data
 */

public class Swport implements Comparable
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

	private int swportid;

	private Integer port;
	private String ifindex;

	private Character link;
	private String speed;
	private Character duplex;
	private String media;
	private Boolean trunk;
	private String portname;

	private Integer vlan;
	private ArrayList vlanList;

	private String hexstring;

	public Swport(Integer port, String ifindex)
	{
		this.port = port;
		this.ifindex = ifindex.trim();
	}

	public Swport(Integer port, String ifindex, char link, String speed, char duplex, String media, boolean trunk, String portname)
	{
		this.port = port;
		this.ifindex = ifindex.trim();

		setLink(link);
		setSpeed(speed);
		setDuplex(duplex);
		setMedia(media);
		setTrunk(trunk);
		setPortname(portname);
	}

	int getSwportid() { return swportid; }
	String getSwportidS() { return String.valueOf(swportid); }
	void setSwportid(int i) { swportid = i; }
	void setSwportid(String s) { swportid = Integer.parseInt(s); }

	Integer getPort() { return port; }
	String getPortS() {
		if (port == null) return null;
		return ((port.toString().length()==1)?"0":"")+getPort();
	}

	String getIfindex() { return ifindex; }
	String getIfindexS() { return ((ifindex.length()==1)?"0":"")+getIfindex(); }

	Character getLink() { return link; }
	String getLinkS() { return string(link); }

	String getSpeed() { return speed; }
	Character getDuplex() { return duplex; }
	String getDuplexS() {
		if (duplex == null) return null;
		String s = String.valueOf(duplex).trim();
		if (s.length() == 0) {
			Log.w("SWPORT", "MISSING_DUPLEX", "Defaulting to full duplex. Port="+getPort()+", Swportid="+getSwportid());
			return "f";
		}
		return s;
	}

	String getMedia() { return media; }

	/**
	 * Get if the port is using trunking or not.
	 */
	public Boolean getTrunk() { return trunk; }
	boolean getTrunkB() { return trunk != null && trunk.booleanValue(); }
	String getTrunkS() {
		if (getTrunk() == null) return null;
		return getTrunk().booleanValue()?"t":"f";
	}
	String getPortname() { return portname; }

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

	/**
	 * Set the current speed of the port in MBit/sec.
	 *
	 */
	public void setSpeed(String s) { speed = trim(s); }

	/**
	 * Set the current duplex of the port:
	 * 
	 * <ul>
	 *  <li>'f' means full duplex</li>
	 *  <li>'h' means half duplex</li>
	 * </ul>
	 */
	public void setDuplex(char c) { duplex = new Character(c); }

	/**
	 * Set the media type for the port, e.g. "100BaseTX" for a 100Mbit TP port.
	 */
	public void setMedia(String s) { media = trim(s); }

	/**
	 * Set if the port is using trunking or not.
	 */
	public void setTrunk(boolean b) {
		trunk = new Boolean(b);
		if (b && vlanList == null) vlanList = new ArrayList();
	}

	/**
	 * Set the port name
	 */
	public void setPortname(String s) { portname = trim(s); }

	Integer getVlan() { return vlan; }

	/**
	 * Set the vlan; only use this for non-trunking ports.
	 */
	public void setVlan(int i) { vlan = new Integer(i); }

	/**
	 * Used for trunking ports; call this method to add
	 * the VLANs allowed on the port.
	 */
	public void addTrunkVlan(String vlan) {
		if (!getTrunkB()) return;
		vlanList.add(vlan);
	}

	String getHexstring() {
		if (hexstring == null) hexstring = getVlanAllowHexString();
		return hexstring;
	}

	/**
	 * Set the allowed VLANs as a hexstring (used on Cisco devices).
	 */
	public void setHexstring(String s) { hexstring = s; }

	String getVlanAllowHexString()
	{
		if (!getTrunkB()) return "";

		int[] a = new int[256];
		for (int i=0; i < a.length; i++) a[i] = 0;

		for (int i=0; i < vlanList.size(); i++) {
			int vlan = Integer.parseInt((String)vlanList.get(i));

			int index = vlan / 4;
			a[index] ^= (1<<3-(vlan%4));
		}

		StringBuffer sb = new StringBuffer();
		for (int i=0; i < a.length; i++) sb.append(Integer.toString(a[i], 16));

		return sb.toString();
	}

	/*
	public static void main(String[] args)
	{
		String s = "4080000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040000000000008000000000000000000";
		for (int i=0;i<1024;i++) {
			if (isAllowedVlan(s, i)) System.out.println("vlan " + i + " allowed");
		}

	}
	private static boolean isAllowedVlan(String hexstr, int vlan)
	{
		if (vlan < 0 || vlan > 1023) return false;
		int index = vlan / 4;

		int allowed = Integer.parseInt(String.valueOf(hexstr.charAt(index)), 16);
		return ((allowed & (1<<3-(vlan%4))) != 0);
	}
	*/

	public boolean equalsSwport(Swport sw) {
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

	public int compareTo(Object o) {
		Swport sw = (Swport)o;
		return port.compareTo(sw.port);
	}

	public String toString() {
		return getPortS() + ": " +
			"Ifindex: " + getIfindexS() +
			" Link: " + getLink() +
			" Speed: " + speed +
			" Duplex: " + duplex +
			" Media: " + media; 
	}

	private String trim(String s) {
		return (s == null) ? s : s.trim();
	}

	private String string(Object o) {
		if (o == null) return null;
		return String.valueOf(o);
	}

}
