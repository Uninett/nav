/*
 *
 *
 *
 */

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
import no.ntnu.nav.getDeviceData.dataplugins.*;
import no.ntnu.nav.getDeviceData.deviceplugins.*;

// select swportid,boksid,sysname,typeid,ifindex,modul,port,status,speed,duplex,media,trunk from swport join boks using (boksid) join type using (typeid) where typegruppe like '3%' and swport.static='f' order by boksid,modul,port;
// select count(*) from swport join boks using (boksid) join type using (typeid) where typegruppe like '3%' and swport.static='f';
// SELECT DISTINCT typeid FROM swport JOIN boks USING(boksid) WHERE swport.static='t';


// For å slette alle swportvlan records dette scriptet fyller inn
// DELETE FROM swportvlan WHERE swportid IN (SELECT swportid FROM swport JOIN boks USING(boksid) NATURAL JOIN type WHERE watch='f' AND (typegruppe LIKE '3%' OR typegruppe IN ('catmeny-sw', 'cat1900-sw')))

class getDeviceData
{
	public static final String navRoot = "/usr/local/nav/";
	public static final String dbConfigFile = "local/etc/conf/db.conf";
	public static final String configFile = "local/etc/conf/getDeviceData.conf";
	public static final String scriptName = "getDeviceData";
	public static final String logFile = "local/log/getDeviceData.log";

	public static int NUM_THREADS = 16;
	public static final int SHOW_TOP = 25;

	public static final boolean ERROR_OUT = true;
	public static final boolean VERBOSE_OUT = true;
	public static final boolean DEBUG_OUT = true;

	public static final boolean DB_UPDATE = true;
	public static final boolean DB_COMMIT = true;

	// END USER CONFIG //

	// Felles datastrukturer som bare skal leses fra
	//static HashMap macBoksid = new HashMap();
	//static HashMap boksidName = new HashMap();
	//static HashMap boksidKat = new HashMap();
	//static HashMap sysnameMap = new HashMap();
	static LinkedList bdFifo = new LinkedList();
	static Map bdMap = new HashMap();

	// Boksdisk / boksinterface
	static HashMap boksDiskMap;
	static HashMap boksInterfaceMap;

	// module / swport
	static HashMap moduleMap;
	static HashMap deviceMap = new HashMap();

	static int threadNumDigits = String.valueOf(NUM_THREADS-1).length();

	// A timer
	static Thread[] threads;
	static Timer timer;
	static NetboxTimer netboxTimer;
	static Stack idleThreads;

	//static HashSet safeCloseBoksid = new HashSet();
	static String qBoks;

	public static void main(String[] args) throws SQLException
	{
		String cf = null;
		// Check arguments
		if (args.length > 0) {
			try {
				NUM_THREADS = Integer.parseInt(args[0]);
			} catch (NumberFormatException e) {
				// Assume this argument is the config file
				File f = new File(args[0]);
				if (f.exists() && !f.isDirectory()) {
					cf = f.getAbsolutePath();
					outl("Using configfile: " + f.getAbsolutePath());
				}

				// Is next arg number of threads?
				if (args.length > 1) {
					try {
						NUM_THREADS = Integer.parseInt(args[1]);
					} catch (NumberFormatException ee) {
						// Assume this argument is a boksname
						qBoks = args[1].trim();
						outl("Querying netbox: " + qBoks);

						// Is next arg number of threads?
						if (args.length > 2) {
							try {
								NUM_THREADS = Integer.parseInt(args[2]);
							} catch (NumberFormatException eee) {
								outl("Error, unrecognized argument: " + args[2]);
								return;
							}
						}
					}
				}
			}
			if (NUM_THREADS > 128) {
				outl("Error, more than 128 threads not recommended, re-compile needed.");
				return;
			}
		}
		outl("Running with " + NUM_THREADS + " threads max.");

		// Init logger
		Log.init(navRoot + logFile, "getDeviceData");

		ConfigParser cp, dbCp;
		try {
			if (cf == null) cf = navRoot + configFile;
			cp = new ConfigParser(cf);
		} catch (IOException e) {
			errl("Error, could not read config file: " + cf);
			return;
		}
		try {
			dbCp = new ConfigParser(navRoot + dbConfigFile);
		} catch (IOException e) {
			errl("Error, could not read config file: " + navRoot + dbConfigFile);
			return;
		}
		if (!Database.openConnection(dbCp.get("dbhost"), dbCp.get("dbport"), dbCp.get("db_nav"), dbCp.get("script_"+scriptName), dbCp.get("userpw_"+dbCp.get("script_"+scriptName)))) {
			errl("Error, could not connect to database!");
			return;
		}

		// Load config
		try {
			QueryNetbox.minBoksRunInterval = Integer.parseInt(cp.get("minBoksRunInterval"));
		} catch (Exception e) {
			QueryNetbox.minBoksRunInterval = 60; // Default is every 60 minutes
		}
		QueryNetbox.minBoksRunInterval *= 60 * 1000; // Convert from minutes to milliseconds
		// DEBUG
		QueryNetbox.minBoksRunInterval = 15000; // Every 15 secs

		int loadDataInterval;
		try {
			loadDataInterval = Integer.parseInt(cp.get("loadDataInterval"));
		} catch (Exception e) {
			loadDataInterval = 5; // Default is every 5 minutes
		}
		loadDataInterval *= 60 * 1000; // Convert from minutes to in milliseconds


		// Hent data
		loadData();
		Timer loadDataTimer = new Timer();
		loadDataTimer.schedule(new LoadDataTask(), loadDataInterval, loadDataInterval);


		// Sett datastrukturer for alle tråder
		QueryNetbox.ERROR_OUT = ERROR_OUT;
		QueryNetbox.VERBOSE_OUT = VERBOSE_OUT;
		QueryNetbox.DEBUG_OUT = DEBUG_OUT;
		QueryNetbox.DB_UPDATE = DB_UPDATE;
		QueryNetbox.DB_COMMIT = DB_COMMIT;

		QueryNetbox.setConfigParser(cp);

		QueryNetbox.setModuleMap(moduleMap);
		QueryNetbox.setDeviceMap(deviceMap);
		//QueryNetbox.setSwportDataMap(swportDataMap);
		QueryNetbox.setBoksDiskMap(boksDiskMap);
		QueryNetbox.setBoksInterfaceMap(boksInterfaceMap);

		QueryNetbox.setBdFifo(bdFifo);
		QueryNetbox.setBdMap(bdMap);

		// Indikerer om en tråd er ferdig
		QueryNetbox.initThreadDone(NUM_THREADS);

		// Lag trådene
		//long beginTime = System.currentTimeMillis();

		threads = new Thread[NUM_THREADS];
		//int digits = String.valueOf(NUM_THREADS-1).length();

		idleThreads = new Stack();
		QueryNetbox.setIdleThreads(idleThreads);
		for (int i=NUM_THREADS-1; i >= 0; i--) {
			idleThreads.push(new Integer(i));
		}

		// Set up the plugin monitor
		Map dataClassMap = new HashMap();
		Map deviceClassMap = new HashMap();
		QueryNetbox.setDataClassMap(dataClassMap);
		QueryNetbox.setDeviceClassMap(deviceClassMap);
		Timer pluginTimer = new Timer(true);
		PluginMonitorTask pmt = new PluginMonitorTask("data-plugins", dataClassMap, "device-plugins", deviceClassMap);
		// Load all plugins
		pmt.run();
		// Check for new plugin every 5 seconds
		pluginTimer.schedule(pmt, 5 * 1000, 5 * 1000);

		outld("Starting timer for boks query scheduling...");
		timer = new Timer();
		timer.schedule( netboxTimer = new NetboxTimer(), 0);

		/*
		// Sleep forever
		while (true) {
			try {
				Thread.currentThread().sleep(5000);
			} catch (InterruptedException e) {
			}
		}
		*/



		/*
		for (int i=0; i < NUM_THREADS; i++) {
			threads[i] = new QueryNetbox(i, format(i, digits));
			threads[i].start();
		}

		for (int i=0; i < NUM_THREADS; i++) {
			try {
				threads[i].join();
			} catch (InterruptedException e) {
				errl("Error, got InterruptedException: " + e.getMessage() );
			}
		}
		*/
		//long usedTime = System.currentTimeMillis() - beginTime;

		// Sjekk om det er port-innslag som ikke lenger er tilstedet
		/*
		Iterator iter = swportDataMap.values().iterator();
		int remcnt=0;
		while (iter.hasNext()) {
			HashMap hm = (HashMap)iter.next();
			String boksid = (String)hm.get("boksid");
			if (!safeCloseBoksid.contains(boksid)) continue;

			String typegruppe = (String)boksidTypegruppe.get(boksid);

			if (typegruppe.startsWith("3") || typegruppe.equals("catmeny-sw") || typegruppe.equals("cat1900-sw")) {
				// Slett enheten
				remcnt++;
				//System.err.println("Want to delete: " + hm.get("boksid") + " Modul: " + hm.get("modul") + " Port: " + hm.get("port") + " Vlan: " + hm.get("vlan"));

			}

		}
		outl("Missing data from " + remcnt + " ports");
		*/

		/*
		// Lag rapport på tid brukt på de forskjellige boksene
		ArrayList boksReport = QueryNetbox.boksReport;
		Collections.sort(boksReport);

		digits = String.valueOf(Math.min(SHOW_TOP, boksReport.size())).length();
		for (int i=0; i < SHOW_TOP && i < boksReport.size(); i++) {
			BoksReport br = (BoksReport)boksReport.get(i);
			outl(format(i+1, digits)+": " + formatTime(br.getUsedTime()) + ", " + br.getBoksData().sysName + " (" + br.getBoksData().boksType + ") (" + br.getBoksData().ip + ")");
		}
		*/

		/*
		Database.closeConnection();
		//outl("All done, time used: " + formatTime(usedTime) + ".");

		// Create a job-finished file
		try {
			String curDir = System.getProperty("user.dir");
			char sep = File.separatorChar;
			File f = new File(curDir+sep+"job-finished");
			f.createNewFile() ;
		} catch (SecurityException e) {
			errl("Error, cannot write to user.dir: " + e.getMessage() );
		} catch (IOException e) {
			errl("Error, got IOException: " + e.getMessage() );
		}

		outflush();
		errflush();
		System.exit(0);
		*/


	}

	private static void timerSched(long l)
	{
		synchronized (timer) {
			netboxTimer.cancel();
			netboxTimer = new NetboxTimer();
			timer.schedule(netboxTimer, l);
		}
	}

	public static void threadIdle()
	{
		timerSched(0);
	}

	public static void checkBdQ()
	{
		outld("Checking queue for ripe boksDatas");
		synchronized (bdFifo) {
			outld("  Elements in queue: " + bdFifo.size());
			if (bdFifo.size() == 0) return;
			NetboxImpl nb = (NetboxImpl)bdFifo.getFirst();
			if (nb.nextRun() > System.currentTimeMillis()) {
				// Not yet ripe
				outld("  Head of queue not yet ripe, next run in: " + (nb.nextRun() - System.currentTimeMillis()) + " ms");
				timerSched(nb.nextRun() - System.currentTimeMillis());
				return;
			}

			// Start a new thread to handle this
			outd("  Head of queue ripe, starting new thread to handle this...");
			int tnum;
			synchronized (idleThreads) {
				if (idleThreads.empty()) { outld("no idle threads"); return; } // No available threads
				tnum = ((Integer)idleThreads.pop()).intValue();
			}
			outld("started thread #"+tnum);

			bdFifo.removeFirst();
			threads[tnum] = new QueryNetbox(tnum, format(tnum, threadNumDigits), nb);
			threads[tnum].start();

			// Schedule next task if there is one
			if (bdFifo.size() > 0) {
				nb = (NetboxImpl)bdFifo.getFirst();
				outld("  Scheduling next task, ripe in: " + (Math.max(0, nb.nextRun() - System.currentTimeMillis())) + " ms");
				timerSched(Math.max(0, nb.nextRun() - System.currentTimeMillis()) );
			}
		}
	}

	public static void loadData() throws SQLException
	{
		//if (moduleMap == null) loadPermanentData();
		loadReloadableData();
	}

	/*
	private static void loadPermanentData() throws SQLException
	{
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;
		outl("Loading permanent data from tables...");

		out("  swport...");
		moduleMap = new HashMap();
		dumpBeginTime = System.currentTimeMillis();
		rs = Database.query("SELECT deviceid,serial,hw_ver,sw_ver,moduleid,module,netboxid,submodule,up,swport.swportid,port,ifindex,link,speed,duplex,media,trunk,portname,vlan,hexstring FROM device JOIN module USING (deviceid) LEFT JOIN swport USING (moduleid) LEFT JOIN swportallowedvlan USING (swportid) LEFT JOIN swportvlan ON (trunk='f' AND swport.swportid=swportvlan.swportid) ORDER BY moduleid");
		//ResultSetMetaData rsmd = rs.getMetaData();
		while (rs.next()) {

			ModuleData md = new ModuleData(rs.getString("serial"), rs.getString("hw_ver"), rs.getString("sw_ver"), rs.getString("module"));
			md.setDeviceid(rs.getInt("deviceid"));
			md.setModuleid(rs.getInt("moduleid"));
			md.setSubmodule(rs.getString("submodule"));

			int moduleid = rs.getInt("moduleid");
			if (rs.getString("port") != null && rs.getString("port").length() > 0) {
				do {
					SwportData sd = new SwportData(rs.getString("port"), rs.getString("ifindex"), rs.getString("link").charAt(0), rs.getString("speed"), rs.getString("duplex").charAt(0), rs.getString("media"), rs.getBoolean("trunk"), rs.getString("portname"));
					sd.setSwportid(rs.getInt("swportid"));
					sd.setVlan(rs.getInt("vlan") == 0 ? Integer.MIN_VALUE : rs.getInt("vlan"));
					sd.setHexstring(rs.getString("hexstring"));
					md.addSwportData(sd);
				} while (rs.next() && rs.getInt("moduleid") == moduleid);
				rs.previous();
			}

			String key = rs.getString("netboxid")+":"+md.getKey();
			moduleMap.put(key, md);
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		out("  netboxdisk...");
		boksDiskMap = new HashMap();
		dumpBeginTime = System.currentTimeMillis();
		rs = Database.query("SELECT netboxid,path,blocksize FROM netboxdisk");
		while (rs.next()) {
			String key = rs.getString("netboxid");
			Map m;
			if ( (m=(Map)boksDiskMap.get(key)) == null) boksDiskMap.put(key, m = new HashMap());
			m.put(rs.getString("path"), new String[] { rs.getString("blocksize") } );
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

		out("  netboxinterface...");
		boksInterfaceMap = new HashMap();
		dumpBeginTime = System.currentTimeMillis();
		rs = Database.query("SELECT netboxid,interf FROM netboxinterface");
		while (rs.next()) {
			String key = rs.getString("netboxid");
			Set s;
			if ( (s=(Set)boksInterfaceMap.get(key)) == null) boksInterfaceMap.put(key, s = new HashSet());
			s.add(rs.getString("interf"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");

	}
	*/

	private static void loadReloadableData() throws SQLException
	{
		ResultSet rs;
		long dumpBeginTime,dumpUsedTime;
		outl("Re-loading data from tables...");

		/*
		// Hent kobling mellom boksid<->typegruppe
		out("  boks...");
		HashMap boksidTypegruppe = new HashMap();
		dumpBeginTime = System.currentTimeMillis();
		rs = Database.query("SELECT boksid,typegruppe FROM boks JOIN type USING (typeid)");
		while (rs.next()) {
			boksidTypegruppe.put(rs.getString("boksid"), rs.getString("typegruppe"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		outl(dumpUsedTime + " ms.");
		*/

		// device
		/*
		dumpBeginTime = System.currentTimeMillis();
		rs = Database.query("SELECT deviceid,serial FROM device");
		while (rs.next()) {
			deviceMap.put(rs.getString("serial"), rs.getString("deviceid"));
		}
		dumpUsedTime = System.currentTimeMillis() - dumpBeginTime;
		*/



		String qNettel;

		//qNettel = "_all";
		//qNettel = "_new";
		//qNettel = "_sw";
		//qNettel = "_gw";
		//qNettel = "_kant";
		//qNettel = "_cat-ios";
		//qNettel = "_cdp";
		//qNettel = "voll-sw";
		//qNettel = "sb-353-sw";
		//qNettel = "hyper-sw";
		//qNettel = "voll-sby-981-h";
		//qNettel = "hb-301-sw2";
		qNettel = "_3com";
		//qNettel = "voll-sw";
		//qNettel = "voll-sby-982-h2";
		//qNettel  = "_voll";
		qNettel = "_def";
		//qNettel = "itea-ans3-230-h";
		//qNettel = "iot-stud-313-h2";

		if (qBoks != null) qNettel = qBoks;

		//Database.setDefaultKeepOpen(true);
		if (qNettel.equals("_new")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE NOT EXISTS (SELECT boksid FROM swp_boks WHERE boksid=boks.boksid) AND (kat='KANT' or kat='SW') ORDER BY boksid");
		} else
		if (qNettel.equals("_all")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE (kat='SW' OR kat='KANT' OR kat='GW') AND watch='f'");
		} else
		if (qNettel.equals("_gw")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='GW'");
		} else
		if (qNettel.equals("_sw")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='SW'");
		} else
		if (qNettel.equals("_kant")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE kat='KANT'");
		} else
		if (qNettel.equals("_3com")) {
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE typegruppe like '3%' AND watch='f'");
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE typegruppe like '3%' AND typeid='SW3300' AND watch='f'");
		} else
		if (qNettel.equals("_voll")) {
			rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE sysname like 'voll%'");
		} else
		if (qNettel.equals("_def")) {
			// USE THIS
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE watch='f' AND (typegruppe LIKE '3%' OR typeid LIKE 'C3000%' OR typeid LIKE 'C1900%')");
			//rs = Database.query("SELECT ip,ro,netboxid,typename,typegroupid,catid,sysname FROM netbox LEFT JOIN type USING(typeid) WHERE up='y' AND (catid='SRV' OR typegroupid LIKE '3%' OR typegroupid IN ('catmeny-sw', 'cat1900-sw', 'hpsw') )");
			rs = Database.query("SELECT ip,ro,netboxid,typename,typegroupid,catid,sysname FROM netbox LEFT JOIN type USING(typeid) WHERE up='y'");
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE boksid=278");
		} else {
			rs = Database.query("SELECT ip,ro,netboxid,typename,typegroupid,catid,sysname FROM netbox LEFT JOIN type USING(typeid) WHERE up='y' AND sysname='"+qNettel+"'");
			//rs = Database.query("SELECT ip,ro,boksid,typeid,typegruppe,kat,sysName FROM boks NATURAL JOIN type WHERE sysName IN ('iot-stud-313-h2','hjarl-sw','math-ans-355-h')");
		}
		//Database.setDefaultKeepOpen(false);

		Map bdMapClone;
		synchronized (bdMap) {
			bdMapClone = (Map) ((HashMap)bdMap).clone();
		}
		while (rs.next()) {
			// Eksisterer denne fra før?
			String boksid = rs.getString("netboxid");
			NetboxImpl nb;
			boolean newBd = false;
			synchronized (bdMap) {
				if ( (nb=(NetboxImpl)bdMap.get(boksid)) != null) {
					bdMapClone.remove(boksid);
				} else {
					nb = new NetboxImpl();
					bdMap.put(boksid, nb);
					newBd = true;
				}
			}

			nb.setNetboxid(boksid);
			nb.setIp(rs.getString("ip"));
			nb.setCommunityRo(rs.getString("ro"));
			nb.setTypegroup(rs.getString("typegroupid"));
			nb.setType(rs.getString("typename"));
			nb.setSysname(rs.getString("sysname"));
			nb.setCat(rs.getString("catid"));
			//bd.setSnmpMajor(rs.getInt("snmp_major"));
			//bd.setSnmpagent(rs.getString("snmpagent"));

			if (newBd) {
				synchronized (bdFifo) {
					bdFifo.addFirst(nb);
				}
			}
		}

		synchronized (bdMap) {
			Iterator i = bdMapClone.keySet().iterator();
			while (i.hasNext()) {
				String boksid = (String)i.next();
				NetboxImpl nb = (NetboxImpl)bdMap.remove(boksid);
				nb.removed(true);
			}
		}

	}

	private static String format(long i, int n)
	{
		DecimalFormat nf = new DecimalFormat("#");
		nf.setMinimumIntegerDigits(n);
		return nf.format(i);
	}
	public static String formatTime(long t)
	{
		long h = t / (60 * 60 * 1000);
		t %= 60 * 60 * 1000;

		long m = t / (60 * 1000);
		t %= 60 * 1000;

		long s = t / (1000);
		t %= 1000;

		long ms = t;

		return format(h,2)+":"+format(m,2)+":"+format(s,2)+"."+format(ms,3);
	}
	private static HashMap getHashFromResultSet(ResultSet rs, ResultSetMetaData md, boolean convertNull) throws SQLException {
		HashMap hm = new HashMap();
		for (int i=md.getColumnCount(); i > 0; i--) {
			String val = rs.getString(i);
			hm.put(md.getColumnName(i), (convertNull&&val==null)?"":val);
		}
		return hm;
	}

	private static void out(Object o) { System.out.print(o); }
	private static void outl(Object o) { System.out.println(o); }
	private static void outflush() { System.out.flush(); }
	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	private static void errflush() { System.err.flush(); }
	private static void outd(String s) { if (DEBUG_OUT) System.out.print(s); }
	private static void outld(String s) { if (DEBUG_OUT) System.out.println(s); }
}

class QueryNetbox extends Thread
{
	public static boolean ERROR_OUT = true;
	public static boolean VERBOSE_OUT = false;
	public static boolean DEBUG_OUT = false;
	public static boolean DB_UPDATE = false;
	public static boolean DB_COMMIT = false;

	// Felles datastrukturer som bare skal leses fra
	/*
	public static HashMap macBoksId;
	public static HashMap boksIdName;
	public static HashMap boksidKat;
	public static HashMap sysnameMap;
	*/

	static ConfigParser navCp;
	public static void setConfigParser(ConfigParser cp) { navCp = cp; }

	static HashMap moduleMap;
	public static void setModuleMap(HashMap h) { moduleMap=h; }
	static HashMap deviceMap;
	public static void setDeviceMap(HashMap h) { deviceMap=h; }
	/*
	static HashMap swportDataMap;
	public static void setSwportDataMap(HashMap h) { swportDataMap=h; }
	*/

	static HashMap boksDiskMap;
	public static void setBoksDiskMap(HashMap h) { boksDiskMap = h; }
	static HashMap boksInterfaceMap;
	public static void setBoksInterfaceMap(HashMap h) { boksInterfaceMap = h; }

	//static HashSet safeCloseBoksid;
	//public static void setSafeCloseBoksid(HashSet h) { safeCloseBoksid=h; }

	// Køen som inneholder alle boksene, delt mellom trådene
	static LinkedList bdFifo;
	public static void setBdFifo(LinkedList l) { bdFifo = l; }
	static Map bdMap;
	public static void setBdMap(Map h) { bdMap = h; }
	static Stack idleThreads;
	public static void setIdleThreads(Stack s) { idleThreads = s; }

	// Minimum delay mellom hver gang vi spør en boks
	public static long minBoksRunInterval = 15 * 60 * 1000; // Default is every 15 mins.
	//public static void setMinBoksRunInterval(long l) { minBoksRunInterval = l; }

	// Hvilke tråder som er ferdig
	static boolean[] threadDone;

	// Rapport når en boks er ferdigbehandlet
	static ArrayList boksReport = new ArrayList();

	// Plugins
	// Caches which device handlers can handle a given Netbox
	static Map deviceNetboxCache = Collections.synchronizedMap(new HashMap());
	static Map dataClassMap, deviceClassMap;
	static Map persistentStorage = Collections.synchronizedMap(new HashMap());
	public static void setDataClassMap(Map m) { dataClassMap = m; }
	public static void setDeviceClassMap(Map m) { deviceClassMap = m; }
	public static void clearDeviceNetboxCache()
	{
		synchronized (deviceNetboxCache) {
			deviceNetboxCache.clear();
		}
	}

	static int curBd, antBd;

	// Objekt-spesifikke data
	int tnum;
	String id;
	NetboxImpl nb;
	//String id;

	SimpleSnmp sSnmp = new SimpleSnmp();

	// Konstruktør
	public QueryNetbox(int tnum, String id, NetboxImpl initialNb)
	{
		this.tnum = tnum;
		this.id = id;
		this.nb = initialNb;
	}

	public static void initThreadDone(final int NUM_THREADS)
	{
		threadDone = new boolean[NUM_THREADS];
		for (int i=0; i < threadDone.length; i++) {
			threadDone[i] = false;
		}
	}


	/*
	private static String[] modulNameShorts = {
		"FastEthernet", "Fa",
		"GigabitEthernet", "Gi"
	};
	private static String processModulName(String modul)
	{
		for (int j=0; j<modulNameShorts.length; j+=2) {
			if (modul.startsWith(modulNameShorts[j])) modul = modulNameShorts[j+1]+modul.substring(modulNameShorts[j].length(), modul.length());
		}
		return modul;
	}
	*/


	public void run()
	{
		long beginTime = System.currentTimeMillis();

		while (true) {
			// Schedule the next run for this boks
			nb.nextRun(System.currentTimeMillis() + minBoksRunInterval);
			synchronized (bdMap) {
				antBd = bdMap.size();
				if (++curBd > antBd) curBd = 0;
			}

			String netboxid = nb.getNetboxid();
			String ip = nb.getIp();
			String cs_ro = nb.getCommunityRo();
			String typegroup = nb.getTypegroup();
			String type = nb.getType();
			String sysName = nb.getSysname();
			String cat = nb.getCat();
			int snmpMajor = nb.getSnmpMajor();

			outla("T"+id+": Now working with("+netboxid+"): " + sysName + ", type="+type+", typegroup="+typegroup+", ip="+ip+" (device "+ curBd +" of "+ antBd+")");
			long boksBeginTime = System.currentTimeMillis();

			try {

				// Get DataContainer objects from each data-plugin.
				DataContainersImpl containers = getDataContainers();

				// Find handlers for this boks
				DeviceHandler[] deviceHandler = findDeviceHandlers(nb);
				if (deviceHandler == null) {
					throw new NoDeviceHandlerException("T"+id+":   No device handlers found for netbox: " + netboxid + " (cat: " + cat + " type: " + type + " typegroup: " + typegroup);
				}
				outld("T"+id+":   Found " + deviceHandler.length + " deviceHandlers for boksid: " + netboxid + " (cat: " + cat + " type: " + type + " typegroup: " + typegroup);

				for (int dhNum=0; dhNum < deviceHandler.length; dhNum++) {

					try {
						deviceHandler[dhNum].handleDevice(nb, sSnmp, navCp, containers);

					} catch (TimeoutException te) {
						outl("T"+id+":   *ERROR*, TimeoutException: " + te.getMessage());
						outla("T"+id+":   *** GIVING UP ON: " + sysName + ", typeid: " + type + " ***");
						continue;
					}

				}

				// Call the data handlers for all data plugins
				containers.callDataHandlers(nb);

					// Process returned swports
					//outld("T"+id+":   DeviceHandler["+dhNum+"] returned MoudleDataList, modules found: : " + moduleDataList.size());


					/*
					// Snmpagent
					if (dd != null) {
						String snmpagent = dd.getSnmpagent();
						if (snmpagent != null && snmpagent.length() > 0 && !snmpagent.equals(bd.getSnmpagent())) {
							// Oppdater
							try {
								if (DB_UPDATE) Database.update("UPDATE boks SET snmpagent='"+Database.addSlashes(snmpagent)+"' WHERE boksid='"+bd.getBoksid()+"'");
								if (DB_COMMIT) Database.commit(); else Database.rollback();
								if (DB_UPDATE && DB_COMMIT) bd.setSnmpagent(snmpagent);
							} catch (SQLException e) {
								outle("T"+id+":   SQLException in QueryNetbox.run(): Cannot update snmpagent for boksid " + bd.getBoksid() + " to " + Database.addSlashes(snmpagent) + ": " + e.getMessage());
							}
						}
					}

					// boksdisk
					if (dd != null && dd.getBoksDiskUpdated()) {
						List l = dd.getBoksDisk();
						HashMap boksDisk;
						synchronized (boksDiskMap) {
							boksDisk = (HashMap)boksDiskMap.get(bd.getBoksid());
							if (boksDisk == null) boksDiskMap.put(bd.getBoksid(), boksDisk = new HashMap());
						}
						HashMap boksDiskClone = (HashMap)boksDisk.clone();

						// Iterate over the list and add/update as needed
						for (Iterator i = l.iterator(); i.hasNext();) {
							String[] vals = (String[])i.next();
							String path = vals[0].trim();
							String blocksize = vals[1];
							if (!boksDisk.containsKey(path)) {
								// Insert new
								try {
									String[] ins = {
										"netboxid", netboxid,
										"path", Database.addSlashes(path),
										"blocksize", blocksize
									};
									if (DB_UPDATE) Database.insert("boksdisk", ins);
									if (DB_COMMIT) Database.commit(); else Database.rollback();
									if (DB_UPDATE && DB_COMMIT) boksDisk.put(path, new String[] { blocksize } );
								} catch (SQLException e) {
									outle("T"+id+":   SQLException in QueryNetbox.run(): Cannot insert new path " + path + ", blocksize: " + blocksize + " for boksid " + bd.getBoksid() + ": " + e.getMessage());
								}
							} else {
								boksDiskClone.remove(path);

								// Check if values (blocksize) have changed
								String[] dbVals = (String[])boksDisk.get(path);
								String dbBlocksize = dbVals[0];
								if (!dbBlocksize.equals(blocksize)) {
									try {
										String[] cnd = {
											"netboxid", netboxid,
											"path", Database.addSlashes(path)
										};
										String[] upd = {
											"blocksize", blocksize
										};
										if (DB_UPDATE) Database.update("boksdisk", upd, cnd);
										if (DB_COMMIT) Database.commit(); else Database.rollback();
										if (DB_UPDATE && DB_COMMIT) boksDisk.put(path, new String[] { blocksize } );
									} catch (SQLException e) {
										outle("T"+id+":   SQLException in QueryNetbox.run(): Cannot update for boksid " + bd.getBoksid() + ", path " + path + " values blocksize: " + blocksize + ": " + e.getMessage());
									}
								}
							}

						}

						// Remove any remaining paths
						StringBuffer sb = new StringBuffer();
						for (Iterator i = boksDiskClone.keySet().iterator(); i.hasNext();) {
							String path = (String)i.next();
							sb.append(",'"+Database.addSlashes(path)+"'");
							if (DB_UPDATE && DB_COMMIT) boksDisk.remove(path);
						}
						if (sb.length() > 0) {
							sb.deleteCharAt(0);
							try {
								if (DB_UPDATE) Database.update("DELETE FROM boksdisk WHERE boksid='"+bd.getBoksid()+"' AND path IN ("+sb+")");
								if (DB_COMMIT) Database.commit(); else Database.rollback();
							} catch (SQLException e) {
								outle("T"+id+":   SQLException in QueryNetbox.run(): Cannot remove paths " + sb + " for boksid " + bd.getBoksid() + ": " + e.getMessage());
							}
						}
					}

					// boksinterface
					if (dd != null && dd.getBoksInterfaceUpdated()) {
						List l = dd.getBoksInterface();
						HashSet boksInterface;
						synchronized (boksInterfaceMap) {
							boksInterface = (HashSet)boksInterfaceMap.get(bd.getBoksid());
							if (boksInterface == null) boksInterfaceMap.put(bd.getBoksid(), boksInterface = new HashSet());
						}
						HashSet boksInterfaceClone = (HashSet)boksInterface.clone();

						// Iterate over the list and add/update as needed
						for (Iterator i = l.iterator(); i.hasNext();) {
							String interf = ((String)i.next()).trim();
							if (!boksInterface.contains(interf)) {
								// Insert new
								try {
									String[] ins = {
										"netboxid", netboxid,
										"interf", Database.addSlashes(interf)
									};
									if (DB_UPDATE) Database.insert("boksinterface", ins);
									if (DB_COMMIT) Database.commit(); else Database.rollback();
									if (DB_UPDATE && DB_COMMIT) boksInterface.add(interf);
								} catch (SQLException e) {
									outle("T"+id+":   SQLException in QueryNetbox.run(): Cannot insert new interf " + interf + " for boksid " + bd.getBoksid() + ": " + e.getMessage());
								}
							} else {
								boksInterfaceClone.remove(interf);
							}
						}

						// Remove any remaining paths
						StringBuffer sb = new StringBuffer();
						for (Iterator i = boksInterfaceClone.iterator(); i.hasNext();) {
							String interf = (String)i.next();
							sb.append(",'"+Database.addSlashes(interf)+"'");
							if (DB_UPDATE && DB_COMMIT) boksInterface.remove(interf);
						}
						if (sb.length() > 0) {
							sb.deleteCharAt(0);
							try {
								if (DB_UPDATE) Database.update("DELETE FROM boksinterface WHERE boksid='"+bd.getBoksid()+"' AND interf IN ("+sb+")");
								if (DB_COMMIT) Database.commit(); else Database.rollback();
							} catch (SQLException e) {
								outle("T"+id+":   SQLException in QueryNetbox.run(): Cannot remove interfs " + sb + " for boksid " + bd.getBoksid() + ": " + e.getMessage());
							}
						}
					}
					********************************/
			} catch (NoDeviceHandlerException exp) {
				outld(exp.getMessage());
			} catch (Exception exp) {
				outle("T"+id+":   QueryNetbox.run(): Fatal error, aborting. Exception: " + exp.getMessage());
				exp.printStackTrace(System.err);
			}


			// OK, done with this boks
			synchronized (bdFifo) {
				// First add it back to the end of the queue (if not removed)
				synchronized (bdMap) {
					if (!nb.removed()) bdFifo.add(nb);
				}

				// Find the next boks still in our list
				nb = (NetboxImpl)bdFifo.getFirst();
				synchronized (bdMap) {
					while (!bdMap.containsKey(nb.getNetboxid())) {
						bdFifo.removeFirst();
						nb = (bdFifo.size() == 0) ? null : (NetboxImpl)bdFifo.getFirst();
					}
					if (nb == null) break;
					//antBd = bdMap.size();
				}

				// Check if the next boks is ripe
				if (nb.nextRun() > System.currentTimeMillis()) {
					// Not yet ripe
					break;
				}

				// OK, we take it, so remove it from the queue
				bdFifo.removeFirst();
				//if (++curBd > antBd) curBd = 0;
			}

			/*
			long boksUsedTime = System.currentTimeMillis() - boksBeginTime;
			synchronized (boksReport) {
				boksReport.add(new BoksReport((int)boksUsedTime, bd));
			}
			*/

			synchronized (idleThreads) {
				idleThreads.push(new Integer(id));
			}
			outld("T"+id+": Thread idle, exiting...");
			getDeviceData.threadIdle();
			
			/*
				long usedTime = System.currentTimeMillis() - beginTime;
				threadDone[id] = true;
				outla("T"+id+": ** Thread done, time used: " + GetDeviceData.formatTime(usedTime) + ", waiting for " + getThreadsNotDone() + " **");
			*/

		}
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
			outle("QueryNetbox.findHandler(): Unable to instantiate handler for " + nb.getNetboxid() + ", msg: " + e.getMessage());
		} catch (IllegalAccessException e) {
			outle("QueryNetbox.findHandler(): IllegalAccessException for " + nb.getNetboxid() + ", msg: " + e.getMessage());
		}

		return dcs;		
	}

	private DeviceHandler[] findDeviceHandlers(Netbox nb) {
		try {
			synchronized (deviceNetboxCache) {
				Class[] c;
				if ( (c=(Class[])deviceNetboxCache.get(nb.getNetboxid() )) != null) {
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
					int v = dh.canHandleDevice(nb);
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
					
					synchronized (deviceNetboxCache) { deviceNetboxCache.put(nb.getNetboxid(), c); }

					// Call ourselves; this avoids duplicating the code for instatiating objects from the classes
					return findDeviceHandlers(nb);
				}
			}
		} catch (InstantiationException e) {
			outle("QueryNetbox.findHandler(): Unable to instantiate handler for " + nb.getNetboxid() + ", msg: " + e.getMessage());
		} catch (IllegalAccessException e) {
			outle("QueryNetbox.findHandler(): IllegalAccessException for " + nb.getNetboxid() + ", msg: " + e.getMessage());
		}

		return null;
	}

	private String getThreadsNotDone()
	{
		StringBuffer sb = new StringBuffer();
		int startRange=0;
		boolean markLast=false;

		for (int i=0; i < threadDone.length+1; i++) {
			if (i != threadDone.length && !threadDone[i]) {
				if (!markLast) {
					startRange=i;
					markLast = true;
				}
			} else if (markLast) {
				String range = (startRange==i-1) ? String.valueOf(i-1) : startRange+"-"+(i-1);
				sb.append(","+range);
				markLast=false;
			}
		}
		if (sb.length() > 0) {
			sb.setCharAt(0, '[');
		} else {
			sb.insert(0, "[");
		}
		sb.append("]");
		return sb.toString();
	}

	private static void outa(String s) { System.out.print(s); }
	private static void outla(String s) { System.out.println(s); }

	private static void oute(Object s) { if (ERROR_OUT) System.out.print(s); }
	private static void outle(Object s) { if (ERROR_OUT) System.out.println(s); }

	private static void out(String s) { if (VERBOSE_OUT) System.out.print(s); }
	private static void outl(String s) { if (VERBOSE_OUT) System.out.println(s); }

	private static void outd(String s) { if (DEBUG_OUT) System.out.print(s); }
	private static void outld(String s) { if (DEBUG_OUT) System.out.println(s); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
	private static void errflush() { System.err.flush(); }

}

class NetboxReport implements Comparable
{
	int usedTime;
	Netbox nb;

	public NetboxReport(int usedTime, Netbox nb)
	{
		this.usedTime = usedTime;
		this.nb = nb;
	}

	public int getUsedTime() { return usedTime; }
	public Netbox getNetbox() { return nb; }

	public int compareTo(Object o)
	{
		return new Integer(((NetboxReport)o).getUsedTime()).compareTo(new Integer(usedTime));
	}
}

class LoadDataTask extends TimerTask
{
	public void run()
	{
		try {
			getDeviceData.loadData();
		} catch (SQLException e) {
			System.err.println("SQLException in LoadData.run(): " + e.getMessage());
		}
	}
}

class NetboxTimer extends TimerTask
{
	public void run()
	{
		getDeviceData.checkBdQ();
	}
}

class PluginMonitorTask extends TimerTask
{
	DynamicURLClassLoader cl = new DynamicURLClassLoader();
	
	File dataDir, deviceDir;
	Map dataClassMap, deviceClassMap;

	Map dataFileMap = new HashMap();
	Map deviceFileMap = new HashMap();

	public PluginMonitorTask(String dataPath, Map dataClassMap, String devicePath, Map deviceClassMap)
	{
		dataDir = new File(dataPath);
		deviceDir = new File(devicePath);
		this.dataClassMap = dataClassMap;
		this.deviceClassMap = deviceClassMap;
	}

	public void run()
	{
		// Update data plugins
		update(dataDir, dataFileMap, dataClassMap, null );

		// Update device plugins
		update(deviceDir, deviceFileMap, deviceClassMap, dataDir.listFiles() );

		/*
		if (update(dataDir, dataFileMap, dataClassMap, dataDir.listFiles() )) {
			devDB.startDBUpdate();

			Class[] ddbClass = new Class[1];
			Object[] o = new Object[] { devDB };
			try {
				ddbClass[0] = Class.forName("no.ntnu.nav.eventengine.DeviceDB");
			} catch (ClassNotFoundException e) {}

			List deviceClassList = new ArrayList();
			for (Iterator i = deviceClassMap.values().iterator(); i.hasNext();) {
				Class c = (Class)i.next();
				deviceClassList.add(new DeviceClassEntry(findDepth(c), c));
			}

			Collections.sort(deviceClassList);

			for (Iterator i = deviceClassList.iterator(); i.hasNext();) {
				Class c = ((DeviceClassEntry)i.next()).deviceClass;
				try {
					Method m = c.getMethod("updateFromDB", ddbClass);
					m.invoke(null, o);
				} catch (NoSuchMethodException e) {

				} catch (IllegalAccessException e) {

				} catch (InvocationTargetException e) {
					outld("PluginMonitorTask:   InvocationTargetException when invoking updateFromDB in class " + c.getName() + ": " + e.getMessage());
					e.printStackTrace(System.err);
				}

			}

			devDB.endDBUpdate();
			classDepthCache.clear();

			// Now call 'init' for all devices
			for (Iterator i = deviceMap.values().iterator(); i.hasNext();) ((Device)i.next()).init(devDB);

			//Device d = (Device)devDB.getDevice(279);
			//errl("Found:\n"+d);

		}

		// Update EventHandlers
		if (update(handlerDir, handlerFileMap, handlerClassMap, deviceDir.listFiles() )) {
			emt.updateCache();
		}
		*/
	}

	private boolean update(File pluginDir, Map fileMap, Map classMap, File[] dependFiles)
	{
		// The cloneMap is used to remove plugins whose .jar file is deleted
		Map cloneMap;
		synchronized (classMap) {
			cloneMap = (Map) ((HashMap)classMap).clone();
		}

		boolean hasChanged = false;
		File[] fileList = pluginDir.listFiles();

		if (dependFiles != null) {
			for (int i=0; i < dependFiles.length; i++) {
				try {
						cl.appendURL(dependFiles[i].toURL());
				} catch (MalformedURLException e) {} // Should never happen
			}
		}

		for (int i=0; i < fileList.length; i++) {
			if (!fileList[i].getName().toLowerCase().endsWith(".jar")) continue;
			cloneMap.remove(fileList[i].getName());

			try {
				Long lastMod;
				// If new or modified JAR
				if ( (lastMod=(Long)fileMap.get(fileList[i].getName())) == null || 
						 !lastMod.equals(new Long(fileList[i].lastModified())) ) {
					fileMap.put(fileList[i].getName(), new Long(fileList[i].lastModified()));

					cl.appendURL(fileList[i].toURL());

					JarFile jf = new JarFile(fileList[i]);
					Manifest mf = jf.getManifest();
					Attributes attr = mf.getMainAttributes();
					String cn = attr.getValue("Plugin-Class");
					outld("PluginMonitorTask: New or modified jar, trying to load " + fileList[i].getName());

					if (cn == null) {
						outld("PluginMonitorTask:   jar is missing Plugin-Class manifest, skipping...");
						continue;
					}

					Class c, dataInterface, deviceInterface;
					try {
						dataInterface = Class.forName("no.ntnu.nav.getDeviceData.dataplugins.DataHandler");
						deviceInterface = Class.forName("no.ntnu.nav.getDeviceData.deviceplugins.DeviceHandler");

						c = cl.loadClass(cn);
					} catch (ClassNotFoundException e) {
						errl("PluginMonitorTask:   Class " + cn + " not found in jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					} catch (NoClassDefFoundError e) {
						errl("PluginMonitorTask:   NoClassDefFoundError when loading class " + cn + " from jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					}

					if (dataInterface.isAssignableFrom(c) || deviceInterface.isAssignableFrom(c)) {
						// Found new Device, add to list
						synchronized (classMap) {
							classMap.put(fileList[i].getName(), c);
						}
						hasChanged = true;
						outld("PluginMonitorTask:   OK! Loaded and added to classMap");
					} else {
						outld("PluginMonitorTask:   Failed! class " + cn + " is not an event engine plugin");
					}
				}
			} catch (IOException e) {
				errl("PluginMonitorTask:   IOException when loading jar " + fileList[i].getName() + ", msg: " + e.getMessage());
			}
		}

		Iterator i = cloneMap.keySet().iterator();
		while (i.hasNext()) {
			String fn = (String)i.next();
			outld("PluginMonitorTask: Removing jar " + fn + " from classMap");
			synchronized (classMap) {
				classMap.remove(fn);
			}
			fileMap.remove(fn);
			hasChanged = true;
		}
		return hasChanged;
	}

	/*
	public void run()
	{
		if (!pluginDir.isDirectory()) {
			outld("pluginMonitorTask: Error, plugins/ directory not found, exiting...");
			System.exit(0);
		}

		Map cloneMap;
		synchronized (deviceHandlerMap) {
			cloneMap = (Map) ((HashMap)deviceHandlerMap).clone();
		}

		boolean clearCache = false;
		File[] fileList = pluginDir.listFiles();
		for (int i=0; i < fileList.length; i++) {
			if (!fileList[i].getName().toLowerCase().endsWith(".jar")) continue;
			cloneMap.remove(fileList[i].getName());

			//if (fileList[i].getName().equals("HandleCisco.jar")) continue;
			//outld("pluginMonitorTask: Found jar: " + fileList[i].getName());

			try {
				Long lastMod;
				if ( (lastMod=(Long)fileMap.get(fileList[i].getName())) == null || !lastMod.equals(new Long(fileList[i].lastModified())) ) {
					fileMap.put(fileList[i].getName(), new Long(fileList[i].lastModified()));

					// Ny eller modifisert device handler
					URL[] plugin_path = new URL[1];
					plugin_path[0] = fileList[i].toURL();
					URLClassLoader cl = new URLClassLoader(plugin_path);

					JarFile jf = new JarFile(fileList[i]);
					Manifest mf = jf.getManifest();
					Attributes attr = mf.getMainAttributes();
					String cn = attr.getValue("Plugin-Class");
					outld("pluginMonitorTask: New or modified jar, trying to load jar " + fileList[i].getName());

					if (cn == null) {
						outld("pluginMonitorTask:   jar is missing Plugin-Class manifest, skipping...");
						continue;
					}

					Class c, deviceHandlerInterface;
					try {
						deviceHandlerInterface = Class.forName("no.ntnu.nav.getDeviceData.plugins.DeviceHandler");

						c = cl.loadClass(cn);
					} catch (ClassNotFoundException e) {
						errl("PluginMonitorTask:   Class " + cn + " not found in jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					} catch (NoClassDefFoundError e) {
						errl("PluginMonitorTask:   NoClassDefFoundError when loading class " + cn + " from jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					}

					if (deviceHandlerInterface.isAssignableFrom(c)) {
						// OK, add to list
						synchronized (deviceHandlerMap) {
							deviceHandlerMap.put(fileList[i].getName(), c);
							clearCache = true;
							outld("PluginMonitorTask:   OK! Loaded and added to deviceHandlerMap");
						}
					} else {
						outld("PluginMonitorTask:   Failed! class " + cn + " does not implement DeviceHandler");
					}
				}
			} catch (IOException e) {
				errl("PluginMonitorTask:   IOException when loading jar " + fileList[i].getName() + ", msg: " + e.getMessage());
			}
		}

		synchronized (deviceHandlerMap) {
			Iterator i = cloneMap.keySet().iterator();
			while (i.hasNext()) {
				String fn = (String)i.next();
				outld("PluginMonitorTask: Removing jar " + fn + " from deviceHandlerMap");
				deviceHandlerMap.remove(fn);
				fileMap.remove(fn);
				clearCache = true;
			}
		}
		if (clearCache) QueryNetbox.clearDeviceHandlerBdCache();
	}
	*/

	class DynamicURLClassLoader extends URLClassLoader {
		Set urlSet = new HashSet();

		DynamicURLClassLoader() {
			super(new URL[0]);
		}
		public void appendURL(URL u) {
			if (urlSet.add(u)) {
				addURL(u);
			}
		}
	}

	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }

}












