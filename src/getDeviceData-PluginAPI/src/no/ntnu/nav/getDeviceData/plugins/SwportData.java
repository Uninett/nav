package no.ntnu.nav.getDeviceData.plugins;

import java.util.ArrayList;

public class SwportData implements Comparable
{
	public static final char PORT_LINK_YES = 'y';
	public static final char PORT_LINK_NO = 'n';
	public static final char PORT_LINK_DOWN = 'd';

	int swportid;

	String port;
	Integer portI;
	String ifindex;

	char link;
	String speed;
	char duplex;
	String media = "";
	boolean trunk;
	String portname = "";

	int vlan = 0;
	ArrayList vlanList;

	String hexstring;

	public SwportData(String port, String ifindex)
	{
		this.port = port.trim();
		this.portI = new Integer(this.port);
		this.ifindex = ifindex.trim();

		this.link = PORT_LINK_DOWN;
		this.speed = "";
		this.trunk = false;
	}

	public SwportData(String port, String ifindex, char link, String speed, char duplex, String media, boolean trunk, String portname)
	{
		this.port = port.trim();
		this.portI = new Integer(this.port);
		this.ifindex = ifindex.trim();

		this.link = link;
		this.speed = speed.trim();
		this.duplex = duplex;
		if (media != null) this.media = media.trim();
		setTrunk(trunk);
		if (portname != null) this.portname = portname.trim();
	}

	public int getSwportid() { return swportid; }
	public String getSwportidS() { return String.valueOf(swportid); }
	public void setSwportid(int i) { swportid = i; }
	public void setSwportid(String s) { swportid = Integer.parseInt(s); }

	public String getPort() { return port; }
	public Integer getPortI() { return portI; }
	public String getPortS() { return ((port.length()==1)?" ":"")+getPort(); }

	public String getIfindex() { return ifindex; }
	public String getIfindexS() { return ((ifindex.length()==1)?" ":"")+getIfindex(); }

	public char getLink() { return link; }

	public String getSpeed() { return speed; }
	public char getDuplex() { return duplex; }
	public String getDuplexS() { return String.valueOf(duplex); }
	public String getMedia() { return media; }
	public boolean getTrunk() { return trunk; }
	public String getTrunkS() { return trunk?"t":"f"; }
	public String getPortname() { return portname; }

	public void setLink(char c) { link = c; }
	public void setSpeed(String s) { speed = s.trim(); }
	public void setDuplex(char c) { duplex = c; }
	public void setMedia(String s) { media = s.trim(); }
	public void setTrunk(boolean b) {
		trunk = b;
		if (trunk && vlanList == null) vlanList = new ArrayList();
	}
	public void setPortname(String s) { portname = s.trim(); }

	public int getVlan() { return vlan; }
	public void setVlan(int i) { vlan = i; }

	public void addTrunkVlan(String vlan) {
		if (!trunk) return;
		vlanList.add(vlan);
	}

	public String getHexstring() {
		if (hexstring == null) hexstring = getVlanAllowHexString();
		return hexstring;
	}
	public void setHexstring(String s) { hexstring = s; }

	public String getVlanAllowHexString()
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
		if (o instanceof SwportData) {
			SwportData sd = (SwportData)o;
			return (port.equals(sd.port) &&
					ifindex.equals(sd.ifindex) &&
					link == sd.link &&
					speed.equals(sd.speed) &&
					duplex == sd.duplex &&
					media.equals(sd.media) &&
					trunk == sd.trunk &&
					portname.equals(sd.portname));
		}
		return false;
	}

	public int compareTo(Object o) {
		SwportData pd = (SwportData)o;
		return new Integer(port).compareTo(new Integer(pd.getPort()));
	}
	public String toString() { return getPortS()+": Ifindex: " + getIfindexS() + " Link: " + getLink() + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media; }
}
