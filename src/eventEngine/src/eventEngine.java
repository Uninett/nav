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
import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;

import java.sql.*;

import no.ntnu.nav.ConfigParser.*;
import no.ntnu.nav.Database.*;
import no.ntnu.nav.eventengine.*;

class eventEngine
{
	//public static final String navRoot = "/usr/local/nav/";
	public static final String navRoot = "c:/jprog/itea/".replace('/', File.separatorChar);
	public static final String dbConfigFile = "local/etc/conf/db.conf".replace('/', File.separatorChar);
	public static final String configFile = "local/etc/conf/eventEngine.conf".replace('/', File.separatorChar);
	public static final String alertmsgFile = navRoot+"local/etc/conf/alertmsg.conf".replace('/', File.separatorChar);
	public static final String scriptName = "eventEngine";

	public static final boolean ERROR_OUT = true;
	public static final boolean VERBOSE_OUT = true;
	public static final boolean DEBUG_OUT = true;

	public static final boolean DB_UPDATE = true;
	public static final boolean DB_COMMIT = true;

	// END USER CONFIG //

	// A timer
	static Thread[] threads;
	static Timer timer;
	static Stack idleThreads;

	//static HashSet safeCloseBoksid = new HashSet();
	static String qBoks;

	public static void main(String[] args) throws Exception
	{
		String cf = null;
		// Check arguments
		if (args.length > 0) {
			// Assume this argument is the config file
			File f = new File(args[0]);
			if (f.exists() && !f.isDirectory()) cf = f.getAbsolutePath();
		}

		ConfigParser dbCp;
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

		// Deamon timer
		timer = new Timer(true);

		// Set up the config file monitor
		if (cf == null) cf = navRoot + configFile;
		ConfigFileMonitorTask cfmt = new ConfigFileMonitorTask(cf);
		if (cfmt.cfNotFound()) {
			errl("Error, could not read config file: " + cf);
			return;
		}
		cfmt.run(); // Load config first time
		timer.schedule(cfmt, 5 * 1000, 5 * 1000); // 5 second delay

		HashMap handlerClassMap = new HashMap();
		HashMap deviceMap = new HashMap();

		DeviceDB devDB;
		try {
			devDB = new DeviceDB(deviceMap, timer, alertmsgFile);
		} catch (ParseException e) {
			errl("While reading " + alertmsgFile + ":");
			errl("  " + e.getMessage());
			return;
		}

		// The eventq monitor
		EventqMonitorTask emt = new EventqMonitorTask(handlerClassMap, devDB);

		// Set up the plugin monitor
		PluginMonitorTask pmt = new PluginMonitorTask("device-plugins", new HashMap(), "handler-plugins", handlerClassMap, devDB, deviceMap, emt );
		pmt.run(); // Load all plugins

		timer.schedule(pmt, 5 * 1000, 5 * 1000); // Check for new plugin every 5 seconds
		timer.schedule(emt, 1 * 1000, 5 * 1000); // Check for new events every 5 seconds


		// Now just wait :-)
		InputStreamReader in = new InputStreamReader(System.in);

		boolean msg = false;
		boolean INTERACTIVE = false;
		while (true) {
			if (!msg) {
				outl("Press Q+Enter to exit...");
				msg = true;
			} else {
				//out(".");
				if (INTERACTIVE) outWait();
			}
			Thread.currentThread().sleep(500);

			// Sjekk om vi skal avslutte
			if (in.ready()) {
				int c = in.read();
				if (c == 'Q' || c == 'q') break;
			}
		}
		outl("All done.");





	}

	private static boolean PRINT_BOX;
	private static int WAIT_POS;
	public static void outWait()
	{
		// - \ | /

		if (!PRINT_BOX) {
			PRINT_BOX = true;
		} else {
			System.out.print((char)8);
			System.out.print((char)8);
			System.out.print((char)8);
		}
		out("[");
		switch (WAIT_POS) {
			case 0: out("-"); break;
			case 1: out("\\"); break;
			case 2: out("|"); break;
			case 3: out("/"); break;
		}
		out("]");
		WAIT_POS = (WAIT_POS+1)%4;
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

class ConfigFileMonitorTask extends TimerTask
{
	File cf;
	ConfigParser cp;
	boolean cfNotFound;

	public ConfigFileMonitorTask(String cfPath)
	{
		cf = new File(cfPath);
		if (!cf.isFile()) cfNotFound = true;
	}

	public void run()
	{
		if (cfNotFound) return;

		try {
			cp = new ConfigParser(cf.getAbsolutePath());
		} catch (IOException e) {
			errl("Error, could not read config file: " + cf);
			return;
		}


	}

	public boolean cfNotFound() { return cfNotFound; }

	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }

}

class PluginMonitorTask extends TimerTask
{
	File deviceDir, handlerDir;
	Map deviceClassMap, handlerClassMap;

	Map deviceFileMap = new HashMap();
	Map handlerFileMap = new HashMap();

	DeviceDB devDB;
	Map deviceMap;
	EventqMonitorTask emt;

	public PluginMonitorTask(String devicePath, Map deviceClassMap, String handlerPath, Map handlerClassMap, DeviceDB devDB, Map deviceMap, EventqMonitorTask emt)
	{
		deviceDir = new File(devicePath);
		this.deviceClassMap = deviceClassMap;
		handlerDir = new File(handlerPath);
		this.handlerClassMap = handlerClassMap;
		this.devDB = devDB;
		this.deviceMap = deviceMap;
		this.emt = emt;

		if (!deviceDir.isDirectory() || !handlerDir.isDirectory()) {
			outld("pluginMonitorTask: Error, plugins directory not found, exiting...");
			System.exit(0);
		}
	}

	public void run()
	{
		// Update Devices
		if (update(deviceDir, deviceFileMap, deviceClassMap, true)) {
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
		if (update(handlerDir, handlerFileMap, handlerClassMap, false)) {
			emt.updateCache();
		}
	}

	class DeviceClassEntry implements Comparable
	{
		int depth;
		Class deviceClass;
		public DeviceClassEntry(int depth, Class c)
		{
			this.depth = depth;
			this.deviceClass = c;
		}
		public int compareTo(Object o)
		{
			DeviceClassEntry dc = (DeviceClassEntry)o;
			return new Integer(depth).compareTo(new Integer(dc.depth)) * -1; // Sort in reverse order, biggest first
		}
	}

	HashMap classDepthCache = new HashMap();
	private int findDepth(Class c)
	{
		Integer depth;
		if ( (depth=(Integer)classDepthCache.get(c.getName())) != null) return depth.intValue();

		Class parent = c.getSuperclass();
		if (parent == null) return 0;

		classDepthCache.put(c.getName(), depth = new Integer(findDepth(parent)+1));
		outld("Class " + c.getName() + " has depth " + depth.intValue());
		return depth.intValue();
	}

	private boolean update(File pluginDir, Map fileMap, Map pluginMap, boolean jarDepend)
	{
		Map cloneMap = (Map) ((HashMap)pluginMap).clone();

		boolean hasChanged = false;
		File[] fileList = pluginDir.listFiles();

		URL[] plugin_path;
		if (jarDepend) {
			plugin_path = new URL[fileList.length];
			for (int i=0; i < fileList.length; i++) {
				try {
					plugin_path[i] = fileList[i].toURL();
				} catch (MalformedURLException e) {} // Should never happen
			}
		} else {
			plugin_path = new URL[1];
		}

		for (int i=0; i < fileList.length; i++) {
			if (!fileList[i].getName().toLowerCase().endsWith(".jar")) continue;
			cloneMap.remove(fileList[i].getName());

			//if (fileList[i].getName().equals("HandleCisco.jar")) continue;
			//outld("pluginMonitorTask: Found jar: " + fileList[i].getName());

			try {
				Long lastMod;
				if ( (lastMod=(Long)fileMap.get(fileList[i].getName())) == null || !lastMod.equals(new Long(fileList[i].lastModified())) ) {
					fileMap.put(fileList[i].getName(), new Long(fileList[i].lastModified()));

					// Ny eller modifisert jar
					if (!jarDepend) plugin_path[0] = fileList[i].toURL();
					URLClassLoader cl = new URLClassLoader(plugin_path);

					JarFile jf = new JarFile(fileList[i]);
					Manifest mf = jf.getManifest();
					Attributes attr = mf.getMainAttributes();
					String cn = attr.getValue("Plugin-Class");
					outld("PluginMonitorTask: New or modified jar, trying to load " + fileList[i].getName());

					if (cn == null) {
						outld("PluginMonitorTask:   jar is missing Plugin-Class manifest, skipping...");
						continue;
					}

					Class c, deviceClass, handlerInterface;
					try {
						deviceClass = Class.forName("no.ntnu.nav.eventengine.Device");
						handlerInterface = Class.forName("no.ntnu.nav.eventengine.EventHandler");

						c = cl.loadClass(cn);
					} catch (ClassNotFoundException e) {
						errl("PluginMonitorTask:   Class " + cn + " not found in jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					} catch (NoClassDefFoundError e) {
						errl("PluginMonitorTask:   NoClassDefFoundError when loading class " + cn + " from jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					}

					if (deviceClass.isAssignableFrom(c) || handlerInterface.isAssignableFrom(c)) {
						// Found new Device, add to list
						pluginMap.put(fileList[i].getName(), c);
						hasChanged = true;
						outld("PluginMonitorTask:   OK! Loaded and added to pluginMap");
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
			outld("PluginMonitorTask: Removing jar " + fn + " from pluginMap");
			pluginMap.remove(fn);
			fileMap.remove(fn);
			hasChanged = true;
		}
		return hasChanged;
	}


	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }

}


class EventqMonitorTask extends TimerTask
{
	Map handlerClassMap;
	DeviceDB devDB;

	Map handlerCache = new HashMap();
	int lastEventqid = 55364;

	public EventqMonitorTask(Map handlerClassMap, DeviceDB devDB)
	{
		this.handlerClassMap = handlerClassMap;
		this.devDB = devDB;
	}

	public void updateCache()
	{
		//Map cloneMap = (Map) ((HashMap)handlerClassMap).clone();
		handlerCache.clear();
		for (Iterator i=handlerClassMap.values().iterator(); i.hasNext();) {
			Class c = (Class)i.next();
			EventHandler eh;
			try {
				eh = (EventHandler)c.newInstance();
			} catch (InstantiationException e) {
				errl("EventqMonitorTask: Error, Main EventHandler plugin class must have a public default (no args) constructor:" + e.getMessage());
				continue;
			} catch (IllegalAccessException e) {
				errl("EventqMonitorTask: Error, Main EventHandler plugin class must have a public default (no args) constructor:" + e.getMessage());
				continue;
			}
			String[] s = eh.handleEventTypes();
			for (int j=0; j < s.length; j++) {
				handlerCache.put(s[j], eh);
			}
		}

	}

	public void run()
	{
		try {
			//outld("Last lastEventqid is: " + lastEventqid);
			ResultSet rs = Database.query("SELECT eventqid,source,deviceid,netboxid,subid,time,eventtypeid,state,value,severity,var,val FROM eventq LEFT JOIN eventqvar USING (eventqid) WHERE eventqid > "+lastEventqid + " AND target='eventEngine' AND source='test' ORDER BY eventqid");
			//ResultSet rs = Database.query("SELECT eventqid,source,deviceid,boksid,subid,time,eventtypeid,state,value,severity,var,val FROM eventq LEFT JOIN eventqvar USING (eventqid) WHERE eventqid > "+lastEventqid + " AND target='eventEngine' and source='pping' ORDER BY eventqid");
			if (rs.getFetchSize() > 0) outld("Fetched " + rs.getFetchSize() + " events from eventq");

			while (rs.next()) {

				Event e = DeviceDB.eventFactory(rs);
				outld("  Got event: " + e);

				String eventtypeid = e.getEventtypeid();
				if (handlerCache.containsKey(eventtypeid)) {
					EventHandler eh = (EventHandler)handlerCache.get(eventtypeid);
					outld("  Found handler: " + eh.getClass().getName());
					try {
						eh.handle(devDB, e);

					} catch (Exception exp) {
						errl("EventqMonitorTask: Got Exception from handler: " + eh.getClass().getName() + " Msg: " + exp.getMessage());
						exp.printStackTrace(System.err);
					}
				} else {
					outld("  No handler found for eventtype: " + eventtypeid);
				}

			}

			if (rs.last()) if (rs.getInt("eventqid") > lastEventqid) lastEventqid = rs.getInt("eventqid");

		} catch (SQLException e) {
			// Now we are in trouble
			errl("EventqMonitorTask:  SQLException when fetching from eventq: " + e.getMessage());
			e.printStackTrace(System.err);
		}
	}

/*
BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'boxState','t',100);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventq_eventqid_seq.last_value),'pl','100');
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'boxState','f',100);
COMMIT;

- tekno-sw is going down...

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',534,533,'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,netboxid,eventtypeid,state,severity) VALUES ('pping','eventEngine',534,533,'boxState','e',100);
COMMIT;

- mask-stud-368-h2 is going down...

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1253,1253,'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1253,1253,'boxState','e',100);
COMMIT;

- Prøv noe enkelt, voll-sby-980-h (238) står i skygge for voll-sw (237)

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',238,238,'boxState','s',100);
COMMIT;
BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',237,237,'boxState','s',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',238,238,'boxState','e',100);
COMMIT;
BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',237,237,'boxState','e',100);
COMMIT;



- sb-351-sw


- Hva gjøres i tilfellet der man har f.eks to like etterfølgende info-events, skal event engine ignorere den siste?
- Hva gjøres for tilstandsfulle events som aldri oppheves (f.eks en linkDown event der kabelen kobles over på annen port)?
- Skal transienter rapporteres, dvs. boxDown og boxUp i rask rekkefølge?
- Hvordan skal coldStart og warmStart behandles?
- linkState events går ikke til alertq/alerthist
- Dersom en boks går ned, skal moduleDown rapporteres til alertq, evt. med skygge?

---
Algoritmen for down|shadow sjekker ikke om en ruter er nåbar hvis alt er oppe, dvs.
har ikke topologiavlederen funnet all info så vil boksen alltid være i skygge uansett.
---

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'info','t',100);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventq_eventqid_seq.last_value),'pl','100');
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'info','f',100);
COMMIT;

BEGIN;
INSERT INTO eventq (source,target,deviceid,boksid,eventtypeid,state,severity) VALUES ('pping','eventEngine',1,1,'info','x',100);
INSERT INTO eventqvar (eventqid,var,val) VALUES ((SELECT eventq_eventqid_seq.last_value),'pl','100');
COMMIT;








*/

	private static void outd(Object o) { System.out.print(o); }
	private static void outld(Object o) { System.out.println(o); }

	private static void err(Object o) { System.err.print(o); }
	private static void errl(Object o) { System.err.println(o); }
}



/*
DeviceDB:
	Device findBySysname(String s)
	Device findByDeviceid(int deviceid)

Device:
	down()
	up()
	isUp()

Box extends Device

Nettel extends Box
	linkDown(String mp)
	linkUp(String mp)
	warmStart()
	coldStart()

Gw extends Nettel
	cpuThresholdExceeded()
	memThresholdExceeded()

Sw extends Nettel
	backplaneThresholdExceeded()

Server extends Device
	serviceDown(String serviceid)
	serviceUp(String serviceid)

WWWServer extends Server
*/