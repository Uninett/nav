import java.util.*;

import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.NetboxUpdatable;

public class NetboxImpl implements Netbox, NetboxUpdatable
{
	private int netboxNum;
	private int deviceid;
	private int netboxid;
	private String ip;
	private String cs_ro;
	private String type;
	private String sysName;
	private String cat;
	private int snmpMajor;
	private String snmpagent;
	private int numInStack;

	private boolean removed;
	private boolean updateNetboxes;
	private boolean recreate;

	// Shared
	Type t;

	private long baseTime;

	// Maps an OID key to the next scheduled run, in absolute time
	private Map oidNextRunMap;

	// Run queue
	private SortedMap oidRunQ;

	NetboxImpl(int netboxNum, Type t) {
		this.netboxNum = netboxNum;
		oidRunQ = Collections.synchronizedSortedMap(new TreeMap());
		oidNextRunMap = Collections.synchronizedMap(new HashMap());
		setType(t);
	}

	public int getNum() { return netboxNum; }

	public int getDeviceid() { return deviceid; }
	public void setDeviceid(int i) { deviceid = i; }

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

	public void setNumInStack(int numInStack) { this.numInStack = numInStack; }

	public String getTypeid() { return t.getTypeid(); }

	Type getTypeT() {
		return t;
	}

	void setType(Type t) {
		this.t = t;
		updateNextRun();
	}

	void scheduleImmediately() {
		synchronized (oidRunQ) {
			oidRunQ.clear();
			oidNextRunMap.clear();
			updateNextRun();
		}
	}

	void updateNextRun() {
		Set r = new HashSet();
		r.addAll(oidNextRunMap.keySet());

		for (Iterator it = t.getKeyFreqMapIterator(); it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			String oidkey = (String)me.getKey();
			r.remove(oidkey);
			if (!oidNextRunMap.containsKey(oidkey)) {
				// Schedule immediately
				addToRunQ(oidkey, new Long(0));
			}
		}

		// Remove oidkeys no longer supported
		for (Iterator it = r.iterator(); it.hasNext();) {
			removeFromRunQ((String)it.next());
		}
		oidNextRunMap.keySet().removeAll(r);
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
	public boolean isSupportedAllOids(String[] oidkeys) {
		for (Iterator it = Arrays.asList(oidkeys).iterator(); it.hasNext();) {
			String oidkey = (String)it.next();
			if (!oidNextRunMap.containsKey(oidkey)) return false;
		}
		return true;
	}

	// Doc in interface
	public Set oidsNotSupported(String[] oidkeys) {
		Set s = new HashSet();
		for (Iterator it = Arrays.asList(oidkeys).iterator(); it.hasNext();) {
			String oidkey = (String)it.next();
			if (!oidNextRunMap.containsKey(oidkey)) s.add(oidkey);
		}
		return s;
	}

	// Doc in interface
	public boolean canGetOid(String key) {
		if (!oidNextRunMap.containsKey(key)) return false;

		long nextRun = ((Long)oidNextRunMap.get(key)).longValue();
		if (nextRun <= System.currentTimeMillis()) {
			return true;
		}
		return false;
	}

	// Doc in interface
	public String getOid(String key) {
		if (canGetOid(key)) {
			return t.getOid(key);
		}
		return null;
	}

	// Doc in interface
	public int getNumInStack() {
		return numInStack;
	}

	// Next run for this Netbox
	long getNextRun() {
		if (oidRunQ.isEmpty()) return Long.MAX_VALUE / 2; // Infinity...
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
		}
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
		oidNextRunMap.put(oidkey, nextRun);
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

	boolean needUpdateNetboxes() { return updateNetboxes; }

	boolean needRecreate() { return recreate; }

	public void recreate() {
		recreate = true;
	}

	public void remove(boolean updateNetboxes) {
		this.updateNetboxes = updateNetboxes;
		remove();
	}

	public String toString() {
		return "Netbox: " + getSysname();
	}
	

}
