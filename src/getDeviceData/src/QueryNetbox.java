import java.io.*;
import java.util.*;
import java.util.jar.*;
import java.net.*;
import java.text.*;

import java.sql.*;

import no.ntnu.nav.logger.*;
import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.SimpleSnmp.*;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.deviceplugins.*;

/**
 * This class schedules the netboxes, assigns them to threads and runs
 * the plugins.
 */

public class QueryNetbox extends Thread
{
	private static ConfigParser navCp;
	private static Map dataClassMap, deviceClassMap;

	private static Timer timer;
	private static Timer updateDataTimer;
	private static int updateDataInterval;
	private static CheckRunQTask checkRunQTask;
	private static UpdateDataTask updateDataTask;

	private static Map typeidMap;
	private static Map oidkeyMap;
	private static SortedMap nbRunQ;
	private static Stack idleThreads;
	private static Map nbMap;

	private static LinkedList oidQ;

	private static int maxThreadCnt;
	private static int threadCnt;
	private static Integer idleThreadLock = new Integer(0);
	private static int netboxCnt;
	private static long nbProcessedCnt;

	private static String qNetbox;

	// Plugins

	// Caches which device handlers can handle a given Netbox
	static Map deviceNetboxCache = Collections.synchronizedMap(new HashMap());

	// Stores the persistent storage for the dataplugins
	static Map persistentStorage = Collections.synchronizedMap(new HashMap());

	// Object data
	String tid;
	NetboxImpl nb;
	Object oidUpdObj;

	// Static init
	public static void init(int numThreads, int updateDataIntervalI, ConfigParser cp, Map dataCM, Map deviceCM, String qnb) {
		maxThreadCnt = numThreads;
		updateDataInterval = updateDataIntervalI;
		navCp = cp;
		dataClassMap = dataCM;
		deviceClassMap = deviceCM;
		qNetbox = qnb;

		// Create the netbox map and the run queue
		nbMap = new HashMap();
		nbRunQ = new TreeMap();
		oidQ = new LinkedList();

		timer = new Timer();
		updateDataTimer = new Timer();

		// Fetch from DB
		updateTypes(false);
		updateNetboxes();

		// Schedule fetch updates
		Log.d("INIT", "Starting timer for data updating");
		scheduleUpdateNetboxes(updateDataInterval);

		Log.d("INIT", "Starting timer for netbox query scheduling");
		scheduleCheckRunQ(0);

	}

	private static void scheduleUpdateNetboxes(long l) {
		synchronized (updateDataTimer) {
			if (updateDataTask != null) updateDataTask.cancel();
			updateDataTask = new UpdateDataTask();
			updateDataTimer.schedule(updateDataTask, l, updateDataInterval);
			Log.d("QUERY_NETBOX", "SCHEDULE_UPDATE_NETBOXES", "Schedule for immediate execution");
		}
	}

	private static void createUnknownType(Map typeidMapL) {
		// The unknown type is used for netboxes with missing type and only supports the 'typeoid' oidkey
		String typeid = Type.UNKNOWN_TYPEID;
		String typename = "unknownType";
		String vendorid = "unknownVendor";
		int csAtVlan = Type.CS_AT_VLAN_UNKNOWN;
		boolean uptodate = true;
		Map keyFreqMap = new HashMap();
		Map keyMap = new HashMap();

		// Add the 'typeoid' oidkey
		try {
			ResultSet rs = Database.query("SELECT snmpoidid, oidkey, snmpoid, getnext, decodehex, match_regex, uptodate FROM snmpoid WHERE oidkey='typeoid'");
			rs.next();
			keyFreqMap.put(rs.getString("oidkey"), new Integer(Integer.MAX_VALUE));

			Snmpoid snmpoid = new Snmpoid(rs.getString("snmpoidid"), rs.getString("oidkey"), rs.getString("snmpoid"), rs.getBoolean("getnext"), rs.getBoolean("decodehex"), rs.getString("match_regex"), rs.getBoolean("uptodate"));
			keyMap.put(rs.getString("oidkey"), snmpoid);

		} catch (SQLException e) {
			Log.w("QUERY_NETBOX", "CREATE_UNKNOWN_NETBOX", "Missing typeoid from snmpoid, cannot update types!");
			Log.d("QUERY_NETBOX", "CREATE_UNKNOWN_NETBOX", "SQLException: " + e.getMessage());
			return;
		}

		Type t = new Type(typeid, typename, vendorid, csAtVlan, uptodate, keyFreqMap, keyMap);
		typeidMapL.put(typeid, t);

	}

	private static void scheduleCheckRunQ(long l)
	{
		synchronized (timer) {
			if (checkRunQTask != null) checkRunQTask.cancel();
			checkRunQTask = new CheckRunQTask();
			// Eh.. make sure we don't schedule anything negative =)
			// If this happens it is a bug and should be fixed!
			//l = Math.max(l, 0);
			Log.d("QUERY_NETBOX", "SCHEDULE_CHECK_RUN_Q", "Schedule in " + l + " ms");
			timer.schedule(checkRunQTask, l);
		}
	}

	private static void checkRunQ()
	{
		Log.setDefaultSubsystem("QUERY_NETBOX");

		// First we check if the OID database needs updating
		synchronized (oidQ) {
			while (!oidQ.isEmpty()) {
				Object updateO = oidQ.removeFirst();
				Log.d("CHECK_RUN_Q", "oidQ not empty, got: " + updateO);

				// Try to get a free thread
				String tid = requestThread();
				if (tid == null) {
					Log.d("CHECK_RUN_Q", "oidQ not empty, but to thread available");
					oidQ.addFirst(updateO);
					return;
				}

				// OK, start a new QueryNetbox
				Log.d("CHECK_RUN_Q", "Starting new OID thread with id: " + tid);
				new QueryNetbox(tid, updateO).start();
			}
		}
		
		// Try to get a free netbox
		Object o;
		while ((o = removeRunQHead()) instanceof NetboxImpl) {
			NetboxImpl nb = (NetboxImpl)o;

			Log.d("CHECK_RUN_Q", "Got netbox: " + nb);

			// Try to get a free thread
			String tid = requestThread();
			if (tid == null) {
				Log.d("CHECK_RUN_Q", "Netbox is available, but no threads are idle");
				// Re-insert into queue
				addToRunQFront(nb);
				return;
			}

			// OK, start a new QueryNetbox
			Log.d("CHECK_RUN_Q", "Starting new Netbox thread with id: " + tid);
			new QueryNetbox(tid, nb).start();

		} 

		// No more free netboxes, schedule re-run when the next is ready
		Long nextRun = (Long)o;
		Log.d("CHECK_RUN_Q", "No available netbox, scheduling next check in " + nextRun + " ms");			
		scheduleCheckRunQ(nextRun.longValue());

	}

	public static synchronized void updateTypes(boolean updateNetboxes) {
		Map typeidM = new HashMap();
		Map oidkeyM = new HashMap();

		// The unknown type is for netboxes without type
		createUnknownType(typeidM);

		// First fetch new types from the database
		try {
			ResultSet rs = Database.query("SELECT typeid, typename, vendorid, type.frequency AS typefreq, cs_at_vlan, type.uptodate, typesnmpoid.frequency AS oidfreq, snmpoidid, oidkey, snmpoid, getnext, decodehex, match_regex, snmpoid.uptodate AS oiduptodate FROM type LEFT JOIN typesnmpoid USING(typeid) LEFT JOIN snmpoid USING(snmpoidid) ORDER BY typeid");
			String prevtypeid = null;
			//boolean prevuptodate;
			//boolean dirty = false;
			//Map keyFreqMap = new HashMap(), keyMap = new HashMap();
			Type t = null;
			Map keyFreqMap = null, keyMap = null;

			synchronized (oidQ) {
				oidQ.clear();
			}

			while (rs.next()) {
				String typeid = rs.getString("typeid");

				if (!typeid.equals(prevtypeid)) {
					keyFreqMap = new HashMap();
					keyMap = new HashMap();
					String typename = rs.getString("typename");
					int csAtVlan = rs.getString("cs_at_vlan") == null ? Type.CS_AT_VLAN_UNKNOWN : Type.csAtVlan(rs.getBoolean("cs_at_vlan"));
					boolean uptodate = rs.getBoolean("uptodate");

					t = new Type(typeid, typename, rs.getString("vendorid"), csAtVlan, uptodate, keyFreqMap, keyMap);
					if (!uptodate) synchronized (oidQ) { oidQ.add(t); }
					typeidM.put(typeid, t);
				}
					
				if (rs.getBoolean("oiduptodate")) {
					String snmpoidid = rs.getString("snmpoidid");
					String oidkey = rs.getString("oidkey");
					String oid = rs.getString("snmpoid");
					boolean getnext = rs.getBoolean("getnext");
					boolean decodehex = rs.getBoolean("decodehex");
					String matchRegex = rs.getString("match_regex");
					boolean oiduptodate = rs.getBoolean("oiduptodate");
				
					Snmpoid snmpoid;
					if ( (snmpoid=(Snmpoid)oidkeyM.get(oidkey)) == null) {
						oidkeyM.put(oidkey, snmpoid = new Snmpoid(snmpoidid, oidkey, oid, getnext, decodehex, matchRegex, oiduptodate));
						/*
						if (!oiduptodate && t.getUptodate()) {
							synchronized (oidQ) { oidQ.add(snmpoid); }
							t.setDirty(true);
						}
						*/
					}
					//snmpoid.addType(t);

					boolean oidfreq = (rs.getString("oidfreq") != null && rs.getString("oidfreq").length() > 0);
					int freq = oidfreq ? rs.getInt("oidfreq") : rs.getInt("typefreq");
					if (freq == 0) {
						Log.w("UPDATE_TYPES", "No frequency specified for type " + typeid + ", oid: " + rs.getString("oidkey") + ", skipping.");
						prevtypeid = typeid;
						//prevuptodate = uptodate;
						continue;
					}
					keyFreqMap.put(rs.getString("oidkey"), new Integer(freq));
					keyMap.put(rs.getString("oidkey"), snmpoid);
				} else if (rs.getString("snmpoidid") != null) {
					t.setDirty(true);
				}
				prevtypeid = typeid;
				//prevuptodate = uptodate;
			}
			//typeidM.put(prevtypeid, new Type(prevtypeid, keyFreqMap, keyMap));

			// Now check all non-uptodate OIDs
			rs = Database.query("SELECT snmpoidid, oidkey, snmpoid, getnext, decodehex, match_regex, snmpoid.uptodate AS oiduptodate FROM snmpoid WHERE uptodate = 'f' OR snmpoidid NOT IN (SELECT snmpoidid FROM typesnmpoid)");
			while (rs.next()) {
				String snmpoidid = rs.getString("snmpoidid");
				String oidkey = rs.getString("oidkey");
				String oid = rs.getString("snmpoid");
				boolean getnext = rs.getBoolean("getnext");
				boolean decodehex = rs.getBoolean("decodehex");
				String matchRegex = rs.getString("match_regex");
				boolean oiduptodate = rs.getBoolean("oiduptodate");
				
				Snmpoid snmpoid = new Snmpoid(snmpoidid, oidkey, oid, getnext, decodehex, matchRegex, oiduptodate);
				oidkeyM.put(oidkey, snmpoid);
				if (!oiduptodate) synchronized (oidQ) { oidQ.add(snmpoid); }

			}

			// Make new types global
			typeidMap = typeidM;
			oidkeyMap = oidkeyM;

			Log.i("UPDATE_TYPES", "Num types: " + typeidMap.size() + ", num OIDs: " + oidkeyMap.size());

			// Then update all netboxes with the new types
			if (updateNetboxes) updateNetboxesWithNewTypes();

		} catch (SQLException e) {
			Log.e("UPDATE_TYPES", "SQLException: " + e);			
		}
	}

	private static synchronized void updateNetboxesWithNewTypes() {
		for (Iterator it = nbMap.values().iterator(); it.hasNext();) {
			NetboxImpl nb = (NetboxImpl)it.next();
			Type t = (Type)typeidMap.get(nb.getTypeT().getTypeid());
			nb.setType(t);
			if (t.getDirty()) {
				synchronized (deviceNetboxCache) {
					deviceNetboxCache.remove(nb.getNetboxidS());
				}
				t.setDirty(false);
			}
		} 
	}

	public static synchronized void updateNetboxes() {
		int newcnt=0, skipcnt=0, delcnt=0;

		try {
			Map numInStackMap = new HashMap();
			ResultSet rs = Database.query("SELECT netboxid,COUNT(*) AS numInStack FROM module GROUP BY netboxid HAVING COUNT(*) > 1");
			while (rs.next()) numInStackMap.put(rs.getString("netboxid"), rs.getString("numInStack"));

			String sql = "SELECT ip,ro,deviceid,netboxid,catid,sysname,typeid,typename FROM netbox LEFT JOIN type USING(typeid) WHERE up='y'";
			if (qNetbox != null) sql += " AND sysname LIKE '"+qNetbox+"'";
			sql += " ORDER BY random() * netboxid";
			//sql += " LIMIT 1000";
			rs = Database.query(sql);

			int nbCnt = netboxCnt;
			Set netboxidSet = new HashSet();
			while (rs.next()) {
				String netboxid = rs.getString("netboxid");
				String typeid = rs.getString("typeid");
				if (typeid == null) typeid = Type.UNKNOWN_TYPEID;
				Type t = (Type)typeidMap.get(typeid);
				if (t == null) {
					Log.d("UPDATE_NETBOXES", "Skipping netbox " + rs.getString("sysname") +
								" because type is null (probably the type doesn't have any OIDs)");
					skipcnt++;
					continue;
				}
				NetboxImpl nb;

				/*
				synchronized (nbMap) {
					if ( (nb=(NetboxImpl)nbMap.get(netboxid)) != null) {
						nb.remove();
					}
					nbMap.put(netboxid, nb = new NetboxImpl(++nbCnt, t));
				}
				*/
				boolean newNetbox = false;
				if ( (nb=(NetboxImpl)nbMap.get(netboxid)) == null) {
					nbMap.put(netboxid, nb = new NetboxImpl(++nbCnt, t));
					newNetbox = true;
					newcnt++;
				} else {
					nb.setType(t);
				}

				nb.setDeviceid(rs.getInt("deviceid"));
				nb.setNetboxid(netboxid);
				nb.setIp(rs.getString("ip"));
				nb.setCommunityRo(rs.getString("ro"));
				nb.setType(rs.getString("typename"));
				nb.setSysname(rs.getString("sysname"));
				nb.setCat(rs.getString("catid"));
				int numInStack = 1;
				if (numInStackMap.containsKey(netboxid)) numInStack = Integer.parseInt((String)numInStackMap.get(netboxid));
				nb.setNumInStack(numInStack);
					
				//nb.setSnmpMajor(rs.getInt("snmp_major"));
				//nb.setSnmpagent(rs.getString("snmpagent"));

				if (newNetbox) {
					addToRunQ(nb);
				}
				netboxidSet.add(new Integer(nb.getNetboxid()));
			}

			netboxCnt = nbCnt;

			// Remove netboxes no longer present
			for (Iterator it = nbMap.values().iterator(); it.hasNext();) {
				NetboxImpl nb = (NetboxImpl)it.next();
				if (!netboxidSet.contains(new Integer(nb.getNetboxid()))) {
					nb.remove();
					it.remove();
					delcnt++;
				}
			}

		} catch (SQLException e) {
			Log.e("UPDATE_NETBOXES", "SQLException: " + e);			
		}

		Log.i("UPDATE_NETBOXES", "Num netboxes: " + netboxCnt + " (" + newcnt + " new, " + delcnt + " removed, " + skipcnt + " skipped)");

		if (newcnt > 0) {
			scheduleCheckRunQ(0);
		}

	}

	private static void addToRunQ(NetboxImpl nb) {
		addToRunQ(nb, false);
	}

	private static void addToRunQFront(NetboxImpl nb) {
		addToRunQ(nb, true);
	}

	private static void addToRunQ(NetboxImpl nb, boolean front) {
		Long nextRun = new Long(nb.getNextRun());
		synchronized (nbRunQ) {
			LinkedList l;
			if ( (l = (LinkedList)nbRunQ.get(nextRun)) == null) nbRunQ.put(nextRun, l = new LinkedList());
			if (front) {
				l.addFirst(nb);
			} else {
				l.add(nb);
			}
		}
	}

	private static Object removeRunQHead() {
		Object o;
		while ((o = removeRunQHeadNoCheck()) instanceof NetboxImpl) {
			NetboxImpl nb = (NetboxImpl)o;
			if (nb.isRemoved()) continue;
			return nb;
		}
		return o;
	}

	private static Object removeRunQHeadNoCheck() {
		synchronized (nbRunQ) {
			if (nbRunQ.isEmpty()) return new Long(System.currentTimeMillis() + Integer.MAX_VALUE); // Infinity...

			Long nextRun = (Long)nbRunQ.firstKey();
			if (nextRun.longValue() > System.currentTimeMillis()) return new Long(nextRun.longValue() - System.currentTimeMillis());

			LinkedList l = (LinkedList)nbRunQ.get(nextRun);
			NetboxImpl nb  = (NetboxImpl)l.removeFirst();
			if (l.isEmpty()) nbRunQ.remove(nextRun);
			return nb;
		}
	}

	private static String requestThread() {
		synchronized (idleThreadLock) {
			if (threadCnt < maxThreadCnt) {
				return format(threadCnt++, String.valueOf(maxThreadCnt-1).length());
			}
			return null;
		}
	}

	private static void threadIdle() {
		synchronized (idleThreadLock) {
			threadCnt--;
		}
		scheduleCheckRunQ(0);
	}

	// Constructor
	public QueryNetbox(String tid, NetboxImpl initialNb)
	{
		this.tid = tid;
		this.nb = initialNb;
	}

	public QueryNetbox(String tid, Object oidUpdObj) {
		this.tid = tid;
		this.oidUpdObj = oidUpdObj;
	}

	public void run()
	{
		Log.setDefaultSubsystem("QUERY_NETBOX_T"+tid);

		long beginTime = System.currentTimeMillis();

		while (true) {

			// Check if we were assigned an oid object and not a netbox
			if (oidUpdObj != null) {
				OidTester oidTester = new OidTester();
				if (oidUpdObj instanceof Type) {
					oidTester.oidTest((Type)oidUpdObj, oidkeyMap.values().iterator() );
				} else if (oidUpdObj instanceof Snmpoid) {
					oidTester.oidTest((Snmpoid)oidUpdObj, typeidMap.values().iterator() );
				}
				Log.d("RUN", "Thread idle, done OID object processing, exiting...");
				threadIdle();
				return;
			}

			// Process netbox
			String netboxid = nb.getNetboxidS();
			String ip = nb.getIp();
			String cs_ro = nb.getCommunityRo();
			String type = nb.getType();
			String sysName = nb.getSysname();
			String cat = nb.getCat();
			int snmpMajor = nb.getSnmpMajor();

			SimpleSnmp sSnmp = SimpleSnmp.simpleSnmpFactory(type);
			sSnmp.setHost(ip);
			sSnmp.setCs_ro(cs_ro);

			Log.d("RUN", "Now working with("+netboxid+"): " + sysName + ", type="+type+", ip="+ip+" (device "+ nb.getNum() +" of "+ netboxCnt+")");
			long boksBeginTime = System.currentTimeMillis();

			try {

				// Get DataContainer objects from each data-plugin.
				DataContainersImpl containers = getDataContainers();

				// Find handlers for this boks
				DeviceHandler[] deviceHandler = findDeviceHandlers(nb);
				if (deviceHandler == null) {
					throw new NoDeviceHandlerException("  No device handlers found for netbox: " + netboxid + " (cat: " + cat + " type: " + type);
				}

				Log.setDefaultSubsystem("QUERY_NETBOX_T"+tid);
				Log.d("RUN", "  Found " + deviceHandler.length + " deviceHandlers for boksid: " + netboxid + " (cat: " + cat + " type: " + type);

				for (int dhNum=0; dhNum < deviceHandler.length; dhNum++) {

					try {
						deviceHandler[dhNum].handleDevice(nb, sSnmp, navCp, containers);
						if (nb.isRemoved()) break;

					} catch (TimeoutException te) {
						Log.setDefaultSubsystem("QUERY_NETBOX_T"+tid);				
						Log.d("RUN", "TimeoutException: " + te.getMessage());
						Log.w("RUN", "GIVING UP ON: " + sysName + ", typeid: " + type );
						continue;
					} catch (Exception exp) {
						Log.w("RUN", "Fatal error from devicehandler, skipping. Exception: " + exp.getMessage());
						exp.printStackTrace(System.err);
					} catch (Throwable e) {
						Log.w("RUN", "Fatal error from devicehandler, plugin is probably old and needs to be updated to new API: " + e.getMessage());
						e.printStackTrace(System.err);
					}

				}

				if (!nb.isRemoved()) {
					// Call the data handlers for all data plugins
					try { 
						containers.callDataHandlers(nb);
					} catch (Exception exp) {
						Log.w("RUN", "Fatal error from datahandler, skipping. Exception: " + exp.getMessage());
						exp.printStackTrace(System.err);
					} catch (Throwable e) {
						Log.w("RUN", "Fatal error from datahandler, plugin is probably old and needs to be updated to new API: " + e.getMessage());
						e.printStackTrace(System.err);
					}
				}
				
			} catch (NoDeviceHandlerException exp) {
				Log.d("RUN", exp.getMessage());
			}
			Log.setDefaultSubsystem("QUERY_NETBOX_T"+tid);				

			// If netbox is removed, don't add it to the RunQ
			if (!nb.isRemoved()) {
				nb.reschedule();
				
				// Insert into queue
				addToRunQ(nb);

				Log.d("RUN", "Done processing netbox " + nb);

			} else {
				Log.d("RUN", "Done, netbox is removed: " + nb);
				if (nb.needUpdateNetboxes()) scheduleUpdateNetboxes(0);
			}

			long pc = ++nbProcessedCnt;
			if ((pc % 100) == 0) {
				Log.i("RUN", "** Processed " + pc + " netboxes (" + (pc%(netboxCnt+1)) + " of " + netboxCnt + ") **");
			}

			// Try to get a new netbox to process
			Object o = removeRunQHead();
			if (o instanceof NetboxImpl) {
				nb = (NetboxImpl)o;
				Log.d("RUN", "Got new netbox: " + nb);
			} else {				
				// We didn't get a netbox; exit the thread
				break;
			}

		}

		Log.d("RUN", "Thread idle, exiting...");
		threadIdle();

	}

	private DataContainersImpl getDataContainers() {
		DataContainersImpl dcs = new DataContainersImpl();

		try {
			// Iterate over all data plugins
			synchronized (dataClassMap) {
				for (Iterator it=dataClassMap.entrySet().iterator(); it.hasNext();) {
					Map.Entry me = (Map.Entry)it.next();
					String fn = (String)me.getKey();
					Class c = (Class)me.getValue();;
					Object o = c.newInstance();
					
					DataHandler dh = (DataHandler)o;
					
					Map m;
					if ( (m = (Map)persistentStorage.get(fn)) == null) persistentStorage.put(fn,  m = Collections.synchronizedMap(new HashMap()));
					dh.init(m);

					dcs.addContainer(dh.dataContainerFactory());				
				}
			}
		} catch (InstantiationException e) {
			Log.w("GET_DATA_CONTAINERS", "GET_DATA_CONTAINERS", "Unable to instantiate handler for " + nb.getNetboxid() + ", msg: " + e.getMessage());
		} catch (IllegalAccessException e) {
			Log.w("GET_DATA_CONTAINERS", "GET_DATA_CONTAINERS", "IllegalAccessException for " + nb.getNetboxid() + ", msg: " + e.getMessage());
		}

		return dcs;		
	}

	private DeviceHandler[] findDeviceHandlers(Netbox nb) {
		try {
			synchronized (deviceNetboxCache) {
				Class[] c;
				if ( (c=(Class[])deviceNetboxCache.get(nb.getNetboxidS() )) != null) {
					DeviceHandler[] dh = new DeviceHandler[c.length];
					for (int i=0; i < c.length; i++) dh[i] = (DeviceHandler)c[i].newInstance();
					return dh;
				}
			}

			// Iterate over all known plugins to find the set of handlers to process this boks
			// Look at DeviceHandler for docs on the algorithm for selecting handlers
			TreeMap dbMap = new TreeMap();
			List alwaysHandleList = new ArrayList();
			synchronized (deviceClassMap) {

				int high = 0;
				for (Iterator it=deviceClassMap.values().iterator(); it.hasNext();) {
					Class c = (Class)it.next();
					Object o = c.newInstance();

					DeviceHandler dh = (DeviceHandler)o;
					int v;
					try {
						v = dh.canHandleDevice(nb);
					} catch (Exception e) {
						Log.w("FIND_DEVICE_HANDLERS", "FIND_DEVICE_HANDLERS", "Error from DeviceHandler " + c + ", skipping: " + e.getMessage());
						continue;
					} catch (Throwable e) {
						Log.w("FIND_DEVICE_HANDLERS", "FIND_DEVICE_HANDLERS",
									"Fatal error from DeviceHandler " + c + ", plugin is probably old and needs to be updated to new API: " + e.getMessage());
						continue;
					}
					
					if (v == DeviceHandler.ALWAYS_HANDLE) {
						alwaysHandleList.add(c);
					} else {
						if (Math.abs(v) > high) {
							if (v > high) high = v;
							dbMap.put(new Integer(Math.abs(v)), c);
						}
					}
				}

				if (!dbMap.isEmpty() || !alwaysHandleList.isEmpty()) {
					SortedMap dbSMap = dbMap.tailMap(new Integer(high));
					Class[] c = new Class[dbSMap.size() + alwaysHandleList.size()];
					
					int j=dbSMap.size()-1;
					for (Iterator i=dbSMap.values().iterator(); i.hasNext(); j--) c[j] = (Class)i.next();
					
					j = c.length - 1;
					for (Iterator i=alwaysHandleList.iterator(); i.hasNext(); j--) c[j] = (Class)i.next();
					
					synchronized (deviceNetboxCache) { deviceNetboxCache.put(nb.getNetboxidS(), c); }

					// Call ourselves; this avoids duplicating the code for instatiating objects from the classes
					return findDeviceHandlers(nb);
				}
			}
		} catch (InstantiationException e) {
			Log.w("FIND_DEVICE_HANDLERS", "FIND_DEVICE_HANDLERS", "Unable to instantiate handler for " + nb.getNetboxid() + ", msg: " + e.getMessage());
		} catch (IllegalAccessException e) {
			Log.w("FIND_DEVICE_HANDLERS", "FIND_DEVICE_HANDLERS", "IllegalAccessException for " + nb.getNetboxid() + ", msg: " + e.getMessage());
		}

		return null;
	}

	static class UpdateDataTask extends TimerTask {
		public void run() {
			Log.setDefaultSubsystem("UPDATE_DATA");		
			updateTypes(false);
			updateNetboxes();
		}
	}

	static class CheckRunQTask extends TimerTask {
		public void run() {
			Log.setDefaultSubsystem("CHECK_RUN_Q");
			checkRunQ();
		}
	}

	private static String format(long i, int n)
	{
		DecimalFormat nf = new DecimalFormat("#");
		nf.setMinimumIntegerDigits(n);
		return nf.format(i);
	}

}
