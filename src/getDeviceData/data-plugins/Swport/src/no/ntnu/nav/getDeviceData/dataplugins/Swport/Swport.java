package no.ntnu.nav.getDeviceData.dataplugins.Swport;

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

	private char link;
	private String speed;
	private char duplex;
	private String media = "";
	private boolean trunk;
	private String portname = "";

	private int vlan = 0;
	private ArrayList vlanList;

	private String hexstring;

	public Swport(Integer port, String ifindex)
	{
		this.port = port;
		this.ifindex = ifindex.trim();

		this.link = PORT_LINK_DOWN;
		this.speed = "";
		this.trunk = false;
	}

	public Swport(Integer port, String ifindex, char link, String speed, char duplex, String media, boolean trunk, String portname)
	{
		this.port = port;
		this.ifindex = ifindex.trim();

		this.link = link;
		this.speed = speed.trim();
		this.duplex = duplex;
		if (media != null) this.media = media.trim();
		setTrunk(trunk);
		if (portname != null) this.portname = portname.trim();
	}

	int getSwportid() { return swportid; }
	String getSwportidS() { return String.valueOf(swportid); }
	void setSwportid(int i) { swportid = i; }
	void setSwportid(String s) { swportid = Integer.parseInt(s); }

	Integer getPort() { return port; }
	String getPortS() { return ((port.toString().length()==1)?" ":"")+getPort(); }

	String getIfindex() { return ifindex; }
	String getIfindexS() { return ((ifindex.length()==1)?" ":"")+getIfindex(); }

	char getLink() { return link; }

	String getSpeed() { return speed; }
	char getDuplex() { return duplex; }
	String getDuplexS() { return String.valueOf(duplex); }
	String getMedia() { return media; }
	boolean getTrunk() { return trunk; }
	String getTrunkS() { return trunk?"t":"f"; }
	String getPortname() { return portname; }

	public void setLink(char c) { link = c; }
	public void setSpeed(String s) { speed = s.trim(); }
	public void setDuplex(char c) { duplex = c; }
	public void setMedia(String s) { media = s.trim(); }
	public void setTrunk(boolean b) {
		trunk = b;
		if (trunk && vlanList == null) vlanList = new ArrayList();
	}
	public void setPortname(String s) { portname = s.trim(); }

	int getVlan() { return vlan; }
	public void setVlan(int i) { vlan = i; }

	public void addTrunkVlan(String vlan) {
		if (!trunk) return;
		vlanList.add(vlan);
	}

	String getHexstring() {
		if (hexstring == null) hexstring = getVlanAllowHexString();
		return hexstring;
	}
	public void setHexstring(String s) { hexstring = s; }

	String getVlanAllowHexString()
	{
		if (!getTrunk()) return "";

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

	public boolean equals(Object o) {
		if (o instanceof Swport) {
			Swport sw = (Swport)o;
			return (port.equals(sw.port) &&
					ifindex.equals(sw.ifindex) &&
					link == sw.link &&
					speed.equals(sw.speed) &&
					duplex == sw.duplex &&
					media.equals(sw.media) &&
					trunk == sw.trunk &&
					portname.equals(sw.portname));
		}
		return false;
	}

	public int compareTo(Object o) {
		Swport sw = (Swport)o;
		return port.compareTo(sw.port);
	}
	public String toString() { return getPortS()+": Ifindex: " + getIfindexS() + " Link: " + getLink() + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media; }
}
