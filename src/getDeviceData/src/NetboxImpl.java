import java.util.*;

import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.NetboxUpdatable;

public class NetboxImpl implements Netbox, NetboxUpdatable
{
	private int netboxNum;
	private int netboxid;
	private String ip;
	private String cs_ro;
	private String type;
	private String sysName;
	private String cat;
	private int snmpMajor;
	private String snmpagent;

	private boolean removed;

	// Shared
	Type t;

	private long baseTime;

	// Maps an OID key to the next scheduled run, in absolute time
	private Map oidNextRunMap;

	// Run queue
	private SortedMap oidRunQ;

	// List of oidkeys to be rescheduled
	private List rescheduleList = new ArrayList();

	NetboxImpl(int netboxNum, Type t) {
		this.netboxNum = netboxNum;
		setType(t);
	}

	public int getNum() { return netboxNum; }

	public int getNetboxid() { return netboxid; }
	public String getNetboxidS() { return String.valueOf(netboxid); }
	public void setNetboxid(String s) { netboxid = Integer.parseInt(s); }
	public void setNetboxid(int i) { netboxid = i; }

	public String getIp() { return ip; }
	public void setIp(String s) { ip = s; }

	public String getCommunityRo() { return cs_ro; }
	public void setCommunityRo(String s) { cs_ro = s; }

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

	Type getTypeT() {
		return t;
	}

	void setType(Type t) {
		this.t = t;
		updateNextRun();
	}

	void updateNextRun() {
		Map m = new HashMap();
		SortedMap sm = new TreeMap();
		Long baseTime = new Long(System.currentTimeMillis());

		Set s = new HashSet();
		for (Iterator it = t.getKeyFreqMapIterator(); it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			String oidkey = (String)me.getKey();
			m.put(oidkey, baseTime);
			s.add(oidkey);
		}
		if (!s.isEmpty()) sm.put(baseTime, s);

		oidRunQ = sm;
		oidNextRunMap = m;
	}
	
	// Doc in interface
	public boolean isSupportedOids(String[] oidkeys) {
		for (Iterator it = Arrays.asList(oidkeys).iterator(); it.hasNext();) {
			String oidkey = (String)it.next();
			if (oidNextRunMap.containsKey(oidkey)) return true;
		}
		return false;
	}

	// Doc in interface
	public boolean canGetOid(String key) {
		if (!oidNextRunMap.containsKey(key)) return false;

		long nextRun = ((Long)oidNextRunMap.get(key)).longValue();
		if (nextRun <= System.currentTimeMillis()) {
			rescheduleList.add(key);
			return true;
		}
		return false;
	}

	// Doc in interface
	public String getOid(String key) {
		return t.getOid(key);
	}

	// Next run for this Netbox
	long getNextRun() {
		if (oidRunQ.isEmpty()) return Long.MAX_VALUE;
		return ((Long)oidRunQ.firstKey()).longValue();
	}

	// Processing done, reschedule requested oids
	void reschedule() {
		long curTime = System.currentTimeMillis();
		if (baseTime == 0) baseTime = curTime; // Set baseTime on first reschedule
		long d = curTime - baseTime;

		String oidkey;
		while ((oidkey = removeRunQHead()) != null) {
			// Freq is in seconds, convert to milliseconds
			long freq = t.getFreq(oidkey);
			freq *= 1000;

			// Calculate time of next run.
			//
			// nextRun = baseTime + X * freq
			//
			// where X is an integer such that nextRun >= curTime.
			long nextRun = baseTime + d / freq * freq + freq;

			addToRunQ(oidkey, new Long(nextRun));
			oidNextRunMap.put(oidkey, new Long(nextRun));
		}
		rescheduleList.clear();
	}

	private String removeRunQHead() {
		if (oidRunQ.isEmpty()) return null;

		Long nextRun = (Long)oidRunQ.firstKey();
		if (nextRun.longValue() > System.currentTimeMillis()) return null;

		Set s = (Set)oidRunQ.get(nextRun);
		Iterator it = s.iterator();
		String oidkey = (String)it.next();
		it.remove();
		if (s.isEmpty()) oidRunQ.remove(nextRun);
		return oidkey;
	}

	private void addToRunQ(String oidkey, Long nextRun) {
		Set s;
		if ( (s = (Set)oidRunQ.get(nextRun)) == null) oidRunQ.put(nextRun, s = new HashSet());
		s.add(oidkey);
	}

	// Currently not in use
	private void removeFromRunQ(String oidkey) {
		Long oidNextRun = (Long)oidNextRunMap.get(oidkey);
		Set s = (Set)oidRunQ.get(oidNextRun);
		s.remove(oidkey);
		if (s.isEmpty()) oidRunQ.remove(oidNextRun);		
	}

	// Return if this netbox is removed
	boolean isRemoved() { return removed; }

	// Remove this netbox
	void remove() { removed = true; }

	public String toString() {
		return "Netbox: " + getSysname();
	}
	

}
