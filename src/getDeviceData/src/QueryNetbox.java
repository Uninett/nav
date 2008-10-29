import java.sql.ResultSet;
import java.sql.SQLException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.SortedMap;
import java.util.Stack;
import java.util.Timer;
import java.util.TimerTask;
import java.util.TreeMap;

import no.ntnu.nav.ConfigParser.ConfigParser;
import no.ntnu.nav.Database.Database;
import no.ntnu.nav.SimpleSnmp.SimpleSnmp;
import no.ntnu.nav.SimpleSnmp.TimeoutException;
import no.ntnu.nav.event.Event;
import no.ntnu.nav.event.EventQ;
import no.ntnu.nav.event.EventQListener;
import no.ntnu.nav.getDeviceData.Netbox;
import no.ntnu.nav.getDeviceData.dataplugins.DataHandler;
import no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler;
import no.ntnu.nav.logger.Log;
import no.ntnu.nav.netboxinfo.NetboxInfo;

/**
 * This class schedules the netboxes, assigns them to threads and runs
 * the plugins.
 */

public class QueryNetbox extends Thread
{
	private static ConfigParser navCp;
	private static ConfigParser myCp;
	private static Map dataClassMap, deviceClassMap;

	private static Timer timer;
	private static Timer updateDataTimer;
	private static int updateDataInterval;
	private static CheckRunQTask checkRunQTask;
	private static UpdateDataTask updateDataTask;

	private static Map typeidMap;
	private static Map oidkeyMap;
	private static List initialQ;
	private static SortedMap nbRunQ;
	private static Map netboxidRunQMap;
	private static Stack idleThreads;
	private static Map nbMap;
	private static List nbList;

	private static LinkedList oidQ;
	private static Set oidNetboxSet = Collections.synchronizedSet(new HashSet());
	private static Set oidKeySet = Collections.synchronizedSet(new HashSet());

	private static int maxThreadCnt;
	private static int extraThreadCnt;
	private static Map scheduleImmediatelyMap = Collections.synchronizedMap(new HashMap());
	private static int threadCnt;
	private static Integer idleThreadLock = new Integer(0);
	private static LinkedList threadIdList = new LinkedList();
	private static int curMaxTid = 0;


	private static int netboxCnt;
	private static int netboxHigh;
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
	public static void init(int numThreads, int updateDataIntervalI, ConfigParser _myCp, ConfigParser _navCp, Map dataCM, Map deviceCM, String qnb) {
		maxThreadCnt = numThreads;
		updateDataInterval = updateDataIntervalI;
		myCp = _myCp;
		navCp = _navCp;
		myCp.setObject("navCp", navCp);
		dataClassMap = dataCM;
		deviceClassMap = deviceCM;
		qNetbox = qnb;

		// Create the netbox map and the run queue
		nbMap = new HashMap();
		initialQ = Collections.synchronizedList(new ArrayList());
		nbRunQ = new TreeMap();
		nbList = new ArrayList();
		netboxidRunQMap = new HashMap();
		oidQ = new LinkedList();

		// Create the EventListener
		EventQ.init(2000);
		EventQ.addEventQListener("getDeviceData", new EventListener());

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

			// The delay can actually be negative due to inaccuracy in the Java timer
			l = Math.max(l, 0);
			Log.d("QUERY_NETBOX", "SCHEDULE_UPDATE_NETBOXES", "Schedule update netboxes in " + l + " ms");
			updateDataTimer.schedule(updateDataTask, l, updateDataInterval);
		}
	}

	private static void createUnknownType(Map typeidMapL) {
		// The unknown type is used for netboxes with missing type
		String typeid = Type.UNKNOWN_TYPEID;
		String typename = "unknownType";
		String vendorid = "unknownVendor";
		int csAtVlan = Type.CS_AT_VLAN_UNKNOWN;
		boolean chassis = true;

		Type t = new Type(typeid, typename, vendorid, csAtVlan, chassis);
		typeidMapL.put(typeid, t);

	}

	private static void addDefaultOids(Map keyFreqMap, Map keyMap) {
		String[] defOidKeys = {
			"typeoid",
			"dnscheck",
		};

		for (int i=0; i < defOidKeys.length; i++) {
			String oidkey = defOidKeys[i];
			Snmpoid snmpoid = (Snmpoid)oidkeyMap.get(oidkey);

			keyFreqMap.put(oidkey, new Integer(OidTester.DEFAULT_FREQ));
			keyMap.put(oidkey, snmpoid);
		}
	}

	/*
	// Add the given oidkey
	private static void addOid(String oidkey, Map keyFreqMap, Map keyMap) {		
		try {
			ResultSet rs = Database.query("SELECT snmpoidid, oidkey, snmpoid, getnext, decodehex, match_regex, uptodate FROM snmpoid WHERE oidkey='" + oidkey + "'");
			rs.next();
			keyFreqMap.put(rs.getString("oidkey"), new Integer(OidTester.DEFAULT_FREQ));

			Snmpoid snmpoid = new Snmpoid(rs.getString("snmpoidid"), rs.getString("oidkey"), rs.getString("snmpoid"), rs.getBoolean("getnext"), rs.getBoolean("decodehex"), rs.getString("match_regex"), rs.getBoolean("uptodate"));
			keyMap.put(rs.getString("oidkey"), snmpoid);

		} catch (SQLException e) {
			Log.w("QUERY_NETBOX", "ADD_OID", "Missing oidkey " + oidkey + " from snmpoid, cannot update types!");
			Log.d("QUERY_NETBOX", "ADD_OID", "SQLException: " + e.getMessage());
		}
	}
	*/

	private static void scheduleCheckRunQ(long l)
	{
		synchronized (timer) {
			if (checkRunQTask != null) checkRunQTask.cancel();
			checkRunQTask = new CheckRunQTask();

			// The delay can actually be negative due to inaccuracy in the Java timer
			l = Math.max(l, 0);
			Log.d("QUERY_NETBOX", "SCHEDULE_CHECK_RUN_Q", "Schedule check runq in " + l + " ms");
			try {
				timer.schedule(checkRunQTask, l);
			} catch (IllegalStateException e) {
				timer = new Timer();
				checkRunQTask = new CheckRunQTask();
				timer.schedule(checkRunQTask, l);
			}
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
				String tid = requestThread(false);
				if (tid == null) {
					Log.d("CHECK_RUN_Q", "oidQ not empty, but no thread available");
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
			String tid = requestThread(true);
			if (tid == null) {
				Log.d("CHECK_RUN_Q", "Netbox is available, but no threads are idle");
				// Re-insert into queue
				addToRunQFront(nb);
				return;
			}

			// OK, start a new QueryNetbox
			Log.d("CHECK_RUN_Q", "Starting new Netbox thread with id: " + tid + " to handle " + nb);
			new QueryNetbox(tid, nb).start();

		} 

		// No more free netboxes, schedule re-run when the next is ready
		Long nextRun = (Long)o;
		Log.d("CHECK_RUN_Q", "No available netbox, scheduling next check in " + nextRun + " ms");			
		scheduleCheckRunQ(nextRun.longValue());

	}

	public static synchronized void updateTypes(boolean updateNetboxes) {
		Map typeidM = new HashMap();
		Map oidkeyM = Collections.synchronizedMap(new HashMap());
		int oidnew=0;

		// The unknown type is for netboxes without type
		createUnknownType(typeidM);

		try {
			// First fetch new types from the database
			ResultSet rs = Database.query("SELECT typeid, typename, vendorid, cs_at_vlan, chassis FROM type");
			while (rs.next()) {
				String typeid = rs.getString("typeid");
				String typename = rs.getString("typename");
				int csAtVlan = rs.getString("cs_at_vlan") == null ? Type.CS_AT_VLAN_UNKNOWN : Type.csAtVlan(rs.getBoolean("cs_at_vlan"));
				boolean chassis = rs.getBoolean("chassis");
				
				Type t = new Type(typeid, typename, rs.getString("vendorid"), csAtVlan, chassis);
				typeidM.put(typeid, t);

			}

			// Now fetch all OIDs
			rs = Database.query("SELECT snmpoidid, oidkey, snmpoid, getnext, decodehex, match_regex, defaultfreq, uptodate AS oiduptodate, mib FROM snmpoid");
			while (rs.next()) {
				String snmpoidid = rs.getString("snmpoidid");
				String oidkey = rs.getString("oidkey");
				String oid = rs.getString("snmpoid");
				boolean getnext = rs.getBoolean("getnext");
				boolean decodehex = rs.getBoolean("decodehex");
				String matchRegex = rs.getString("match_regex");
				int defaultfreq = rs.getInt("defaultfreq");
				boolean oiduptodate = rs.getBoolean("oiduptodate");
				String mib = rs.getString("mib");
				
				Snmpoid snmpoid = new Snmpoid(snmpoidid, oidkey, oid, getnext, decodehex, matchRegex, defaultfreq, oiduptodate, mib);
				oidkeyM.put(oidkey, snmpoid);
				if (!oiduptodate && oidKeySet.add(oidkey)) {
					OidTester.clearDupe(snmpoid);
					synchronized (oidQ) {
						oidQ.add(snmpoid);
						oidnew++;
					}
				}
			}

			// Make new types global
			typeidMap = typeidM;
			oidkeyMap = oidkeyM;

			Log.i("UPDATE_TYPES", "Num types: " + typeidMap.size() + ", num OIDs: " + oidkeyMap.size() + ", new oidQ: " + oidnew);

			// Then update all netboxes with the new types
			if (updateNetboxes) updateNetboxesWithNewTypes();

		} catch (SQLException e) {
			Log.e("UPDATE_TYPES", "SQLException: " + e);
			e.printStackTrace(System.err);
		}
	}

	private static synchronized void updateNetboxesWithNewTypes() {
		for (Iterator it = nbMap.values().iterator(); it.hasNext();) {
			NetboxImpl nb = (NetboxImpl)it.next();
			Type t = (Type)typeidMap.get(nb.getTypeT().getTypeid());
			nb.setType(t);
		} 
	}

	public static synchronized void updateNetboxes() {
		int newcnt=0, skipcnt=0, delcnt=0;

		try {
			Map numInStackMap = new HashMap();
			ResultSet rs = Database.query("SELECT netboxid,COUNT(*) AS numInStack FROM module GROUP BY netboxid HAVING COUNT(*) > 1");
			while (rs.next()) numInStackMap.put(rs.getString("netboxid"), rs.getString("numInStack"));

			//String sql = "SELECT ip,ro,deviceid,netboxid,catid,sysname,typeid,typename FROM netbox LEFT JOIN type USING(typeid) WHERE up='y' AND ro IS NOT NULL";
			String sql = "SELECT ip,ro,deviceid,netboxid,catid,sysname,typeid,snmp_version,netbox.uptodate,type.frequency AS typefreq, netboxsnmpoid.frequency AS oidfreq, snmpoidid, oidkey, snmpoid FROM netbox LEFT JOIN type USING(typeid) LEFT JOIN netboxsnmpoid USING(netboxid) LEFT JOIN snmpoid USING(snmpoidid) WHERE up='y' AND ro IS NOT NULL";
			boolean randomize = true;
			if (qNetbox != null) {
				String qn = qNetbox;

				if (qn.startsWith("_") || qn.startsWith("-") || qn.indexOf(",") >= 0) {
					if (qn.startsWith("__")) {
						qn = "";
						sql += " AND netbox.uptodate=false";
					} else if (qn.startsWith("-")) {
						qn = qn.substring(1, qn.length());
						sql += " AND typeid IN (";
					} else if (qn.startsWith("_")) {
						qn = qn.substring(1, qn.length());
						sql += " AND catid IN (";
					} else {
						sql += " AND sysname IN (";
						randomize = false;
					}
					if (qn.length() > 0) {
						String[] ids = qn.split(",");
						for (int i=0; i < ids.length; i++) sql += "'" + ids[i] + "',";
						if (ids.length > 0) sql = sql.substring(0, sql.length()-1);
						sql += ")";
					}
				} else {
					sql += " AND sysname LIKE '"+qn+"'";
				}
			}
			/*
			if (randomize) {
				sql += " ORDER BY random() * netboxid";
			}
			*/
			sql += " ORDER BY netboxid";
			//sql += " LIMIT 1000";
			rs = Database.query(sql);

			String prevnetboxid = null;
			Map keyFreqMap = null, keyMap = null;

			int nbHigh = netboxHigh;
			Set netboxidSet = new HashSet();
			List addToRunQList = new ArrayList();

			while (rs.next()) {
				String netboxid = rs.getString("netboxid");

				try {
					if (!netboxid.equals(prevnetboxid)) {
						keyFreqMap = new HashMap();
						keyMap = new HashMap();
						addDefaultOids(keyFreqMap, keyMap);

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

						boolean newNetbox = false;
						if ( (nb=(NetboxImpl)nbMap.get(netboxid)) == null) {
							nbMap.put(netboxid, nb = new NetboxImpl(++nbHigh, t, keyFreqMap, keyMap));
							newNetbox = true;
						} else {
							long oldNextRun = nb.getNextRun();
							nb.setType(t);
							if (oldNextRun != nb.getNextRun()) {
								// We need to remove the netbox from the runq and re-insert it
								removeFromRunQ(nb, new Long(oldNextRun));
								newNetbox = true;
							}
						}

						nb.setDeviceid(rs.getInt("deviceid"));
						nb.setNetboxid(netboxid);
						nb.setIp(rs.getString("ip"));
						nb.setCommunityRo(rs.getString("ro"));
						nb.setSysname(rs.getString("sysname"));
						nb.setCat(rs.getString("catid"));
						int numInStack = 1;
						if (numInStackMap.containsKey(netboxid)) numInStack = Integer.parseInt((String)numInStackMap.get(netboxid));
						nb.setNumInStack(numInStack);
						nb.setSnmpVersion(rs.getInt("snmp_version"));
						//nb.setSnmpagent(rs.getString("snmpagent"));

						///////////////////////////////////////////
						if (newNetbox) {
							newcnt++;
							addToRunQList.add(nb);
							if (!rs.getBoolean("uptodate")) {
								synchronized (deviceNetboxCache) {
									deviceNetboxCache.remove(nb.getNetboxidS());
								}
							}
						}
						netboxidSet.add(new Integer(nb.getNetboxid()));
						nb.setUptodate(rs.getBoolean("uptodate"));
						/*
						netboxidSet.add(new Integer(nb.getNetboxid()));
						//System.err.println("Sysname: " + rs.getString("sysname") + ", " + rs.getBoolean("uptodate") + ", " + oidNetboxSet);
						if (!rs.getBoolean("uptodate") && oidNetboxSet.add(netboxid)) {
							synchronized (deviceNetboxCache) {
								deviceNetboxCache.remove(nb.getNetboxidS());
							}
							addToOidQList.add(nb);
							System.err.println("Added to oidq: " + nb);
							oidnew++;
						}
						*/
						///////////////////////////////////////////

					}

					String oidkey = rs.getString("oidkey");
					if (oidkey != null) {
						Snmpoid snmpoid = (Snmpoid)oidkeyMap.get(oidkey);

						boolean oidfreq = (rs.getString("oidfreq") != null && rs.getString("oidfreq").length() > 0);
						int freq = oidfreq ? rs.getInt("oidfreq") : rs.getInt("typefreq");
						if (freq <= 0) {
							Log.w("UPDATE_NETBOXES", "No frequency specified for netbox " + netboxid + ", oid: " + oidkey + ", skipping.");
							continue;
						}
						keyFreqMap.put(oidkey, new Integer(freq));
						keyMap.put(oidkey, snmpoid);
					} else {
						Log.d("UPDATE_NETBOXES", "No OIDs found for netbox: " + rs.getString("sysname"));
					}
				} finally {
					prevnetboxid = netboxid;
				}
			}
				
			for (Iterator it = addToRunQList.iterator(); it.hasNext();) {
				NetboxImpl nb = (NetboxImpl)it.next();
				nb.updateNextRun();
				initialQ.add(nb);
				//addToRunQ(nb);
			}

			netboxCnt = netboxidSet.size();
			netboxHigh = nbHigh;

			// Remove netboxes no longer present
			for (Iterator it = nbMap.values().iterator(); it.hasNext();) {
				NetboxImpl nb = (NetboxImpl)it.next();
				if (!netboxidSet.contains(new Integer(nb.getNetboxid()))) {
					nb.remove();
					it.remove();
					delcnt++;
				}
			}

			// Re-create list
			if (newcnt > 0 || delcnt > 0) {
				List nbL = new ArrayList(nbMap.values());
				nbList = nbL;
			}

		} catch (SQLException e) {
			Log.e("UPDATE_NETBOXES", "SQLException: " + e);			
			e.printStackTrace(System.err);
		}

		String msg = "Num netboxes: " + netboxCnt + " (" + netboxHigh + " high, " + newcnt + " new, " + delcnt + " removed, " + skipcnt + " skipped, " + nbRunQSize() + " runq,";
		if (initialQ.size() > 0) msg += " " + initialQ.size() + " initialQ,";
		msg +=  " " + threadCnt + " active)";
		Log.i("UPDATE_NETBOXES", msg);
		//Log.i("UPDATE_NETBOXES", "Num netboxes: " + netboxCnt + " (" + netboxHigh + " high, " + newcnt + " new, " + delcnt + " removed, " + skipcnt + " skipped, " + nbRunQSize() + " runq, " + threadCnt + " active)");

		// Check the run queue in case we have any new netboxes to check
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
			netboxidRunQMap.put(nb.getNetboxidS(), nextRun);
		}
	}

	private static void removeFromRunQ(NetboxImpl nb, Long nextRun) {
		synchronized (nbRunQ) {
 			LinkedList l;
			if ( (l = (LinkedList)nbRunQ.get(nextRun)) == null) {
				// Check if the netbox is still in the initialQ
				for (Iterator it = initialQ.iterator(); it.hasNext();) {
					if (nb.getNum() == ((NetboxImpl)it.next()).getNum()) {
						it.remove();
						break;
					}
				}
				return;
			}
			for (Iterator it = l.iterator(); it.hasNext();) {
				if (nb.getNum() == ((NetboxImpl)it.next()).getNum()) {
					it.remove();
					netboxidRunQMap.remove(nb.getNetboxidS());
					break;
				}
			}
			if (l.isEmpty()) nbRunQ.remove(nextRun);
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

	private static int nbRunQSize() {
		synchronized (nbRunQ) {
			return nbRunQ.size();
		}
	}

	private static Object removeRunQHeadNoCheck() {
		synchronized (nbRunQ) {
			boolean isInitial = !initialQ.isEmpty();
			boolean rand = Math.random() >= 0.5f; // 50% of picking initial if runQ is not empty
			if (extraThreadCnt > 0) rand = false; // Don't pick from initial queue when doing immediate netbox runs
			if (nbRunQ.isEmpty() || (isInitial && rand)) {
				if (!initialQ.isEmpty()) return initialQ.remove(initialQ.size()-1);
				return new Long(Long.MAX_VALUE / 2); // Infinity...
			}
			Long nextRun = (Long)nbRunQ.firstKey();
			if (nextRun.longValue() > System.currentTimeMillis()) {
				// Head of queue is not yet ready to be run
				if (!initialQ.isEmpty()) return initialQ.remove(initialQ.size()-1);
				return new Long(nextRun.longValue() - System.currentTimeMillis());
			}

			LinkedList l = (LinkedList)nbRunQ.get(nextRun);
			NetboxImpl nb  = (NetboxImpl)l.removeFirst();
			netboxidRunQMap.remove(nb.getNetboxidS());
			if (l.isEmpty()) nbRunQ.remove(nextRun);
			return nb;
		}
	}

	private static NetboxImpl removeFromRunQ(String netboxid) {
		synchronized (nbRunQ) {
 			LinkedList l;
			Long nextRun = (Long)netboxidRunQMap.get(netboxid);
			if (nextRun == null) {
				// Check if the netbox is still in the initialQ
				for (Iterator it = initialQ.iterator(); it.hasNext();) {
					NetboxImpl nb = (NetboxImpl)it.next();
					if (nb.getNetboxidS().equals(netboxid)) {
						it.remove();
						return nb;
					}
				}
				Log.d("QUERY_NETBOX", "REMOVE_FROM_RUNQ", "nextRun not found for netboxid " + netboxid);
				return null;
			}
			if ( (l = (LinkedList)nbRunQ.get(nextRun)) == null) return null;
			for (Iterator it = l.iterator(); it.hasNext();) {
				NetboxImpl nb = (NetboxImpl)it.next();
				if (nb.getNetboxidS().equals(netboxid)) {
					it.remove();
					if (l.isEmpty()) nbRunQ.remove(nextRun);
					netboxidRunQMap.remove(nb.getNetboxidS());
					return nb;
				}
			}
		}
		return null;
	}

	// Run the nexbox immediately
	private static boolean runNetbox(String netboxid, String maxage, String source, String subid) {
		scheduleImmediatelyMap.put(netboxid, new String[] { source, subid });
		NetboxImpl nb = removeFromRunQ(netboxid);
		Log.d("QUERY_NETBOX", "RUN_NETBOX", "Immediate run for netbox("+netboxid+"): " + nb);
		if (nb == null) return false;
		nb.scheduleImmediately(); // Schedule immediately
		addToRunQFront(nb);
		synchronized (idleThreadLock) {
			// If there are no idle threads, make one
			extraThreadCnt++;
		}
		scheduleCheckRunQ(0);
		return true;
	}

	private static String requestThread(boolean allowExtra) {
		synchronized (idleThreadLock) {
			int max = allowExtra ? maxThreadCnt+extraThreadCnt : maxThreadCnt;
			if (allowExtra && extraThreadCnt > 0) extraThreadCnt--;
			if (threadCnt < max) {
				int tid = getFreeTid();
				threadCnt++;
				//System.err.println("New thread, cnt="+(threadCnt+1)+" max="+max);
				return format(tid, String.valueOf(max-1).length());
			}
			return null;
		}
	}

	private static void threadIdle(String tid) {
		synchronized (idleThreadLock) {
			returnTid(Integer.parseInt(tid));
			//System.err.println("Del thread, cnt="+(threadCnt-1));
			threadCnt--;
		}
		scheduleCheckRunQ(0);
	}

	private static int getFreeTid() {
		if (threadIdList.isEmpty()) {
			threadIdList.add(new Integer(curMaxTid++));
		}
		return ((Integer)threadIdList.removeFirst()).intValue();
	}

	private static void returnTid(int tid) {
		threadIdList.add(new Integer(tid));
	}

	// Constructor
	public QueryNetbox(String tid, NetboxImpl initialNb)
	{
		this.tid = tid;
		this.setName("QueryNetbox-" + tid);
		this.nb = initialNb;
	}

	public QueryNetbox(String tid, Object oidUpdObj) {
		this.tid = tid;
		this.setName("QueryNetbox-" + tid);
		this.oidUpdObj = oidUpdObj;
	}

	public void run()
	{
		Log.setDefaultSubsystem("QUERY_NETBOX_T"+tid);
		Log.setThreadId(tid);

		Log.d("RUN", "Thread " + tid + " starting work on ("+nb+"|"+oidUpdObj+")");

		long beginTime = System.currentTimeMillis();
		SimpleSnmp sSnmp = null;

		try {
			while (true) {

				// Check if we were assigned an oid object and not a netbox
				if (oidUpdObj == null && !nb.getUptodate()) oidUpdObj = nb;

				if (oidUpdObj != null) {
					OidTester oidTester = new OidTester();
					if (oidUpdObj instanceof NetboxImpl) {
						nb = (NetboxImpl)oidUpdObj;
						sSnmp = SimpleSnmp.simpleSnmpFactory();
						sSnmp.setHost(nb.getIp());
						sSnmp.setCs_ro(nb.getCommunityRo());
						sSnmp.checkSnmpVersion();
						oidTester.oidTest(nb, oidkeyMap.values().iterator(), sSnmp );
						//nb.scheduleImmediately();
					} else if (oidUpdObj instanceof Snmpoid) {
						Snmpoid oid = (Snmpoid)oidUpdObj;
						oidTester.oidTest(oid, nbList.iterator() );
						oidKeySet.remove(oid.getOidkey());
						synchronized (oidQ) {
							if (oidQ.isEmpty()) {
								Log.d("RUN", "oidQ empty, scheduling types/netboxes update");
								scheduleUpdateNetboxes(0);
							}
							Log.d("RUN", "Thread idle, done OID object processing ("+oidQ.size()+" remain), exiting...");
							return;
						}
					}
					oidUpdObj = null;
				}
				nb.setNeedRestart(false);

				// Process netbox
				String netboxid = nb.getNetboxidS();
				String ip = nb.getIp();
				String cs_ro = nb.getCommunityRo();
				String vendor = nb.getTypeT().getVendor();
				String type = nb.getType();
				String sysName = nb.getSysname();
				String cat = nb.getCat();
				int snmpVersion = nb.getSnmpVersion();

				Log.setNetbox(sysName);

				sSnmp = SimpleSnmp.simpleSnmpFactory();
				//System.err.println("Created sSnmp: " + sSnmp);
				sSnmp.setHost(ip);
				sSnmp.setCs_ro(cs_ro);

				Log.d("RUN", "Now working with("+netboxid+"): " + sysName + ", type="+type+", ip="+ip+" (device "+ nb.getNum() +" of "+ netboxHigh+")");
				long boksBeginTime = System.currentTimeMillis();

				try {

					// Get DataContainer objects from each data-plugin.
					DataContainersImpl containers = getDataContainers(null);

					// Find handlers for this boks
					DeviceHandler[] deviceHandler = findDeviceHandlers(nb);
					if (deviceHandler == null) {
						nb.printSchedule();
						throw new NoDeviceHandlerException("  No device handlers found for netbox: " + netboxid + " (cat: " + cat + " type: " + type + ")");
					}

					Log.setDefaultSubsystem("QUERY_NETBOX_T"+tid);
					String dhNames = "";
					for (int dhNum=0; dhNum < deviceHandler.length; dhNum++) {
						String[] ss = String.valueOf(deviceHandler[dhNum].getClass()).split("\\.");
						dhNames += (dhNum==0?"":",")+ss[ss.length-1];
					}

					Log.d("RUN", "  Found " + deviceHandler.length + " deviceHandlers ("+dhNames+"): " + netboxid + " (cat: " + cat + " type: " + type + ")");

					boolean timeout = false;
					for (int dhNum=0; dhNum < deviceHandler.length; dhNum++) {
						try {
							deviceHandler[dhNum].handleDevice(nb, sSnmp, myCp, containers);
							if (nb.needRefetch() || nb.needRestart() || nb.isRemoved()) break;

						} catch (TimeoutException te) {
							Log.setDefaultSubsystem("QUERY_NETBOX_T"+tid);				
							Log.d("RUN", "TimeoutException: " + te.getMessage());
							Log.w("RUN", "GIVING UP ON: " + sysName + ", typeid: " + type );
							timeout = true;
						} catch (Exception exp) {
							Log.w("RUN", "Fatal error from devicehandler, skipping. Exception: " + exp.getMessage());
							exp.printStackTrace(System.err);
						} catch (Throwable e) {
							Log.w("RUN", "Fatal error from devicehandler, plugin is probably old and needs to be updated to new API: " + e.getMessage());
							e.printStackTrace(System.err);
						}

					}

					if (!timeout && !nb.isRemoved()) {
						// Call the data handlers for all data plugins
						try { 
							Map changedDeviceids = containers.callDataHandlers(nb);
							if (!changedDeviceids.isEmpty()) getDataContainers(changedDeviceids);
						
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

				if (scheduleImmediatelyMap.containsKey(nb.getNetboxidS())) {
					// Send event that we are done
					String[] ss = (String[])scheduleImmediatelyMap.remove(nb.getNetboxidS());
					String target = ss[0];
					String subid = ss[1];
					Log.i("RUN", "Done collecting immediate data for " + target + ", netbox: " + nb);

					Map varMap = new HashMap();
					varMap.put("command", "runNetboxDone");
					try {
						EventQ.createAndPostEvent("getDeviceData", target, nb.getDeviceid(), nb.getNetboxid(), Integer.parseInt(subid), "notification", Event.STATE_NONE, 0, 0, varMap);
					} catch (Exception e) {
						Log.e("RUN", "Exception when posting to eventq: " + e);
						e.printStackTrace(System.err);
					}
				}

				// If we need to recreate the netbox, set the unknown type
				/*
				if (nb.needRecreate()) {
					Log.d("RUN", "Recreating netbox: " + nb);
					nb.setType((Type)typeidMap.get(Type.UNKNOWN_TYPEID));
				}
				*/

				// If netbox is removed, don't add it to the RunQ
				if (!nb.needRefetch() && !nb.isRemoved()) {

					// Store last collect time in netboxinfo
					try {
						NetboxInfo.put(nb.getNetboxidS(), null, "lastUpdated", String.valueOf(System.currentTimeMillis()));
					} catch (RuntimeException rte) {
						Log.w("RUN", "Database error while updating lastUpdated for " + nb.getSysname() + ", contact NAV support.");
						Log.d("RUN", "Got exception while setting lastUpdated: " + rte.getMessage());
					}

					nb.reschedule();

					/*
					// Don't reschedule if we just set the unknown type for this netbox as we want it to run immediately
					if (!nb.needRecreate()) {
						nb.reschedule();
					}
					*/
				
					// Insert into queue
					addToRunQ(nb);

					Log.d("RUN", "Done processing netbox " + nb + " (nextrun: " + (nb.getNextRun()-System.currentTimeMillis())+ ")");

				} else {
					Log.d("RUN", "Done, re-fetching nb from database: " + nb);
					synchronized (nbMap) {
						nbMap.remove(nb.getNetboxidS());
					}
					scheduleUpdateNetboxes(0);
				}
				Log.setNetbox(null);

				long pc = ++nbProcessedCnt;
				if ((pc % 100) == 0) {
					Log.i("RUN", "** Processed " + pc + " netboxes (" + (pc%(netboxCnt+1)) + " of " + netboxCnt + ") **");
				}

				if (nb.needRefetch() || !nb.needRestart()) {
					// Try to get a new netbox to process
					Object o = removeRunQHead();
					if (o instanceof NetboxImpl) {
						nb = (NetboxImpl)o;
						Log.d("RUN", "Got new netbox: " + nb);
					} else {
						// We didn't get a netbox; exit the thread
						Log.d("RUN", "No new netbox available: " + o);
						break;
					}
				}

			}

		} catch (Throwable e) {
			Log.e("RUN", "Caught exception, should not happen: " + e.getMessage());
			e.printStackTrace(System.err);
		} finally {
			Log.d("RUN", "Thread idle, exiting...");
			//System.err.println("Thread idle, sSnmp: " + sSnmp);
			if (sSnmp != null) sSnmp.destroy();
			sSnmp = null;
			System.gc();
			Log.freeThread();
			threadIdle(tid);
		}
	}

	private DataContainersImpl getDataContainers(Map changedDeviceids) {
		if (changedDeviceids == null) changedDeviceids = new HashMap();
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
					m.put("navCp", navCp);
					try {
						dh.init(m, changedDeviceids);
					} catch (Throwable th) {
						System.err.println("File: " + fn);
						th.printStackTrace();
						continue;
					}

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
						if (v == DeviceHandler.NEVER_HANDLE) continue;
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

	static class EventListener implements EventQListener {
		public void handleEvent(Event e) {
			Log.setDefaultSubsystem("HANDLE_EVENT");
			if (!e.getEventtypeid().equals("notification")) {
				Log.d("HANDLE_EVENT", "Unknown eventtypeid: " + e.getEventtypeid());
				e.dispose();
				return;
			}

			String cmd = e.getVar("command");
			if ("dumpRunq".equals(cmd)) {
				// Dump runq
				synchronized (nbRunQ) {
					Log.d("HANDLE_EVENT", "Dumping runQ: " + nbRunQ.size() + " entries"); 
					for (Iterator it=nbRunQ.entrySet().iterator(); it.hasNext();) {
						Map.Entry me = (Map.Entry)it.next();
						long curTime = System.currentTimeMillis();
						Log.d("RUNQ", (((Long)me.getKey()).longValue()-curTime) + ": " + me.getValue());
					}
				}
			} else if ("dumpOidLocks".equals(cmd)) {
				Log.d("HANDLE_EVENT", "Active OID locks: " + OidTester.getLockSet());
			} else if ("updateFromDB".equals(cmd)) {
				// Update types/netboxes
				Log.d("HANDLE_EVENT", "Updating types/netboxes");
				scheduleUpdateNetboxes(0);
			} else if ("runNetbox".equals(cmd)) {
				String netboxid = String.valueOf(e.getNetboxid());
				if (netboxid != null) {
					runNetbox(netboxid, e.getVar("maxage"), e.getSource(), String.valueOf(e.getSubid()));
				}
			} else if ("dumpOidNetbox".equals(cmd)) {
				String netboxid = String.valueOf(e.getNetboxid());
				if (netboxid != null) {
					NetboxImpl nb = (NetboxImpl)nbMap.get(netboxid);
					if (nb != null) nb.printSchedule();
				}
			} else {
				Log.d("HANDLE_EVENT", "Unknown command: " + cmd);
			}

			e.dispose();

		}
	}

	private static String format(long i, int n)
	{
		DecimalFormat nf = new DecimalFormat("#");
		nf.setMinimumIntegerDigits(n);
		return nf.format(i);
	}

}
