import java.util.*;

import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.NetboxUpdatable;

public class NetboxImpl implements Netbox, NetboxUpdatable
{
	private int netboxid;
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

	// Shared
	Type t;

	// Maps a OID key to the next scheduled run, in absolute time
	private Map oidNextRunMap;

	// Maps a key to OID
	private Map oidMap;

	NetboxImpl() {
		nextRun = System.currentTimeMillis();
	}

	public int getNetboxid() { return netboxid; }
	public String getNetboxidS() { return String.valueOf(netboxid); }
	public void setNetboxid(String s) { netboxid = Integer.parseInt(s); }
	public void setNetboxid(int i) { netboxid = i; }

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

	// Doc in interface
	public boolean isReadyOid(String key) {
		if (!oidNextRunMap.containsKey(key)) return false;

		int nextRun = ((Integer)oidNextRunMap.get(key)).intValue();
		return (nextRun <= System.currentTimeMillis());
	}

	// Doc in interface
	public String getOid(String key) {
		return (String)oidMap.get(key);
	}

	// For scheduling purposes, do not use
	long nextRun() { return nextRun; }

	// For scheduling purposes, do not use
	void nextRun(long l) { nextRun = l; }

	// For scheduling purposes, do not use
	boolean removed() { return removed; }

	// For scheduling purposes, do not use
	void removed(boolean b) { removed = b; }


}
