
import no.ntnu.nav.getDeviceData.plugins.BoksData;

public class BoksDataImpl implements BoksData
{
	private String boksid;
	private String ip;
	private String cs_ro;
	private String boksTypegruppe;
	private String boksType;
	private String sysName;
	private String kat;
	private int snmpMajor;
	private long nextRun;
	private boolean removed;

	public BoksDataImpl() {
		nextRun = System.currentTimeMillis();
	}

	public String getBoksid() { return boksid; }
	public void setBoksid(String s) { boksid = s; }

	public String getIp() { return ip; }
	public void setIp(String s) { ip = s; }

	public String getCommunityRo() { return cs_ro; }
	public void setCommunityRo(String s) { cs_ro = s; }

	public String getTypegruppe() { return boksTypegruppe; }
	public void setTypegruppe(String s) { boksTypegruppe = s; }

	public String getType() { return boksType; }
	public void setType(String s) { boksType = s; }

	public String getSysname() { return sysName; }
	public void setSysname(String s) { sysName = s; }

	public String getKat() { return kat; }
	public void setKat(String s) { kat = s; }

	public int getSnmpMajor() { return snmpMajor; }
	public void setSnmpMajor(int i) { snmpMajor = i; }

	/** For scheduling purposes, do not use */
	public long nextRun() { return nextRun; }
	/** For scheduling purposes, do not use */
	public void nextRun(long l) { nextRun = l; }

	/** For scheduling purposes, do not use */
	public boolean removed() { return removed; }
	/** For scheduling purposes, do not use */
	public void removed(boolean b) { removed = b; }


}
