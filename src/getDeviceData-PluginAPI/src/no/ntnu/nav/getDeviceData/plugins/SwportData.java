package no.ntnu.nav.getDeviceData.plugins;

import java.util.ArrayList;

public class SwportData implements Comparable
{
	String ifindex;
	String modul;
	String port;

	String status;
	String speed;
	String duplex;
	String media;
	boolean trunk;
	String portnavn;

	int vlan = 0;
	ArrayList vlanList;

	public SwportData(String ifindex, String modul, String port)
	{
		this.ifindex = ifindex.trim();
		this.modul = modul.trim();
		this.port = port.trim();

		this.status = "";
		this.speed = "";
		this.duplex = "";
		this.media = "";
		this.trunk = false;
		this.portnavn = "";
	}

	public SwportData(String ifindex, String modul, String port, String status, String speed, String duplex, String media, boolean trunk, String portnavn)
	{
		this.ifindex = ifindex.trim();
		this.modul = modul.trim();
		this.port = port.trim();

		setStatus(status);
		this.speed = speed.trim();
		this.duplex = duplex.trim();
		this.media = media.trim();
		setTrunk(trunk);
		this.portnavn = portnavn.trim();

	}

	public String getIfindex() { return ifindex; }
	public String getIfindexS() { return ((ifindex.length()==1)?" ":"")+getIfindex(); }

	public String getModul() { return modul; }
	public String getModulS() { return ((modul.length()==1)?" ":"")+getModul(); }

	public String getPort() { return port; }
	public String getPortS() { return ((port.length()==1)?" ":"")+getPort(); }

	public String getStatus() { return status; }
	public String getStatusS() { return ((status.length()==2)?"  ":"")+status; }

	public String getSpeed() { return speed; }
	public String getDuplex() { return duplex; }
	public String getMedia() { return media; }
	public boolean getTrunk() { return trunk; }
	public String getTrunkS() { return trunk?"t":"f"; }
	public String getPortnavn() { return portnavn; }

	public void setStatus(String s) { status = s.trim(); }
	public void setSpeed(String s) { speed = s.trim(); }
	public void setDuplex(String s) { duplex = s.trim(); }
	public void setMedia(String s) { media = s.trim(); }
	public void setTrunk(boolean b) {
		trunk = b;
		if (trunk && vlanList == null) vlanList = new ArrayList();
	}
	public void setPortnavn(String s) { portnavn = s.trim(); }

	public int getVlan() { return vlan; }
	public void setVlan(int i) { vlan = i; }

	public void addTrunkVlan(String vlan) {
		if (!trunk) return;
		vlanList.add(vlan);
	}

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

	public int compareTo(Object o) {
		SwportData pd = (SwportData)o;
		if (modul.equals(pd.getModul())) {
			return new Integer(port).compareTo(new Integer(pd.getPort()));
		}
		return new Integer(modul).compareTo(new Integer(pd.getModul()));
	}
	public String toString() { return getIfindexS()+" "+getModulS()+"/"+getPortS()+": Status: " + getStatusS() + " Speed: " + speed + " Duplex: " + duplex + " Media: " + media; }
}
