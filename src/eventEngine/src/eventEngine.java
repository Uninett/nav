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
import no.ntnu.nav.logger.*;
import no.ntnu.nav.eventengine.*;

class eventEngine
{
	public static final String realNavRoot = "/usr/local/nav/";
	//public static final String navRoot = "c:/jprog/itea/".replace('/', File.separatorChar);
	//public static final String navRoot = "/home/kristian/devel/".replace('/', File.separatorChar);
	public static final String navRoot = realNavRoot.replace('/', File.separatorChar);
	public static final String dbConfigFile = "local/etc/conf/db.conf".replace('/', File.separatorChar);
	public static final String configFile = "local/etc/conf/eventEngine.conf".replace('/', File.separatorChar);
	public static final String alertmsgFile = realNavRoot+"local/etc/conf/alertmsg.conf".replace('/', File.separatorChar);
	public static final String scriptName = "eventEngine";
	public static final String logFile = "local/log/eventEngine.log";

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
			System.err.println("Error, could not read config file: " + navRoot + dbConfigFile);
			return;
		}
		if (!Database.openConnection(dbCp.get("dbhost"), dbCp.get("dbport"), dbCp.get("db_nav"), dbCp.get("script_"+scriptName), dbCp.get("userpw_"+dbCp.get("script_"+scriptName)))) {
			System.err.println("Error, could not connect to database!");
			return;
		}

		// Init logger
		Log.init(navRoot + logFile, "eventEngine");

		// Deamon timer
		timer = new Timer(false);

		// Set up the config file monitor
		if (cf == null) cf = navRoot + configFile;
		ConfigFileMonitorTask cfmt = new ConfigFileMonitorTask(cf);
		if (cfmt.cfNotFound()) {
			System.err.println("Error, could not read config file: " + cf);
			return;
		}
		cfmt.run(); // Load config first time
		timer.schedule(cfmt, 5 * 1000, 5 * 1000); // 5 second delay

		HashMap handlerClassMap = new HashMap();
		HashMap deviceMap = new HashMap();

		DeviceDBImpl devDB;
		try {
			devDB = new DeviceDBImpl(deviceMap, timer, alertmsgFile);
		} catch (ParseException e) {
			System.err.println("While reading " + alertmsgFile + ":");
			System.err.println("  " + e.getMessage());
			return;
		}

		// The eventq monitor
		EventqMonitorTask emt = new EventqMonitorTask(handlerClassMap, devDB, cfmt);

		// Set up the plugin monitor
		PluginMonitorTask pmt = new PluginMonitorTask("device-plugins", new HashMap(), "handler-plugins", handlerClassMap, devDB, deviceMap, emt );
		pmt.run(); // Load all plugins

		timer.schedule(pmt, 5 * 1000, 5 * 1000); // Check for new plugin every 5 seconds
		timer.schedule(emt, 1 * 1000, 5 * 1000); // Check for new events every 5 seconds

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

}

class ConfigFileMonitorTask extends TimerTask
{
	private File cf;
	private ConfigParser cp;
	private boolean cfNotFound;
	private long lastMod;

	public ConfigFileMonitorTask(String cfPath)
	{
		cf = new File(cfPath);
		if (!cf.isFile()) cfNotFound = true;
	}

	public void run()
	{
		if (cfNotFound) return;
		if (lastMod == cf.lastModified()) return;
		lastMod = cf.lastModified();

		try {
			cp = new ConfigParser(cf.getAbsolutePath());
		} catch (IOException e) {
			Log.w("CONFIG_FILE_MONITOR_TASK", "RUN", "Could not read config file: " + cf);
			return;
		}
	}

	public ConfigParser getConfigParser() {
		return cp;
	}

	public boolean cfNotFound() { return cfNotFound; }

}

class PluginMonitorTask extends TimerTask
{
  DynamicURLClassLoader cl = new DynamicURLClassLoader();

	File deviceDir, handlerDir;
	Map deviceClassMap, handlerClassMap;

	Map deviceFileMap = new HashMap();
	Map handlerFileMap = new HashMap();

	DeviceDBImpl devDB;
	Map deviceMap;
	EventqMonitorTask emt;

	public PluginMonitorTask(String devicePath, Map deviceClassMap, String handlerPath, Map handlerClassMap, DeviceDBImpl devDB, Map deviceMap, EventqMonitorTask emt)
	{
		deviceDir = new File(devicePath);
		this.deviceClassMap = deviceClassMap;
		handlerDir = new File(handlerPath);
		this.handlerClassMap = handlerClassMap;
		this.devDB = devDB;
		this.deviceMap = deviceMap;
		this.emt = emt;

		if (!deviceDir.isDirectory() || !handlerDir.isDirectory()) {
			Log.w("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "Plugins directory not found, exiting...");
			System.exit(0);
		}
	}

	public void run()
	{
		// Update Devices
		if (update(deviceDir, deviceFileMap, deviceClassMap, deviceDir.listFiles() )) {
			devDB.startDBUpdate();
			Class[] ddbClass = new Class[1];
			Object[] o = new Object[] { devDB };
			try {
				ddbClass[0] = Class.forName("no.ntnu.nav.eventengine.DeviceDB");
			} catch (ClassNotFoundException e) {
				System.err.println("ClassNotFoundException when getting DeviceDB reference: " + e.getMessage());
				e.printStackTrace(System.err);
			}

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
					Log.w("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "NoSuchMethodException when invoking updateFromDB in class " + c.getName() + ": " + e.getMessage());
					e.printStackTrace(System.err);
				} catch (IllegalAccessException e) {
					Log.w("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "IllegalAccessException when invoking updateFromDB in class " + c.getName() + ": " + e.getMessage());
					e.printStackTrace(System.err);
				} catch (InvocationTargetException e) {
					Log.w("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "InvocationTargetException when invoking updateFromDB in class " + c.getName() + ": " + e.getMessage());
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
		Log.d("PLUGIN_MONITOR_TASK", "CONSTRUCTOR", "Class " + c.getName() + " has depth " + depth.intValue());

		return depth.intValue();
	}

	private boolean update(File pluginDir, Map fileMap, Map pluginMap, File[] dependFiles)
	{
		// The cloneMap is used to remove plugins whose .jar file is deleted
		Map cloneMap = (Map) ((HashMap)pluginMap).clone();

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
					Log.d("PLUGIN_MONITOR_TASK", "UPDATE", "New or modified jar, trying to load " + fileList[i].getName());

					if (cn == null) {
						Log.d("PLUGIN_MONITOR_TASK", "UPDATE", "JAR is missing Plugin-Class manifest, skipping...");
						continue;
					}

					Class c, deviceClass, handlerInterface;
					try {
						deviceClass = Class.forName("no.ntnu.nav.eventengine.Device");
						handlerInterface = Class.forName("no.ntnu.nav.eventengine.EventHandler");

						c = cl.loadClass(cn);
					} catch (ClassNotFoundException e) {
						Log.w("PLUGIN_MONITOR_TASK", "UPDATE", "Class " + cn + " not found in jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					} catch (NoClassDefFoundError e) {
						Log.w("PLUGIN_MONITOR_TASK", "UPDATE", "NoClassDefFoundError when loading class " + cn + " from jar " + fileList[i].getName() + ", msg: " + e.getMessage());
						continue;
					}

					if (deviceClass.isAssignableFrom(c) || handlerInterface.isAssignableFrom(c)) {
						// Found new Device, add to list
						pluginMap.put(fileList[i].getName(), c);
						hasChanged = true;
						Log.d("PLUGIN_MONITOR_TASK", "UPDATE", "OK! JAR Loaded and added to pluginMap");
					} else {
						Log.w("PLUGIN_MONITOR_TASK", "UPDATE", "Failed! Class " + cn + " is not an event engine plugin");
					}
				}
			} catch (IOException e) {
				Log.e("PLUGIN_MONITOR_TASK", "UPDATE", "IOException when loading jar " + fileList[i].getName() + ", msg: " + e.getMessage());
			}
		}

		Iterator i = cloneMap.keySet().iterator();
		while (i.hasNext()) {
			String fn = (String)i.next();
			Log.d("PLUGIN_MONITOR_TASK", "UPDATE", "Removing jar " + fn + " from pluginMap");
			pluginMap.remove(fn);
			fileMap.remove(fn);
			hasChanged = true;
		}
		return hasChanged;
	}

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

}


class EventqMonitorTask extends TimerTask
{
	Map handlerClassMap;
	DeviceDBImpl devDB;
	ConfigFileMonitorTask cfmt;

	Map handlerCache = new HashMap();
	int lastEventqid = 0;

	public EventqMonitorTask(Map handlerClassMap, DeviceDBImpl devDB, ConfigFileMonitorTask cfmt)
	{
		this.handlerClassMap = handlerClassMap;
		this.devDB = devDB;
		this.cfmt = cfmt;
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
				Log.w("EVENTQ_MONITOR_TASK", "UPDATE_CACHE", "Main EventHandler plugin class must have a public default (no args) constructor:" + e.getMessage());
				continue;
			} catch (IllegalAccessException e) {
				Log.w("EVENTQ_MONITOR_TASK", "UPDATE_CACHE", "Main EventHandler plugin class must have a public default (no args) constructor:" + e.getMessage());
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
			ResultSet rs = Database.query("SELECT eventqid,source,deviceid,netboxid,subid,time,eventtypeid,state,value,severity,var,val FROM eventq LEFT JOIN eventqvar USING (eventqid) WHERE eventqid > "+lastEventqid + " AND target='eventEngine' ORDER BY eventqid");
			if (rs.getFetchSize() > 0) {
				Log.d("EVENTQ_MONITOR_TASK", "RUN", "Fetched " + rs.getFetchSize() + " rows from eventq");
			} else {
				return;
			}

			int eventCnt=0;
			while (rs.next()) {
				Event e = DeviceDBImpl.eventFactory(rs);
				eventCnt++;
				Log.d("EVENTQ_MONITOR_TASK", "RUN", "Got event: " + e);

				String eventtypeid = e.getEventtypeid();
				if (handlerCache.containsKey(eventtypeid)) {
					EventHandler eh = (EventHandler)handlerCache.get(eventtypeid);
					Log.d("EVENTQ_MONITOR_TASK", "RUN", "Found handler: " + eh.getClass().getName());
					try {
						eh.handle(devDB, e, cfmt.getConfigParser() );

					} catch (Exception exp) {
						Log.e("EVENTQ_MONITOR_TASK", "RUN", "Got Exception from handler: " + eh.getClass().getName() + " Msg: " + exp.getMessage());
						exp.printStackTrace(System.err);

						// Rollback any database changes
						Database.rollback();
					}
				} else {
					Log.w("EVENTQ_MONITOR_TASK", "RUN", "No handler found for eventtype: " + eventtypeid);
				}

			}

			Log.d("EVENTQ_MONITOR_TASK", "RUN", "Processed " + eventCnt + " events in this session");
			if (rs.last()) if (rs.getInt("eventqid") > lastEventqid) lastEventqid = rs.getInt("eventqid");

		} catch (SQLException e) {
			// Now we are in trouble
			Log.e("EVENTQ_MONITOR_TASK", "RUN", "SQLException when fetching from eventq: " + e.getMessage());
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
