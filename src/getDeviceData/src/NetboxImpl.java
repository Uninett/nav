import no.ntnu.nav.getDeviceData.deviceplugins.Netbox;

public class NetboxImpl implements Netbox
{
	private String netboxid;
	private String ip;
	private String cs_ro;
	private String typegroup;
	private String type;
	private String sysName;
	private String cat;
	private int snmpMajor;
	private String snmpagent;
	private long nextRun;
	private boolean removed;

	public NetboxImpl() {
		nextRun = System.currentTimeMillis();
	}

	public String getNetboxid() { return netboxid; }
	public void setNetboxid(String s) { netboxid = s; }

	public String getIp() { return ip; }
	public void setIp(String s) { ip = s; }

	public String getCommunityRo() { return cs_ro; }
	public void setCommunityRo(String s) { cs_ro = s; }

	public String getTypegroup() { return typegroup; }
	public void setTypegroup(String s) { typegroup = s; }

	public String getType() { return type; }
	public void setType(String s) { type = s; }

	public String getSysname() { return sysName; }
	public void setSysname(String s) { sysName = s; }

	public String getCat() { return cat; }
	public void setCat(String s) { cat = s; }

	public int getSnmpMajor() { return snmpMajor; }
	public void setSnmpMajor(int i) { snmpMajor = i; }

	public String getSnmpagent() { return snmpagent; }
	public void setSnmpagent(String s) { snmpagent = s; }

	/** For scheduling purposes, do not use */
	public long nextRun() { return nextRun; }
	/** For scheduling purposes, do not use */
	public void nextRun(long l) { nextRun = l; }

	/** For scheduling purposes, do not use */
	public boolean removed() { return removed; }
	/** For scheduling purposes, do not use */
	public void removed(boolean b) { removed = b; }


}
