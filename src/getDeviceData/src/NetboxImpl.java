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
	//private String type;
	private String sysName;
	private String cat;
	private int snmpMajor;
	private String snmpagent;
	private int numInStack;

	private boolean uptodate;

	private boolean removed;
	private boolean updateNetboxes;
	private boolean recreate;

	// Maps an OID key to frequency in seconds
	private Map keyFreqMap;

	// Maps an OID key to Snmpoid
	private Map keyMap;

	private Map reschedulesMap;
	private Map numberStoreMap;

	// Shared
	Type t;

	private long baseTime;

	// Maps an OID key to the next scheduled run, in absolute time
	private Map oidNextRunMap;

	// Run queue
	private SortedMap oidRunQ;

	NetboxImpl(int netboxNum, Type t, Map keyFreqMap, Map keyMap) {
		this.netboxNum = netboxNum;
		oidRunQ = Collections.synchronizedSortedMap(new TreeMap());
		oidNextRunMap = Collections.synchronizedMap(new HashMap());
		this.t = t;
		this.keyFreqMap = keyFreqMap;
		this.keyMap = keyMap;
		numberStoreMap = Collections.synchronizedMap(new HashMap());
		reschedulesMap = Collections.synchronizedMap(new HashMap());
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

	/*
	public String getType() { return type; }
	public void setType(String s) { type = s; }
	*/

	public String getType() { return t.getTypename(); }
	//public void setType(String s) { type = s; }

	public String getSysname() { return sysName; }
	public void setSysname(String s) { sysName = s; }

	public String getCat() { return cat; }
	public void setCat(String s) { cat = s; }

	public int getSnmpMajor() { return snmpMajor; }
	public void setSnmpMajor(int i) { snmpMajor = i; }

	public String getSnmpagent() { return snmpagent; }
	public void setSnmpagent(String s) { snmpagent = s; }

	public boolean getUptodate() { return uptodate; }
	public void setUptodate(boolean b) { uptodate = b; }

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
		scheduleAllOids(0);
	}

	void scheduleAllOids(long delay) {
		synchronized (oidRunQ) {
			oidRunQ.clear();
			oidNextRunMap.clear();
			updateNextRun(delay);
		}
	}

	void updateNextRun() {
		updateNextRun(0);
	}

	void updateNextRun(long delay) {
		Set r = new HashSet();
		r.addAll(oidNextRunMap.keySet());

		for (Iterator it = keyFreqMap.entrySet().iterator(); it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			String oidkey = (String)me.getKey();
			r.remove(oidkey);
			if (!oidNextRunMap.containsKey(oidkey)) {
				// Schedule immediately
				addToRunQ(oidkey, new Long(delay));
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
	public void scheduleOid(String oidkey, long delay) {
		delay *= 1000;
		Long l;
		if ((l=(Long)reschedulesMap.get(oidkey)) != null) {
			if (l.longValue() < delay) return;
		}
		reschedulesMap.put(oidkey, new Long(delay));
	}

	// Doc in interface
	public void set(String k, int n) {
		numberStoreMap.put(k, new Integer(n));
	}

	// Doc in interface
	public int get(String k) {
		if (!numberStoreMap.containsKey(k)) return - (1 << 28);
		return ((Integer)numberStoreMap.get(k)).intValue();
	}


	void addSnmpoid(int freq, Snmpoid snmpoid) {
		String oidkey = snmpoid.getOidkey();
		keyFreqMap.put(oidkey, new Integer(freq));
		keyMap.put(oidkey, snmpoid);
		if (!oidNextRunMap.containsKey(oidkey)) {
			// Schedule this OID immediately
			addToRunQ(oidkey, new Long(0));
		}
	}

	// Doc in interface
	public String getOid(String key) {
		if (canGetOid(key)) {
			return getOidNoCheck(key);
		}
		return null;
	}

	int getFreq(String key) {
		return ((Integer)keyFreqMap.get(key)).intValue();
	}

	public String getOidNoCheck(String key) {
		Snmpoid snmpoid = (Snmpoid)keyMap.get(key);
		return snmpoid == null ? null : snmpoid.getSnmpoid();
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

	private void integrateReschedules(long curTime) {
		for (Iterator it=reschedulesMap.entrySet().iterator();it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			String oidkey = (String)me.getKey();
			long delay = ((Long)me.getValue()).longValue()+curTime;
			if (oidkey == null) {
				scheduleAllOids(delay);
			} else {
				removeFromRunQ(oidkey);
				addToRunQ(oidkey, new Long(delay));
			}
		}
		reschedulesMap.clear();
	}

	// Processing done, reschedule requested oids
	void reschedule() {
		long curTime = System.currentTimeMillis();
		if (baseTime == 0) baseTime = curTime; // Set baseTime on first reschedule
		long d = curTime - baseTime;
		
		integrateReschedules(curTime);

		String oidkey;
		while ((oidkey = removeRunQHead()) != null) {
			// Freq is in seconds, convert to milliseconds
			long freq = getFreq(oidkey);
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

	private void removeFromRunQ(String oidkey) {
		Long oidNextRun = (Long)oidNextRunMap.get(oidkey);
		Set s = (Set)oidRunQ.get(oidNextRun);
		s.remove(oidkey);
		if (s.isEmpty()) oidRunQ.remove(oidNextRun);		
	}

	void printSchedule() {
		System.err.println("sysName: " + toString());
		System.err.println("needUpdateNetboxes: " + needUpdateNetboxes());
		System.err.println("needRecreate: " + needRecreate());
		System.err.println("isRemoved: " + isRemoved());
		System.err.println("nextRun: " + getNextRun());
		SortedMap tm = new TreeMap();
		long curTime = System.currentTimeMillis();
		for (Iterator it=oidNextRunMap.entrySet().iterator();it.hasNext();) {
			Map.Entry me = (Map.Entry)it.next();
			long l = ((Long)me.getValue()).longValue()-curTime;
			if (l < 0) l = 0;
			tm.put(me.getKey(), new Long(l));
		}
		System.err.println("nextRunMap: " + tm);
		System.err.println("oidRunQ: " + oidRunQ);
		System.err.println("currentTime: " + System.currentTimeMillis());
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

	public String getKey() {
		return getNetboxidS();
	}

	public String toString() {
		return getSysname();
	}
	

}
